"""
VoiceAgent — голосовой AI-агент на базе LiveKit Agents.

Обрабатывает голосовые звонки:
1. Получает аудио от клиента
2. Распознаёт речь (Deepgram STT)
3. Генерирует ответ (Ollama LLM)
4. Синтезирует голос (Cartesia TTS)
5. Отправляет аудио клиенту
"""

import os
import asyncio
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import deepgram, cartesia, silero

# Загружаем переменные окружения
load_dotenv()


class VoiceAgent:
    """
    Голосовой агент для обработки звонков.
    
    Использование:
        agent = VoiceAgent(
            bot_name="Анна",
            company="Салон красоты",
            system_prompt="Ты администратор салона..."
        )
        agent.run()
    """
    
    def __init__(
        self,
        bot_name: str = "Ассистент",
        company: str = "",
        system_prompt: str = "",
        language: str = "ru",
        voice_id: str = None
    ):
        self.bot_name = bot_name
        self.company = company
        self.language = language
        self.voice_id = voice_id or self._get_default_voice(language)
        
        # Системный промпт
        self.system_prompt = system_prompt or self._build_default_prompt()
    
    def _get_default_voice(self, language: str) -> str:
        """Получить голос по умолчанию для языка."""
        # Cartesia voice IDs
        voices = {
            "ru": "f786b574-daa5-4673-aa0c-cbe3e8534c02",  # Russian female
            "en": "694f9389-aac1-45b6-b726-9d9369183238",  # English female
        }
        return voices.get(language, voices["en"])
    
    def _build_default_prompt(self) -> str:
        """Построить системный промпт по умолчанию."""
        return f"""Ты {self.bot_name}, голосовой ассистент компании {self.company}.

Правила:
- Отвечай коротко и по делу (1-2 предложения)
- Говори естественно, как человек
- Будь дружелюбным и помогай клиенту
- Если не знаешь ответ — честно скажи об этом

Язык: {'русский' if self.language == 'ru' else 'английский'}
"""
    
    async def create_session(self) -> AgentSession:
        """Создать сессию агента."""
        
        # STT — Deepgram
        stt = deepgram.STT(
            model="nova-3",
            language=self.language,
        )
        
        # TTS — Cartesia
        tts = cartesia.TTS(
            model="sonic-2",
            voice=self.voice_id,
            language=self.language,
        )
        
        # VAD — Voice Activity Detection (Silero)
        vad = silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.5,
        )
        
        # Создаём сессию
        session = AgentSession(
            stt=stt,
            tts=tts,
            vad=vad,
        )
        
        return session


# =============================================================================
# LiveKit Agent Entry Point
# =============================================================================

async def entrypoint(ctx: agents.JobContext):
    """
    Точка входа для LiveKit Agent.
    
    Вызывается когда клиент подключается к комнате.
    """
    
    # Создаём агента
    voice_agent = VoiceAgent(
        bot_name="Анна",
        company="AI Prosto",
        language="ru",
    )
    
    # Создаём сессию
    session = await voice_agent.create_session()
    
    # Подключаемся к комнате
    await ctx.connect()
    
    # Запускаем агента
    await session.start(
        room=ctx.room,
        participant=ctx.room.local_participant,
    )
    
    # Приветствие
    await session.say("Здравствуйте! Чем могу помочь?")
    
    # Ждём завершения
    await session.wait()


def run_agent():
    """Запустить агента."""
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )


if __name__ == "__main__":
    run_agent()
