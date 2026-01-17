"""
Voice Agent с загрузкой конфигурации из Skillbase (БД) + ScenarioEngine.

Этот агент:
- Загружает Skillbase из PostgreSQL по ID
- Конвертирует Skillbase.config → ScenarioEngine.config
- Использует ScenarioEngine для управления диалогом
- Использует настройки LLM, TTS, STT из конфигурации
- Поддерживает интеграцию с Knowledge Base

Запуск:
    # С указанием Skillbase ID через переменную окружения
    SKILLBASE_ID=<uuid> python -m src.voice_agent.skillbase_voice_agent dev
    
    # Или через аргумент командной строки (TODO)
"""

import os
import asyncio
from uuid import UUID
from typing import Optional
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

# Наши модули
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_async_db
from services.skillbase_service import SkillbaseService
from schemas.skillbase_schemas import SkillbaseConfig
from prompts.skillbase_prompt_builder import build_prompt_from_skillbase
from adapters.skillbase_to_scenario import convert_skillbase_to_scenario
from scenario_engine.engine import ScenarioEngine

# Загружаем переменные окружения
load_dotenv()

# Skillbase ID из переменной окружения
SKILLBASE_ID = os.getenv("SKILLBASE_ID")


async def load_skillbase_config(skillbase_id: UUID) -> tuple[SkillbaseConfig, str, ScenarioEngine]:
    """
    Загрузить Skillbase из БД и создать ScenarioEngine.
    
    Args:
        skillbase_id: UUID Skillbase
        
    Returns:
        Tuple (SkillbaseConfig, company_name, ScenarioEngine)
        
    Raises:
        ValueError: Если Skillbase не найден
    """
    async with get_async_db() as db:
        service = SkillbaseService(db)
        
        # Загружаем Skillbase с eager loading (company, knowledge_base)
        skillbase = await service.get_by_id(skillbase_id, eager_load=True)
        
        if not skillbase:
            raise ValueError(f"Skillbase {skillbase_id} не найден")
        
        # Валидируем и парсим config
        config = SkillbaseConfig(**skillbase.config)
        
        # Получаем название компании
        company_name = skillbase.company.name if skillbase.company else "Компания"
        
        # Конвертируем Skillbase config → ScenarioEngine config
        scenario_config = convert_skillbase_to_scenario(
            config,
            str(skillbase.id),
            company_name
        )
        
        # Создаём ScenarioEngine
        engine = ScenarioEngine(scenario_config)
        
        print(f"[Skillbase] Загружен: {skillbase.name} (v{skillbase.version})")
        print(f"[Skillbase] Компания: {company_name}")
        print(f"[Skillbase] LLM: {config.llm.provider}/{config.llm.model}")
        print(f"[Skillbase] TTS: {config.voice.tts_provider}")
        print(f"[Skillbase] STT: {config.voice.stt_provider}")
        print(f"[ScenarioEngine] States: {len(scenario_config.states)}")
        print(f"[ScenarioEngine] Transitions: {len(scenario_config.transitions)}")
        
        return config, company_name, engine


def create_llm_from_config(config: SkillbaseConfig):
    """
    Создать LLM провайдер из конфигурации.
    
    Args:
        config: Skillbase конфигурация
        
    Returns:
        LLM instance
    """
    if config.llm.provider == "groq":
        # Groq через OpenAI-совместимый API
        return openai.LLM(
            model=config.llm.model,
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=config.llm.temperature,
        )
    elif config.llm.provider == "openai":
        return openai.LLM(
            model=config.llm.model,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=config.llm.temperature,
        )
    else:
        raise ValueError(f"Неподдерживаемый LLM провайдер: {config.llm.provider}")


def create_stt_from_config(config: SkillbaseConfig):
    """
    Создать STT провайдер из конфигурации.
    
    Args:
        config: Skillbase конфигурация
        
    Returns:
        STT instance
    """
    if config.voice.stt_provider == "deepgram":
        return deepgram.STT(
            model="nova-2",
            language=config.voice.stt_language or "ru",
        )
    else:
        raise ValueError(f"Неподдерживаемый STT провайдер: {config.voice.stt_provider}")


def create_tts_from_config(config: SkillbaseConfig):
    """
    Создать TTS провайдер из конфигурации.
    
    Args:
        config: Skillbase конфигурация
        
    Returns:
        TTS instance
    """
    if config.voice.tts_provider == "cartesia":
        return cartesia.TTS(
            model="sonic-2",
            voice=config.voice.tts_voice_id,
            language=config.voice.stt_language or "ru",
        )
    else:
        raise ValueError(f"Неподдерживаемый TTS провайдер: {config.voice.tts_provider}")


async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    # Проверяем, что SKILLBASE_ID указан
    if not SKILLBASE_ID:
        print("[ERROR] SKILLBASE_ID не указан в переменных окружения!")
        print("Использование: SKILLBASE_ID=<uuid> python -m src.voice_agent.skillbase_voice_agent dev")
        return
    
    try:
        skillbase_id = UUID(SKILLBASE_ID)
    except ValueError:
        print(f"[ERROR] Неверный формат SKILLBASE_ID: {SKILLBASE_ID}")
        return
    
    # Подключаемся к комнате
    await ctx.connect()
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    
    # Загружаем Skillbase из БД и создаём ScenarioEngine
    try:
        config, company_name, engine = await load_skillbase_config(skillbase_id)
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить Skillbase: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Строим system prompt из конфигурации
    instructions = build_prompt_from_skillbase(config, company_name)
    
    print(f"[Agent] System prompt построен ({len(instructions)} символов)")
    
    # Создаём агента
    agent = Agent(instructions=instructions)
    
    # Создаём LLM, STT, TTS из конфигурации
    try:
        llm = create_llm_from_config(config)
        stt = create_stt_from_config(config)
        tts = create_tts_from_config(config)
    except Exception as e:
        print(f"[ERROR] Не удалось создать провайдеры: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Создаём сессию
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        vad=silero.VAD.load(),
    )
    
    # Запускаем
    await session.start(agent, room=ctx.room)
    
    # Начинаем звонок через ScenarioEngine
    call_id = ctx.room.name
    greeting = engine.start_call(call_id, direction="inbound")
    
    # Отправляем приветствие
    await session.say(greeting)
    
    print(f"[Agent] Приветствие: {greeting}")
    print("[Agent] Агент запущен, ожидаю голос...")
    print(f"[ScenarioEngine] Текущий этап: {engine.get_context().current_state_id}")
    
    # TODO: Интегрировать обработку реплик через engine.process_turn()
    # Пока работает через стандартный Agent loop


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
