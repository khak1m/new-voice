"""
Простой Voice Agent для тестирования.

Запуск:
    python -m src.voice_agent.simple_agent dev
"""

import os
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

load_dotenv()


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
    
    # Выбор LLM: Groq (быстро) или Ollama (локально)
    use_groq = os.getenv("USE_GROQ", "true").lower() == "true"
    
    if use_groq and os.getenv("GROQ_API_KEY"):
        # Groq — очень быстрый, ~300ms latency
        llm = openai.LLM(
            model="llama-3.1-8b-instant",  # Быстрая модель
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
        print("[Agent] Используем Groq LLM (fast)")
    else:
        # Ollama — локально, медленнее
        llm = openai.LLM(
            model="qwen2:1.5b",
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        print("[Agent] Используем Ollama LLM (local)")
    
    # Создаём сессию
    session = AgentSession(
        llm=llm,
        stt=deepgram.STT(
            model="nova-2",
            language="ru",
        ),
        tts=cartesia.TTS(
            model="sonic-2",
            voice="064b17af-d36b-4bfb-b003-be07dba1b649",
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
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="voice-agent"  # Имя агента для LiveKit Dispatch Rule
    ))
