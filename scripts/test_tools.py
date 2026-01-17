#!/usr/bin/env python3
"""
Тестирование Function Calling Tools.

Этот скрипт:
1. Тестирует CalendarTool
2. Тестирует TransferTool
3. Тестирует ToolRegistry

Запуск:
    python scripts/test_tools.py
"""

import sys
import asyncio
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_calendar_tool():
    """Тест CalendarTool."""
    print("=" * 70)
    print("🧪 ТЕСТ 1: CalendarTool")
    print("=" * 70)
    
    try:
        from tools.calendar_tool import CalendarTool
        from tools.base import ToolStatus
        
        # Создаём tool с mock конфигурацией
        config = {
            "api_url": None,  # Mock mode
            "api_key": None
        }
        
        tool = CalendarTool(config)
        
        print(f"✅ Tool создан: {tool.name}")
        print(f"   Описание: {tool.description}")
        
        # Тест 1: Проверка доступности
        print("\n📅 Тест: check_availability")
        result = await tool.execute(
            action="check_availability",
            date="2026-01-20",
            time="14:00",
            duration_minutes=60
        )
        
        if result.success:
            print(f"✅ Доступность проверена")
            print(f"   Данные: {result.data}")
            print(f"   Сообщение: {result.message}")
        else:
            print(f"❌ Ошибка: {result.error}")
            return False
        
        # Тест 2: Бронирование
        print("\n📝 Тест: book_appointment")
        result = await tool.execute(
            action="book_appointment",
            date="2026-01-20",
            time="14:00",
            duration_minutes=60,
            service="Маникюр",
            client_name="Иван Иванов",
            client_phone="+79991234567"
        )
        
        if result.success:
            print(f"✅ Встреча забронирована")
            print(f"   Booking ID: {result.data.get('booking_id')}")
            print(f"   Статус: {result.data.get('status')}")
            print(f"   Сообщение: {result.message}")
        else:
            print(f"❌ Ошибка: {result.error}")
            return False
        
        # Тест 3: Function schema
        print("\n📋 Тест: function schema")
        schema = tool.to_function_schema()
        print(f"✅ Schema сгенерирована")
        print(f"   Name: {schema['name']}")
        print(f"   Parameters: {len(schema['parameters']['properties'])} полей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_transfer_tool():
    """Тест TransferTool."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 2: TransferTool")
    print("=" * 70)
    
    try:
        from tools.transfer_tool import TransferTool
        from tools.base import ToolStatus
        
        # Создаём tool с конфигурацией
        config = {
            "targets": {
                "operator": "sip:operator@example.com",
                "sales": "sip:sales@example.com",
                "support": "sip:support@example.com"
            }
        }
        
        tool = TransferTool(config)
        
        print(f"✅ Tool создан: {tool.name}")
        print(f"   Описание: {tool.description}")
        
        # Тест: Перевод на оператора
        print("\n📞 Тест: transfer_to_operator")
        result = await tool.execute(
            target="operator",
            reason="Customer wants to speak with human",
            priority="high"
        )
        
        if result.success:
            print(f"✅ Перевод инициирован")
            print(f"   Target: {result.data.get('target')}")
            print(f"   URI: {result.data.get('target_uri')}")
            print(f"   Priority: {result.data.get('priority')}")
            print(f"   Сообщение: {result.message}")
        else:
            print(f"❌ Ошибка: {result.error}")
            return False
        
        # Тест: Function schema
        print("\n📋 Тест: function schema")
        schema = tool.to_function_schema()
        print(f"✅ Schema сгенерирована")
        print(f"   Name: {schema['name']}")
        print(f"   Parameters: {len(schema['parameters']['properties'])} полей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_registry():
    """Тест ToolRegistry."""
    print("\n" + "=" * 70)
    print("🧪 ТЕСТ 3: ToolRegistry")
    print("=" * 70)
    
    try:
        from tools.base import get_registry
        
        registry = get_registry()
        
        # Проверяем что tools зарегистрированы
        tools = registry.list_tools()
        
        print(f"✅ Registry инициализирован")
        print(f"   Зарегистрировано tools: {len(tools)}")
        
        for tool_name in tools:
            print(f"   - {tool_name}")
        
        # Проверяем что можем получить tool
        if "calendar" in tools:
            tool = registry.get("calendar", {})
            if tool:
                print(f"✅ Tool 'calendar' получен из registry")
            else:
                print(f"❌ Не удалось получить tool 'calendar'")
                return False
        
        # Проверяем schemas
        print("\n📋 Тест: get_all_schemas")
        configs = [
            {"name": "calendar", "config": {}, "enabled": True},
            {"name": "transfer", "config": {"targets": {}}, "enabled": True}
        ]
        
        schemas = registry.get_all_schemas(configs)
        
        print(f"✅ Schemas получены: {len(schemas)}")
        for schema in schemas:
            print(f"   - {schema['name']}: {schema['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Основная функция тестирования."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ FUNCTION CALLING TOOLS")
    print("=" * 70)
    print()
    
    tests = [
        ("CalendarTool", test_calendar_tool),
        ("TransferTool", test_transfer_tool),
        ("ToolRegistry", lambda: test_tool_registry()),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            success = await test_func()
        else:
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
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Function Calling Tools готовы к использованию")
        return 0
    else:
        print("\n💥 ЕСТЬ ПРОБЛЕМЫ!")
        print("❌ Некоторые тесты провалены")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
