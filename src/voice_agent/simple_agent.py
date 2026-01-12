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
    
    # Создаём сессию
    session = AgentSession(
        stt=deepgram.STT(model="nova-2"),
        tts=cartesia.TTS(model="sonic-2", voice="694f9389-aac1-45b6-b726-9d9369183238"),
        vad=silero.VAD.load(),
    )
    
    # Запускаем сессию
    await session.start(ctx.room, agent)
    
    # Приветствие
    await session.say("Здравствуйте! Чем могу помочь?")
    
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
