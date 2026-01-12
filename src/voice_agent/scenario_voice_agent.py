"""
Voice Agent с интеграцией Scenario Engine.

Бот работает по сценарию из YAML файла:
- Приветствует клиента
- Собирает нужные данные (имя, телефон, услуга, дата)
- Ведёт естественный диалог
- Завершает с результатом (лид, перезвон, и т.д.)

Запуск:
    python -m src.voice_agent.scenario_voice_agent dev
    
    # С указанием сценария:
    SCENARIO_PATH=examples/scenarios/salon_scenario.yaml python -m src.voice_agent.scenario_voice_agent dev
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

# Загружаем переменные окружения
load_dotenv()

# Путь к сценарию (по умолчанию — салон)
SCENARIO_PATH = os.getenv("SCENARIO_PATH", "examples/scenarios/salon_scenario.yaml")


def load_scenario(path: str) -> dict:
    """Загрузить сценарий из YAML файла."""
    scenario_file = Path(path)
    
    if not scenario_file.exists():
        print(f"[Warning] Сценарий не найден: {path}, использую дефолтный")
        return get_default_scenario()
    
    with open(scenario_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_default_scenario() -> dict:
    """Дефолтный сценарий если файл не найден."""
    return {
        "company_name": "AI Prosto",
        "bot_name": "Ассистент",
        "goal": "Помочь клиенту с его вопросом",
        "greeting": "Здравствуйте! Чем могу помочь?",
        "fields_to_collect": [],
    }


def build_instructions(scenario: dict) -> str:
    """
    Построить инструкции для агента из сценария.
    
    Это главный промпт, который определяет поведение бота.
    """
    
    instructions = """# КТО ТЫ
Ты — голосовой ассистент, который отвечает на звонки.
Говори как живой человек, а не как робот.

# КАК ГОВОРИТЬ
- Короткие фразы, 1-2 предложения
- Разговорные слова: "ага", "понял", "хорошо", "отлично"
- Паузы: "секундочку...", "так-так..."
- Переспрашивай если нужно: "правильно понял, что...?"

# ЧЕГО НЕ ДЕЛАТЬ
- Длинные сложные предложения
- Канцелярит: "в рамках", "осуществить"
- Повторять одно и то же
- Говорить "как я могу вам помочь"
- Извиняться слишком часто

"""
    
    # Компания и имя
    company = scenario.get("company_name", "Компания")
    bot_name = scenario.get("bot_name", "Ассистент")
    
    instructions += f"""# ТВОЯ РОЛЬ
Ты работаешь в компании "{company}".
Тебя зовут {bot_name}.

"""
    
    # Описание компании
    if "company_description" in scenario:
        instructions += f"""# О КОМПАНИИ
{scenario['company_description']}

"""
    
    # Цель
    if "goal" in scenario:
        instructions += f"""# ТВОЯ ЗАДАЧА
{scenario['goal']}

"""
    
    # Что собирать
    if scenario.get("fields_to_collect"):
        instructions += "# ЧТО НУЖНО УЗНАТЬ\n"
        instructions += "Постепенно узнай у клиента:\n"
        for field in scenario["fields_to_collect"]:
            if isinstance(field, dict):
                name = field.get("name", "")
                desc = field.get("description", "")
                instructions += f"- {name}: {desc}\n"
            else:
                instructions += f"- {field}\n"
        instructions += "\nСпрашивай по одному пункту за раз!\n\n"
    
    # Дополнительные инструкции
    if "additional_instructions" in scenario:
        instructions += f"""# ДОПОЛНИТЕЛЬНО
{scenario['additional_instructions']}

"""
    
    # Язык
    instructions += """# ЯЗЫК
- Говори на русском языке
- Используй "вы" по умолчанию
"""
    
    return instructions


async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    # Подключаемся к комнате
    await ctx.connect()
    
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    
    # Загружаем сценарий
    scenario = load_scenario(SCENARIO_PATH)
    print(f"[Agent] Загружен сценарий: {scenario.get('company_name', 'Unknown')}")
    
    # Строим инструкции
    instructions = build_instructions(scenario)
    
    # Создаём агента
    agent = Agent(instructions=instructions)
    
    # LLM через Ollama
    llm = openai.LLM(
        model="qwen2:1.5b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )
    
    # Голос — русский
    voice_id = scenario.get("voice_id", "064b17af-d36b-4bfb-b003-be07dba1b649")
    
    # Создаём сессию
    session = AgentSession(
        llm=llm,
        stt=deepgram.STT(
            model="nova-2",
            language="ru",
        ),
        tts=cartesia.TTS(
            model="sonic-2",
            voice=voice_id,
            language="ru",
        ),
        vad=silero.VAD.load(),
    )
    
    # Запускаем
    await session.start(agent, room=ctx.room)
    
    # Приветствие из сценария
    greeting = scenario.get("greeting", "Здравствуйте! Чем могу помочь?")
    await session.say(greeting)
    
    print(f"[Agent] Приветствие: {greeting}")
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
