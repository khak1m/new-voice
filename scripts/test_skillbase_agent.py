#!/usr/bin/env python3
"""
Тестирование Skillbase Voice Agent.

Этот скрипт:
1. Создаёт тестовый Skillbase в БД
2. Тестирует SystemPromptBuilder
3. Выводит сгенерированный промпт

Запуск:
    python scripts/test_skillbase_agent.py
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

load_dotenv()


async def test_prompt_builder():
    """Тест 1: SystemPromptBuilder."""
    print("=" * 70)
    print("🧪 ТЕСТ 1: SystemPromptBuilder")
    print("=" * 70)
    
    try:
        from schemas.skillbase_schemas import SkillbaseConfig
        from prompts.skillbase_prompt_builder import build_prompt_from_skillbase
        
        # Проверяем, что базовый промпт существует
        base_prompt_path = Path(__file__).parent.parent / "config" / "base_prompt.txt"
        if base_prompt_path.exists():
            print(f"✅ Базовый промпт найден: {base_prompt_path}")
            with open(base_prompt_path, "r", encoding="utf-8") as f:
                base_content = f.read()
            print(f"   Размер: {len(base_content)} символов")
        else:
            print(f"⚠️  Базовый промпт не найден: {base_prompt_path}")
            print("   Будет использован fallback промпт")
        
        # Тестовая конфигурация
        test_config = {
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
        
        # Валидируем конфигурацию
        config = SkillbaseConfig(**test_config)
        print("✅ Конфигурация валидна")
        
        # Строим промпт
        prompt = build_prompt_from_skillbase(config, "Салон красоты 'Элегант'")
        
        print(f"✅ Промпт построен ({len(prompt)} символов)")
        print("\n" + "=" * 70)
        print("📝 СГЕНЕРИРОВАННЫЙ ПРОМПТ:")
        print("=" * 70)
        print(prompt)
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_create_skillbase():
    """Тест 2: Создание Skillbase в БД."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 2: Создание Skillbase в БД")
    print("=" * 70)
    
    try:
        from database.connection import get_async_db
        from database.models import Company
        from services.skillbase_service import SkillbaseService
        from schemas.skillbase_schemas import SkillbaseConfig
        
        async with get_async_db() as db:
            # Создаём тестовую компанию
            company = Company(
                id=uuid4(),
                name="Салон красоты 'Элегант'",
                slug=f"salon-elegant-{uuid4().hex[:8]}",
                email="test@salon-elegant.ru"
            )
            db.add(company)
            await db.flush()
            
            print(f"✅ Компания создана: {company.name} (ID: {company.id})")
            
            # Конфигурация Skillbase
            skillbase_config = {
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
            
            # Создаём Skillbase через сервис
            service = SkillbaseService(db)
            skillbase = await service.create(
                company_id=company.id,
                name="Салон - Запись клиентов",
                slug=f"salon-booking-{uuid4().hex[:8]}",
                description="Skillbase для записи клиентов в салон красоты",
                config=skillbase_config
            )
            
            print(f"✅ Skillbase создан: {skillbase.name} (ID: {skillbase.id})")
            print(f"   Version: {skillbase.version}")
            print(f"   Slug: {skillbase.slug}")
            
            # Откатываем транзакцию (чтобы не засорять БД)
            await db.rollback()
            print("✅ Транзакция откачена (тестовые данные не сохранены)")
            
            print("\n" + "=" * 70)
            print("📋 ДЛЯ ЗАПУСКА АГЕНТА С ЭТИМ SKILLBASE:")
            print("=" * 70)
            print(f"SKILLBASE_ID={skillbase.id} python -m src.voice_agent.skillbase_voice_agent dev")
            print("=" * 70)
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_load_skillbase():
    """Тест 3: Загрузка существующего Skillbase."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 3: Загрузка существующего Skillbase")
    print("=" * 70)
    
    try:
        from database.connection import get_async_db
        from services.skillbase_service import SkillbaseService
        from sqlalchemy import select
        from database.models import Skillbase
        
        async with get_async_db() as db:
            # Ищем любой Skillbase в БД
            result = await db.execute(
                select(Skillbase).limit(1)
            )
            skillbase = result.scalar_one_or_none()
            
            if not skillbase:
                print("⚠️  В БД нет Skillbase для тестирования")
                print("   Создайте Skillbase через API или запустите тест 2")
                return False
            
            print(f"✅ Найден Skillbase: {skillbase.name}")
            print(f"   ID: {skillbase.id}")
            print(f"   Version: {skillbase.version}")
            
            # Загружаем через сервис
            service = SkillbaseService(db)
            loaded = await service.get_by_id(skillbase.id, eager_load=True)
            
            print(f"✅ Skillbase загружен через сервис")
            print(f"   Company: {loaded.company.name if loaded.company else 'N/A'}")
            
            # Строим промпт
            from schemas.skillbase_schemas import SkillbaseConfig
            from prompts.skillbase_prompt_builder import build_prompt_from_skillbase
            
            config = SkillbaseConfig(**loaded.config)
            company_name = loaded.company.name if loaded.company else "Компания"
            prompt = build_prompt_from_skillbase(config, company_name)
            
            print(f"✅ Промпт построен ({len(prompt)} символов)")
            
            print("\n" + "=" * 70)
            print("📋 ДЛЯ ЗАПУСКА АГЕНТА:")
            print("=" * 70)
            print(f"SKILLBASE_ID={skillbase.id} python -m src.voice_agent.skillbase_voice_agent dev")
            print("=" * 70)
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ SKILLBASE VOICE AGENT")
    print("=" * 70)
    print()
    
    tests = [
        ("SystemPromptBuilder", test_prompt_builder),
        ("Создание Skillbase", test_create_skillbase),
        ("Загрузка Skillbase", test_load_skillbase),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        success = await test_func()
        results.append((test_name, success))
    
    # Итоговый отчет
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Результат: {passed}/{total} тестов пройдено ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Skillbase Voice Agent готов к использованию")
        return 0
    else:
        print("\n💥 ЕСТЬ ПРОБЛЕМЫ!")
        print("❌ Некоторые тесты провалены")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
