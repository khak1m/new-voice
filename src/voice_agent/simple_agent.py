"""
Простой Voice Agent для тестирования.

Запуск:
    python -m src.voice_agent.simple_agent dev
"""

import os
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero

load_dotenv()


async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    # Подключаемся к комнате
    await ctx.connect()
    
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    
    # Создаём агента
    agent = Agent(
        instructions="""Ты голосовой ассистент компании AI Prosto.
Отвечай коротко и дружелюбно, 1-2 предложения.
Говори на русском языке.""",
    )
    
    # Создаём сессию с русским языком
    session = AgentSession(
        # Deepgram с русским языком
        stt=deepgram.STT(
            model="nova-2",
            language="ru",  # Русский язык для распознавания
        ),
        # Cartesia с мультиязычным голосом (поддерживает русский)
        tts=cartesia.TTS(
            model="sonic-2",
            voice="794f9389-aac1-45b6-b726-9d9369183238",  # Мультиязычный голос
            language="ru",  # Русский язык для синтеза
        ),
        vad=silero.VAD.load(),
    )
    
    # Запускаем сессию
    await session.start(agent, room=ctx.room)
    
    # Приветствие на русском
    await session.say("Здравствуйте! Чем могу помочь?")
    
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
