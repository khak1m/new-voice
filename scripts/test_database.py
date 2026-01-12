#!/usr/bin/env python3
"""
Тест подключения к базе данных.

Запуск:
    python scripts/test_database.py
"""

import os
import sys
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_sync_connection():
    """Тест синхронного подключения."""
    print("\n🔄 Тестирую синхронное подключение...")
    
    try:
        from src.database.connection import get_db, get_database_url
        
        url = get_database_url(async_mode=False)
        print(f"   URL: {url.replace(os.getenv('DB_PASSWORD', ''), '***')}")
        
        with get_db() as db:
            result = db.execute("SELECT version()").fetchone()
            print(f"   ✅ PostgreSQL: {result[0][:50]}...")
            
            # Проверяем таблицы
            result = db.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """).fetchall()
            
            tables = [r[0] for r in result]
            print(f"   📋 Таблицы ({len(tables)}): {', '.join(tables)}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


async def test_async_connection():
    """Тест асинхронного подключения."""
    print("\n🔄 Тестирую асинхронное подключение...")
    
    try:
        from src.database.connection import get_async_db
        from sqlalchemy import text
        
        async with get_async_db() as db:
            result = await db.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"   ✅ PostgreSQL (async): {version[0][:50]}...")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_models():
    """Тест моделей."""
    print("\n🔄 Тестирую модели...")
    
    try:
        from src.database.models import Company, Bot, Call, Lead
        from src.database.connection import get_db
        
        with get_db() as db:
            # Проверяем тестовую компанию
            from sqlalchemy import text
            result = db.execute(text("SELECT id, name, slug FROM companies LIMIT 1")).fetchone()
            
            if result:
                print(f"   ✅ Тестовая компания: {result[1]} ({result[2]})")
            else:
                print("   ⚠️ Тестовая компания не найдена")
                
            # Считаем записи
            for table in ["companies", "users", "bots", "calls", "leads"]:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                print(f"   📊 {table}: {result[0]} записей")
                
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def main():
    """Главная функция."""
    print("=" * 50)
    print("🗄️  NEW-VOICE 2.0 — Тест базы данных")
    print("=" * 50)
    
    # Показываем конфигурацию
    print("\n📋 Конфигурация:")
    print(f"   DB_HOST: {os.getenv('DB_HOST', 'localhost')}")
    print(f"   DB_PORT: {os.getenv('DB_PORT', '5432')}")
    print(f"   DB_NAME: {os.getenv('DB_NAME', 'newvoice')}")
    print(f"   DB_USER: {os.getenv('DB_USER', 'newvoice')}")
    
    results = []
    
    # Синхронный тест
    results.append(("Sync connection", test_sync_connection()))
    
    # Асинхронный тест
    import asyncio
    results.append(("Async connection", asyncio.run(test_async_connection())))
    
    # Тест моделей
    results.append(("Models", test_models()))
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 Результаты:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("🎉 Все тесты пройдены!" if all_passed else "⚠️ Есть ошибки"))
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
