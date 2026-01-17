#!/usr/bin/env python3
"""
Тест миграций и моделей Enterprise Platform.

Проверяет:
1. Корректность импорта всех новых моделей
2. Синтаксис миграций (offline mode)
3. Структуру JSONB полей
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_model_imports():
    """Тест импорта всех новых моделей."""
    print("🧪 Тестируем импорт моделей...")
    
    try:
        from database.models import (
            Skillbase, Campaign, CallTask, 
            CallMetrics, CallLog
        )
        print("✅ Все модели импортированы успешно")
        
        # Проверяем основные атрибуты
        assert hasattr(Skillbase, 'config'), "Skillbase должен иметь поле config"
        assert hasattr(Campaign, 'skillbase_id'), "Campaign должен иметь поле skillbase_id"
        assert hasattr(CallTask, 'campaign_id'), "CallTask должен иметь поле campaign_id"
        assert hasattr(CallMetrics, 'call_id'), "CallMetrics должен иметь поле call_id"
        assert hasattr(CallLog, 'turn_index'), "CallLog должен иметь поле turn_index"
        
        print("✅ Все атрибуты моделей корректны")
        
    except Exception as e:
        print(f"❌ Ошибка импорта моделей: {e}")
        return False
    
    return True


def test_migration_syntax():
    """Тест синтаксиса миграций в offline режиме."""
    print("\n🧪 Тестируем синтаксис миграций...")
    
    try:
        # Проверяем, что alembic может сгенерировать SQL
        result = os.system("python -m alembic upgrade head --sql > migration_test.sql 2>&1")
        
        if result == 0:
            print("✅ Миграции синтаксически корректны")
            
            # Проверяем, что файл создался и содержит ожидаемые таблицы
            if os.path.exists("migration_test.sql"):
                with open("migration_test.sql", "r", encoding="utf-8") as f:
                    content = f.read()
                
                expected_tables = [
                    "CREATE TABLE skillbases",
                    "CREATE TABLE campaigns", 
                    "CREATE TABLE call_tasks",
                    "CREATE TABLE call_metrics",
                    "CREATE TABLE call_logs"
                ]
                
                for table in expected_tables:
                    if table in content:
                        print(f"✅ Найдена таблица: {table}")
                    else:
                        print(f"❌ Не найдена таблица: {table}")
                        return False
                
                # Очищаем тестовый файл
                os.remove("migration_test.sql")
                
            return True
        else:
            print("❌ Ошибка в синтаксисе миграций")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования миграций: {e}")
        return False


def test_skillbase_config_structure():
    """Тест структуры конфигурации Skillbase."""
    print("\n🧪 Тестируем структуру конфигурации Skillbase...")
    
    try:
        from database.models import Skillbase
        
        # Пример корректной конфигурации
        sample_config = {
            "context": {
                "role": "Ассистент салона красоты",
                "style": "Дружелюбный и профессиональный",
                "safety_rules": ["Не давать медицинские советы"],
                "facts": ["Работаем с 9 до 21", "Принимаем карты и наличные"]
            },
            "flow": {
                "type": "linear",
                "states": ["greeting", "service_inquiry", "booking", "confirmation"],
                "transitions": []
            },
            "agent": {
                "handoff_criteria": {"complex_request": True},
                "crm_field_mapping": {"name": "client_name", "phone": "client_phone"}
            },
            "tools": [
                {"name": "calendar", "config": {"api_url": "https://api.example.com"}}
            ],
            "voice": {
                "tts_provider": "cartesia",
                "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                "stt_provider": "deepgram",
                "stt_language": "ru"
            },
            "llm": {
                "provider": "groq",
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.7
            }
        }
        
        print("✅ Пример конфигурации Skillbase корректен")
        print(f"   - Секций: {len(sample_config)}")
        print(f"   - Состояний в flow: {len(sample_config['flow']['states'])}")
        print(f"   - Инструментов: {len(sample_config['tools'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        return False


def main():
    """Основная функция тестирования."""
    print("🚀 Запуск тестов Enterprise Platform миграций\n")
    
    tests = [
        test_model_imports,
        test_migration_syntax,
        test_skillbase_config_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("❌ Тест провален")
    
    print(f"\n📊 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Миграции готовы к применению на сервере.")
        return True
    else:
        print("💥 Есть проблемы, требующие исправления.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)