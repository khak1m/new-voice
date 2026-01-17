#!/usr/bin/env python3
"""
Тестирование адаптера Skillbase → ScenarioEngine.

Этот скрипт:
1. Создаёт тестовый Skillbase config
2. Конвертирует его в ScenarioEngine config
3. Проверяет корректность конвертации

Запуск:
    python scripts/test_skillbase_scenario_adapter.py
"""

import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_adapter():
    """Тест адаптера Skillbase → ScenarioEngine."""
    print("=" * 70)
    print("🧪 ТЕСТ: Адаптер Skillbase → ScenarioEngine")
    print("=" * 70)
    
    try:
        from schemas.skillbase_schemas import SkillbaseConfig
        from adapters.skillbase_to_scenario import convert_skillbase_to_scenario
        
        # Тестовая конфигурация Skillbase
        skillbase_config_dict = {
            "context": {
                "role": "Администратор салона красоты",
                "style": "Дружелюбный и профессиональный",
                "safety_rules": [
                    "Не обсуждай политику и религию",
                    "Не давай медицинских советов"
                ],
                "facts": [
                    "Мы работаем с 9:00 до 21:00",
                    "У нас 5 мастеров",
                    "Принимаем оплату картой и наличными"
                ]
            },
            "flow": {
                "type": "linear",
                "states": [
                    "Приветствие",
                    "Узнать имя клиента",
                    "Узнать желаемую услугу",
                    "Предложить время записи",
                    "Подтвердить запись"
                ],
                "transitions": []
            },
            "agent": {
                "handoff_criteria": {},
                "crm_field_mapping": {}
            },
            "tools": [],
            "voice": {
                "tts_provider": "cartesia",
                "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                "stt_provider": "deepgram",
                "stt_language": "ru"
            },
            "llm": {
                "provider": "groq",
                "model": "llama-3.1-8b-instant",
                "temperature": 0.7
            }
        }
        
        # Валидируем Skillbase config
        skillbase_config = SkillbaseConfig(**skillbase_config_dict)
        print("✅ Skillbase config валиден")
        
        # Конвертируем в ScenarioEngine config + Tools
        scenario_config, tools = convert_skillbase_to_scenario(
            skillbase_config,
            "test-skillbase-id",
            "Салон красоты 'Элегант'"
        )
        
        print("✅ Конвертация успешна")
        print(f"✅ Tools загружены: {len(tools)}")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Проверяем результат
        print("\n" + "=" * 70)
        print("📋 РЕЗУЛЬТАТ КОНВЕРТАЦИИ:")
        print("=" * 70)
        
        print(f"\n🤖 Личность бота:")
        print(f"   Роль: {scenario_config.personality.role}")
        print(f"   Компания: {scenario_config.personality.company}")
        print(f"   Тон: {scenario_config.personality.tone}")
        
        print(f"\n🌍 Язык:")
        print(f"   По умолчанию: {scenario_config.language.default}")
        print(f"   Поддерживаемые: {', '.join(scenario_config.language.supported)}")
        print(f"   Авто-определение: {scenario_config.language.auto_detect}")
        
        print(f"\n📊 Этапы (States): {len(scenario_config.states)}")
        for i, state in enumerate(scenario_config.states, 1):
            print(f"   {i}. {state.name.ru} (ID: {state.id})")
            print(f"      Цель: {state.goal}")
            print(f"      Начальный: {state.is_start}, Конечный: {state.is_end}")
        
        print(f"\n🔀 Переходы (Transitions): {len(scenario_config.transitions)}")
        for i, trans in enumerate(scenario_config.transitions, 1):
            print(f"   {i}. {trans.from_state} → {trans.to_state}")
            print(f"      Условие: {trans.condition.type}")
        
        print(f"\n🎯 Outcomes: {len(scenario_config.outcomes)}")
        for outcome in scenario_config.outcomes:
            print(f"   - {outcome.name.ru} (ID: {outcome.id})")
        
        print(f"\n🛡️  Guardrails: {len(scenario_config.guardrails)}")
        for guard in scenario_config.guardrails:
            print(f"   - {guard.id}: {guard.action}")
        
        print("\n" + "=" * 70)
        
        # Проверяем что все обязательные поля заполнены
        assert scenario_config.bot_id == "test-skillbase-id"
        assert len(scenario_config.states) == 5
        assert len(scenario_config.transitions) == 4  # 5 этапов = 4 перехода
        assert scenario_config.states[0].is_start == True
        assert scenario_config.states[-1].is_end == True
        
        print("✅ Все проверки пройдены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция тестирования."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ АДАПТЕРА SKILLBASE → SCENARIOENGINE")
    print("=" * 70)
    print()
    
    success = test_adapter()
    
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    if success:
        print("✅ ТЕСТ ПРОЙДЕН")
        print("🎉 Адаптер работает корректно!")
        return 0
    else:
        print("❌ ТЕСТ ПРОВАЛЕН")
        print("💥 Есть проблемы с адаптером")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
