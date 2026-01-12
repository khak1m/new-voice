"""
Voice Agent с поддержкой сценариев.
Загружает сценарий из YAML и строит промпт.

Запуск:
    python -m src.voice_agent.scenario_agent dev
    
    # С конкретным сценарием:
    SCENARIO=examples/scenarios/salon_scenario.yaml python -m src.voice_agent.scenario_agent dev
"""

import os
import yaml
from dotenv import load_dotenv

from livekit.agents import cli, WorkerOptions, JobContext
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, cartesia, silero, openai

# Импортируем систему промптов
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.prompts import build_full_prompt

load_dotenv()


def load_scenario(scenario_path: str) -> dict:
    """Загружает сценарий из YAML файла."""
    with open(scenario_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Загружаем сценарий
SCENARIO_PATH = os.getenv("SCENARIO", "examples/scenarios/salon_scenario.yaml")
print(f"[Agent] Загружаю сценарий: {SCENARIO_PATH}")

try:
    SCENARIO = load_scenario(SCENARIO_PATH)
    FULL_PROMPT = build_full_prompt(SCENARIO)
    print(f"[Agent] Сценарий загружен: {SCENARIO.get('company_name', 'Unknown')}")
except FileNotFoundError:
    print(f"[Agent] Сценарий не найден: {SCENARIO_PATH}, использую базовый")
    SCENARIO = {
        "company_name": "AI Prosto",
        "bot_name": "Ассистент",
        "goal": "Помочь клиенту с его вопросом",
        "greeting": "Здравствуйте! Чем могу помочь?"
    }
    FULL_PROMPT = build_full_prompt(SCENARIO)


async def entrypoint(ctx: JobContext):
    """Точка входа агента."""
    
    await ctx.connect()
    print(f"[Agent] Подключен к комнате: {ctx.room.name}")
    print(f"[Agent] Компания: {SCENARIO.get('company_name')}")
    print(f"[Agent] Бот: {SCENARIO.get('bot_name')}")
    
    # Создаём агента с полным промптом
    agent = Agent(instructions=FULL_PROMPT)
    
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
    
    # Приветствие из сценария
    greeting = SCENARIO.get("greeting", "Здравствуйте!")
    await session.say(greeting)
    
    print("[Agent] Агент запущен, ожидаю голос...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
