"""
Smart Voice Agent — интеграция с системой промптов и сбором данных.

Запуск:
    python -m src.voice_agent.smart_agent dev
    
    # С конкретным сценарием:
    SCENARIO=examples/scenarios/my_scenario.yaml python -m src.voice_agent.smart_agent dev
"""

import os
import yaml
import json
from typing import Optional
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

load_dotenv()

# =============================================================================
# Системный промпт
# =============================================================================

SYSTEM_PROMPT_BASE = """
# КТО ТЫ
Ты — голосовой ассистент, который звонит или отвечает на звонки от имени компании.
Ты говоришь как живой человек, а не как робот.

# КАК ГОВОРИТЬ

## Естественность речи
- Говори короткими фразами, 1-2 предложения максимум
- Используй разговорные слова: "ага", "понял", "так", "хорошо", "отлично"
- Делай паузы для размышления: "секундочку...", "так-так...", "дайте подумать..."
- Иногда переспрашивай: "правильно я понял, что...?", "то есть вы хотите...?"

## Чего НЕ делать
- Не говори длинными сложными предложениями
- Не используй канцелярит: "в рамках", "осуществить", "произвести"
- Не повторяй одно и то же разными словами
- Не говори "как я могу вам помочь" — это звучит как робот
- Не извиняйся слишком часто

## Реакции на собеседника
- Если человек перебил — остановись и слушай
- Если человек молчит — мягко продолжи разговор
- Если человек раздражён — будь спокойным и понимающим
- Если человек шутит — можешь легко поддержать

## Структура ответа
- Сначала короткая реакция на сказанное ("Понял", "Хорошо", "Ага")
- Потом основная мысль
- Если нужно — уточняющий вопрос

## Примеры хороших ответов
- "Ага, понял. А на какое время вам удобнее?"
- "Хорошо, записала. Это будет стрижка, верно?"
- "Так, секундочку... Да, на пятницу есть окошко в три часа."
- "Отлично! Тогда жду вас в субботу в 14:00."

## Примеры плохих ответов (НЕ ГОВОРИ ТАК)
- "Благодарю вас за предоставленную информацию. Позвольте уточнить..."
- "Я с радостью помогу вам осуществить запись на удобное для вас время."
- "Приношу свои извинения за возможные неудобства."

# ПРАВИЛА ДИАЛОГА

## Начало разговора
- Представься коротко
- Сразу переходи к делу
- Не спрашивай "как дела" — это раздражает

## Сбор информации
- Спрашивай по одному пункту за раз
- Подтверждай что услышал: "Так, Иван, записал"
- Если не расслышал — переспроси просто: "Простите, не расслышал имя"

## Завершение
- Кратко повтори договорённости
- Попрощайся тепло но коротко
- "Отлично, тогда ждём вас! До свидания!"

# ЯЗЫК
- Говори на русском языке
- Используй "вы" по умолчанию
- Если собеседник перешёл на "ты" — можешь тоже
"""


# =============================================================================
# Сборка промпта
# =============================================================================

def build_prompt(scenario: dict, collected_data: dict) -> str:
    """Собирает полный промпт из базового + сценария + собранных данных."""
    
    prompt = SYSTEM_PROMPT_BASE
    
    # Добавляем сценарий клиента
    prompt += "\n\n# ТВОЙ СЦЕНАРИЙ\n\n"
    
    # Компания
    if "company_name" in scenario:
        prompt += f"## Компания\nТы работаешь в компании \"{scenario['company_name']}\".\n"
    
    if "company_description" in scenario:
        prompt += f"{scenario['company_description']}\n"
    
    # Имя бота
    if "bot_name" in scenario:
        prompt += f"\n## Твоё имя\nТебя зовут {scenario['bot_name']}.\n"
    
    # Цель
    if "goal" in scenario:
        prompt += f"\n## Цель разговора\n{scenario['goal']}\n"
    
    # Что нужно собрать
    if "fields_to_collect" in scenario:
        prompt += "\n## Информация для сбора\nТебе нужно узнать у клиента:\n"
        for field in scenario["fields_to_collect"]:
            if isinstance(field, dict):
                field_name = field.get("name", "")
                field_desc = field.get("description", "")
                prompt += f"- {field_name}"
                if field_desc:
                    prompt += f" ({field_desc})"
            else:
                prompt += f"- {field}"
            prompt += "\n"
    
    # Дополнительные инструкции
    if "additional_instructions" in scenario:
        prompt += f"\n## Дополнительно\n{scenario['additional_instructions']}\n"
    
    # Собранные данные
    if collected_data:
        prompt += "\n## Уже собранные данные\n"
        prompt += "Эту информацию ты уже узнал, не спрашивай повторно:\n"
        for key, value in collected_data.items():
            prompt += f"- {key}: {value}\n"
    
    return prompt


