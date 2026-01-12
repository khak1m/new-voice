"""
Простой Voice Agent для тестирования.

Запуск:
    python -m src.voice_agent.simple_agent dev
"""

import os
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.llm import LLM
from livekit.plugins import deepgram, cartesia, silero
from openai import AsyncOpenAI

load_dotenv()


class OllamaLLM(LLM):
    """Ollama LLM через OpenAI-совместимый API."""
    
    def __init__(self, model: str = "qwen2:1.5b"):
        super().__init__()
        self._model = model
        self._client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama не требует ключ
        )
    
    async def chat(self, messages: list, **kwargs):
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            **kwargs
        )
        return response


async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    # Подключаемся к комнате
    await ctx.connect()
    
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    
    # Создаём агента с инструкциями
    agent = Agent(
        instructions="""Ты голосовой ассистент компании AI Prosto.
Отвечай коротко и дружелюбно, 1-2 предложения.
Говори на русском языке.""",
    )
    
    # Создаём сессию с LLM, STT, TTS
    session = AgentSession(
        # Ollama LLM для генерации ответов
        llm=OllamaLLM(model="qwen2:1.5b"),
        # Deepgram с русским языком
        stt=deepgram.STT(
            model="nova-2",
            language="ru",
        ),
        # Cartesia с русским языком
        tts=cartesia.TTS(
            model="sonic-2",
            voice="794f9389-aac1-45b6-b726-9d9369183238",
            language="ru",
        ),
        vad=silero.VAD.load(),
    )
    
    # Запускаем сессию
    await session.start(agent, room=ctx.room)
    
    # Приветствие
    await session.say("Здравствуйте! Чем могу помочь?")
    
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
