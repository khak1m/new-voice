"""
Full Voice Agent — полная интеграция с ScenarioEngine.

Профессиональная реализация:
- ScenarioEngine для управления диалогом
- Извлечение данных из речи (FieldExtractor)
- Машина состояний (StateMachine)
- Классификация результатов (OutcomeClassifier)
- Определение языка (LanguageDetector)

Запуск:
    python -m src.voice_agent.full_agent dev
    
    # С конкретным конфигом:
    BOT_CONFIG=examples/salon_bot_config.yaml python -m src.voice_agent.full_agent dev
"""

import os
import asyncio
from typing import Optional
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

# Импортируем ScenarioEngine
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.scenario_engine import (
    ScenarioEngine,
    load_config,
    ScenarioConfig,
    CallContext,
    TurnResult,
)
from src.prompts.system_prompt import SYSTEM_PROMPT_BASE

load_dotenv()


# =============================================================================
# LLM Provider для ScenarioEngine
# =============================================================================

class OllamaLLMProvider:
    """
    Ollama LLM провайдер для ScenarioEngine.
    Реализует интерфейс LLMProvider.
    """
    
    def __init__(self, model: str = "qwen2:1.5b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._client = None
    
    def _get_client(self):
        """Ленивая инициализация клиента."""
        if self._client is None:
            import httpx
            self._client = httpx.Client(base_url=self.base_url, timeout=30.0)
        return self._client
    
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 150
    ) -> str:
        """Сгенерировать ответ через Ollama."""
        try:
            client = self._get_client()
            
            # Формируем запрос
            ollama_messages = [{"role": "system", "content": system_prompt}]
            ollama_messages.extend(messages)
            
            response = client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                print(f"[LLM] Ошибка Ollama: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"[LLM] Ошибка: {e}")
            return ""


# =============================================================================
# Построитель промпта
# =============================================================================

class PromptBuilder:
    """Строит промпт для LLM на основе контекста."""
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
    
    def build_full_prompt(self, context: CallContext, current_state_goal: str = "") -> str:
        """Собрать полный промпт."""
        
        prompt = SYSTEM_PROMPT_BASE
        
        # Добавляем информацию о компании
        personality = self.config.personality
        prompt += f"\n\n# ТВОЯ РОЛЬ\n"
        prompt += f"Ты — {personality.name}, {personality.role} в компании \"{personality.company}\".\n"
        
        if personality.language_style:
            prompt += f"\nСтиль общения:\n{personality.language_style}\n"
        
        if personality.base_system_prompt:
            prompt += f"\n{personality.base_system_prompt}\n"
        
        # Текущий этап
        if current_state_goal:
            prompt += f"\n# ТЕКУЩАЯ ЗАДАЧА\n{current_state_goal}\n"
        
        # Собранные данные
        if context.collected_data:
            prompt += "\n# УЖЕ ИЗВЕСТНО О КЛИЕНТЕ\n"
            for key, value in context.collected_data.items():
                if not key.startswith("_"):  # Пропускаем служебные поля
                    prompt += f"- {key}: {value}\n"
        
        # Язык
        prompt += f"\n# ЯЗЫК\nГовори на {'русском' if context.language == 'ru' else 'английском'} языке.\n"
        
        return prompt


# =============================================================================
# Voice Agent с ScenarioEngine
# =============================================================================

class ScenarioVoiceAgent:
    """
    Голосовой агент с полной интеграцией ScenarioEngine.
    """
    
    def __init__(self, config_path: str):
        # Загружаем конфигурацию
        self.config = load_config(config_path)
        print(f"[Agent] Загружен конфиг: {self.config.bot_id}")
        print(f"[Agent] Компания: {self.config.personality.company}")
        print(f"[Agent] Бот: {self.config.personality.name}")
        
        # Создаём ScenarioEngine
        self.engine = ScenarioEngine(self.config)
        
        # Подключаем LLM провайдер
        self.llm_provider = OllamaLLMProvider()
        self.engine.set_llm_provider(self.llm_provider)
        
        # Построитель промптов
        self.prompt_builder = PromptBuilder(self.config)
        
        # Состояние
        self.call_id: Optional[str] = None
        self.session: Optional[AgentSession] = None
    
    def get_current_prompt(self) -> str:
        """Получить текущий промпт для LLM."""
        if not self.engine.is_call_active():
            return SYSTEM_PROMPT_BASE
        
        context = self.engine.get_context()
        
        # Получаем текущий этап
        current_state = None
        for state in self.config.states:
            if state.id == context.current_state_id:
                current_state = state
                break
        
        goal = current_state.goal if current_state else ""
        
        return self.prompt_builder.build_full_prompt(context, goal)
    
    async def start_call(self, call_id: str) -> str:
        """Начать звонок."""
        self.call_id = call_id
        greeting = self.engine.start_call(call_id)
        print(f"[Agent] Звонок начат: {call_id}")
        print(f"[Agent] Приветствие: {greeting}")
        return greeting
    
    async def process_user_input(self, user_text: str) -> str:
        """Обработать реплику пользователя."""
        if not self.engine.is_call_active():
            return "Звонок не активен."
        
        print(f"[Agent] Пользователь: {user_text}")
        
        # Обрабатываем через ScenarioEngine
        result: TurnResult = self.engine.process_turn(user_text)
        
        print(f"[Agent] Этап: {result.current_state_id}")
        print(f"[Agent] Ответ: {result.response}")
        
        if result.collected_in_turn:
            print(f"[Agent] Собрано: {result.collected_in_turn}")
        
        if result.should_end:
            print(f"[Agent] Завершение: {result.outcome}")
            await self.end_call(result.outcome or "completed")
        
        return result.response
    
    async def end_call(self, reason: str = "completed"):
        """Завершить звонок."""
        if self.engine.is_call_active():
            result = self.engine.end_call(reason)
            print(f"[Agent] Звонок завершён")
            print(f"[Agent] Outcome: {result.outcome}")
            print(f"[Agent] Собранные данные: {result.collected_data}")
            print(f"[Agent] Длительность: {result.duration_sec} сек")
            return result
        return None


# =============================================================================
# Глобальные переменные
# =============================================================================

CONFIG_PATH = os.getenv("BOT_CONFIG", "examples/salon_bot_config.yaml")
AGENT: Optional[ScenarioVoiceAgent] = None


# =============================================================================
# Точка входа
# =============================================================================

async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    global AGENT
    
    await ctx.connect()
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    
    # Создаём агента со сценарием
    try:
        AGENT = ScenarioVoiceAgent(CONFIG_PATH)
    except Exception as e:
        print(f"[Agent] Ошибка загрузки конфига: {e}")
        print(f"[Agent] Использую базовый режим")
        AGENT = None
    
    # Получаем промпт
    if AGENT:
        initial_prompt = AGENT.get_current_prompt()
    else:
        initial_prompt = SYSTEM_PROMPT_BASE + "\n\nТы ассистент компании AI Prosto. Помоги клиенту."
    
    # Создаём LiveKit агента
    agent = Agent(instructions=initial_prompt)
    
    # Ollama LLM для LiveKit
    llm = openai.LLM(
        model="qwen2:1.5b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )
    
    # Создаём сессию
    session = AgentSession(
        llm=llm,
        stt=deepgram.STT(model="nova-2", language="ru"),
        tts=cartesia.TTS(
            model="sonic-2",
            voice="064b17af-d36b-4bfb-b003-be07dba1b649",
            language="ru",
        ),
        vad=silero.VAD.load(),
    )
    
    # Запускаем
    await session.start(agent, room=ctx.room)
    
    # Начинаем звонок в ScenarioEngine
    if AGENT:
        greeting = await AGENT.start_call(ctx.room.name)
        await session.say(greeting)
    else:
        await session.say("Здравствуйте! Чем могу помочь?")
    
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