# =============================================================================
# Загрузка сценария
# =============================================================================

def load_scenario(path: str) -> dict:
    """Загружает сценарий из YAML файла."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[Agent] Сценарий не найден: {path}")
        return {}


# =============================================================================
# Класс для отслеживания данных
# =============================================================================

class ConversationTracker:
    """Отслеживает собранные данные во время разговора."""
    
    def __init__(self, fields_to_collect: list):
        self.fields_to_collect = fields_to_collect
        self.collected_data = {}
        self.messages = []
    
    def add_message(self, role: str, content: str):
        """Добавить сообщение в историю."""
        self.messages.append({"role": role, "content": content})
    
    def get_collected(self) -> dict:
        """Получить собранные данные."""
        return self.collected_data
    
    def set_field(self, field: str, value: str):
        """Установить значение поля."""
        self.collected_data[field] = value
    
    def get_missing_fields(self) -> list:
        """Получить список несобранных полей."""
        collected_keys = set(self.collected_data.keys())
        missing = []
        for field in self.fields_to_collect:
            field_name = field.get("name") if isinstance(field, dict) else field
            if field_name not in collected_keys:
                missing.append(field)
        return missing
    
    def is_complete(self) -> bool:
        """Проверить все ли данные собраны."""
        return len(self.get_missing_fields()) == 0


# =============================================================================
# Глобальные переменные
# =============================================================================

SCENARIO_PATH = os.getenv("SCENARIO", "examples/scenarios/salon_scenario.yaml")
SCENARIO = load_scenario(SCENARIO_PATH)

if SCENARIO:
    print(f"[Agent] Загружен сценарий: {SCENARIO.get('company_name', 'Unknown')}")
else:
    SCENARIO = {
        "company_name": "AI Prosto",
        "bot_name": "Ассистент",
        "goal": "Помочь клиенту с его вопросом",
        "greeting": "Здравствуйте! Чем могу помочь?",
        "fields_to_collect": []
    }
    print("[Agent] Используется базовый сценарий")


# =============================================================================
# Точка входа
# =============================================================================

async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    await ctx.connect()
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    print(f"[Agent] Компания: {SCENARIO.get('company_name')}")
    print(f"[Agent] Бот: {SCENARIO.get('bot_name')}")
    
    # Трекер для отслеживания данных
    tracker = ConversationTracker(SCENARIO.get("fields_to_collect", []))
    
    # Собираем промпт
    full_prompt = build_prompt(SCENARIO, tracker.get_collected())
    
    # Создаём агента
    agent = Agent(instructions=full_prompt)
    
    # Ollama LLM
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
    
    # Приветствие
    greeting = SCENARIO.get("greeting", "Здравствуйте!")
    await session.say(greeting)
    
    print("[Agent] Агент запущен, ожидаю голос...")
    print(f"[Agent] Цель: {SCENARIO.get('goal', 'не указана')}")
    print(f"[Agent] Нужно собрать: {[f.get('name') if isinstance(f, dict) else f for f in SCENARIO.get('fields_to_collect', [])]}")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
