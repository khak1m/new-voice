"""
Простой Voice Agent для тестирования.

Запуск:
    python -m src.voice_agent.simple_agent dev
"""

import os
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, RoomInputOptions, RoomOutputOptions, RunContext, function_tool, rtc_session
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import deepgram, cartesia, silero

load_dotenv()


class SimpleAgent(Agent):
    """Простой голосовой агент."""
    
    def __init__(self):
        super().__init__(
            instructions="""Ты голосовой ассистент компании AI Prosto.
Отвечай коротко и дружелюбно, 1-2 предложения.
Говори на русском языке.""",
        )


@rtc_session()
async def entrypoint(session: AgentSession):
    """Точка входа агента."""
    
    # Создаём компоненты
    stt = deepgram.STT(model="nova-2")
    tts = cartesia.TTS(model="sonic-2", voice="694f9389-aac1-45b6-b726-9d9369183238")
    vad = silero.VAD.load()
    
    # Запускаем сессию с агентом
    await session.start(
        agent=SimpleAgent(),
        stt=stt,
        tts=tts,
        vad=vad,
    )
    
    # Приветствие
    await session.say("Здравствуйте! Чем могу помочь?")


if __name__ == "__main__":
    from livekit.agents import cli, WorkerOptions
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
