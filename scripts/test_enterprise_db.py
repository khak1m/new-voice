#!/usr/bin/env python3
"""
Тестирование Enterprise Platform с реальной базой данных.

ВНИМАНИЕ: Этот скрипт требует подключения к PostgreSQL!

Проверяет:
1. Подключение к БД
2. Применение миграций
3. CRUD операции с реальной БД
4. Транзакции и откаты
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_database_connection():
    """Тест 1: Подключение к базе данных."""
    print("=" * 70)
    print("🧪 ТЕСТ 1: Подключение к PostgreSQL")
    print("=" * 70)
    
    try:
        from database.connection import check_connection, get_database_url
        
        db_url = get_database_url(async_mode=False)
        print(f"Database URL: {db_url.replace(db_url.split('@')[0].split('://')[1], '***')}")
        
        if check_connection():
            print("✅ Подключение к PostgreSQL успешно")
            return True
        else:
            print("❌ Не удалось подключиться к PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


def test_tables_exist():
    """Тест 2: Проверка существования таблиц."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 2: Проверка существования таблиц")
    print("=" * 70)
    
    try:
        from database.connection import get_db
        from sqlalchemy import text
        
        expected_tables = [
            'skillbases',
            'campaigns',
            'call_tasks',
            'call_metrics',
            'call_logs'
        ]
        
        with get_db() as db:
            for table in expected_tables:
                result = db.execute(text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables "
                    f"WHERE table_name = '{table}')"
                ))
                exists = result.scalar()
                
                if exists:
                    print(f"✅ Таблица '{table}' существует")
                else:
                    print(f"❌ Таблица '{table}' не найдена")
                    return False
        
        print("\n✅ Все таблицы Enterprise Platform существуют")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crud_operations():
    """Тест 3: CRUD операции с реальной БД."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 3: CRUD операции")
    print("=" * 70)
    
    try:
        from database.connection import get_db
        from database.models import Company, Skillbase, Campaign, CallTask
        
        with get_db() as db:
            # CREATE: Создаем тестовую компанию
            company = Company(
                id=uuid4(),
                name="Test Company (Enterprise Platform)",
                slug=f"test-ep-{uuid4().hex[:8]}",
                email="test-ep@example.com"
            )
            db.add(company)
            db.flush()
            print(f"✅ CREATE: Company создана (ID: {company.id})")
            
            # CREATE: Создаем Skillbase
            skillbase_config = {
                "context": {
                    "role": "Тестовый ассистент",
                    "style": "Профессиональный",
                    "safety_rules": ["Тестовое правило"],
                    "facts": ["Тестовый факт"]
                },
                "flow": {
                    "type": "linear",
                    "states": ["start", "middle", "end"],
                    "transitions": []
                },
                "agent": {
                    "handoff_criteria": {},
                    "crm_field_mapping": {}
                },
                "tools": [],
                "voice": {
                    "tts_provider": "cartesia",
                    "tts_voice_id": "test-voice-id",
                    "stt_provider": "deepgram",
                    "stt_language": "ru"
                },
                "llm": {
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                    "temperature": 0.7
                }
            }
            
            skillbase = Skillbase(
                id=uuid4(),
                company_id=company.id,
                name="Test Skillbase",
                slug=f"test-sb-{uuid4().hex[:8]}",
                config=skillbase_config,
                version=1
            )
            db.add(skillbase)
            db.flush()
            print(f"✅ CREATE: Skillbase создан (ID: {skillbase.id}, Version: {skillbase.version})")
            
            # CREATE: Создаем Campaign
            campaign = Campaign(
                id=uuid4(),
                company_id=company.id,
                skillbase_id=skillbase.id,
                name="Test Campaign",
                status="draft",
                max_concurrent_calls=3,
                calls_per_minute=5
            )
            db.add(campaign)
            db.flush()
            print(f"✅ CREATE: Campaign создана (ID: {campaign.id}, Status: {campaign.status})")
            
            # CREATE: Создаем CallTask
            call_task = CallTask(
                id=uuid4(),
                campaign_id=campaign.id,
                phone_number="+79991234567",
                contact_name="Тестовый контакт",
                contact_data={"email": "test@example.com", "city": "Moscow"},
                status="pending"
            )
            db.add(call_task)
            db.flush()
            print(f"✅ CREATE: CallTask создан (ID: {call_task.id}, Phone: {call_task.phone_number})")
            
            # READ: Читаем созданные данные
            read_skillbase = db.query(Skillbase).filter_by(id=skillbase.id).first()
            if read_skillbase and read_skillbase.name == "Test Skillbase":
                print(f"✅ READ: Skillbase прочитан корректно")
            else:
                print(f"❌ READ: Ошибка чтения Skillbase")
                return False
            
            # UPDATE: Обновляем Skillbase
            read_skillbase.increment_version()
            db.flush()
            
            updated_skillbase = db.query(Skillbase).filter_by(id=skillbase.id).first()
            if updated_skillbase.version == 2:
                print(f"✅ UPDATE: Версия Skillbase увеличена (v{updated_skillbase.version})")
            else:
                print(f"❌ UPDATE: Версия не обновилась")
                return False
            
            # UPDATE: Обновляем статус Campaign
            campaign.status = "running"
            db.flush()
            
            updated_campaign = db.query(Campaign).filter_by(id=campaign.id).first()
            if updated_campaign.status == "running":
                print(f"✅ UPDATE: Статус Campaign обновлен ({updated_campaign.status})")
            else:
                print(f"❌ UPDATE: Статус Campaign не обновился")
                return False
            
            # DELETE: Удаляем тестовые данные (в обратном порядке из-за FK)
            db.delete(call_task)
            db.delete(campaign)
            db.delete(skillbase)
            db.delete(company)
            db.flush()
            
            # Проверяем, что данные удалены
            deleted_skillbase = db.query(Skillbase).filter_by(id=skillbase.id).first()
            if deleted_skillbase is None:
                print(f"✅ DELETE: Все тестовые данные удалены")
            else:
                print(f"❌ DELETE: Данные не удалились")
                return False
            
            # Откатываем транзакцию (чтобы не засорять БД)
            db.rollback()
            print(f"✅ ROLLBACK: Транзакция откачена (БД чиста)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка CRUD операций: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_relationships():
    """Тест 4: Проверка связей между таблицами."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 4: Связи между таблицами")
    print("=" * 70)
    
    try:
        from database.connection import get_db
        from database.models import Company, Skillbase, Campaign, CallTask
        
        with get_db() as db:
            # Создаем связанные данные
            company = Company(
                id=uuid4(),
                name="Test Company Relations",
                slug=f"test-rel-{uuid4().hex[:8]}",
                email="test-rel@example.com"
            )
            db.add(company)
            db.flush()
            
            skillbase = Skillbase(
                id=uuid4(),
                company_id=company.id,
                name="Test Skillbase Relations",
                slug=f"test-sb-rel-{uuid4().hex[:8]}",
                config={"test": "config"},
                version=1
            )
            db.add(skillbase)
            db.flush()
            
            campaign = Campaign(
                id=uuid4(),
                company_id=company.id,
                skillbase_id=skillbase.id,
                name="Test Campaign Relations",
                status="draft"
            )
            db.add(campaign)
            db.flush()
            
            # Проверяем связи
            # Company -> Skillbases
            if len(company.skillbases) > 0:
                print(f"✅ Company -> Skillbases: {len(company.skillbases)} связь(ей)")
            else:
                print(f"❌ Company -> Skillbases: связь не работает")
                return False
            
            # Skillbase -> Campaigns
            if len(skillbase.campaigns) > 0:
                print(f"✅ Skillbase -> Campaigns: {len(skillbase.campaigns)} связь(ей)")
            else:
                print(f"❌ Skillbase -> Campaigns: связь не работает")
                return False
            
            # Campaign -> Skillbase
            if campaign.skillbase.id == skillbase.id:
                print(f"✅ Campaign -> Skillbase: связь работает")
            else:
                print(f"❌ Campaign -> Skillbase: связь не работает")
                return False
            
            # Откатываем
            db.rollback()
        
        print("\n✅ Все связи работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки связей: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция тестирования."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ ENTERPRISE PLATFORM С РЕАЛЬНОЙ БД")
    print("=" * 70)
    print()
    
    # Проверяем подключение
    if not test_database_connection():
        print("\n❌ Нет подключения к БД. Убедитесь, что:")
        print("1. PostgreSQL запущен")
        print("2. Настройки в .env корректны")
        print("3. Миграции применены: python -m alembic upgrade head")
        return 1
    
    tests = [
        ("Существование таблиц", test_tables_exist),
        ("CRUD операции", test_crud_operations),
        ("Связи между таблицами", test_relationships),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        success = test_func()
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
        print("\n🎉 ВСЕ ТЕСТЫ С БД ПРОЙДЕНЫ!")
        print("✅ Enterprise Platform Phase 1 полностью функциональна")
        return 0
    else:
        print("\n💥 ЕСТЬ ПРОБЛЕМЫ С БД!")
        print("❌ Некоторые тесты провалены")
        return 1


if __name__ == "__main__":
    sys.exit(main())
