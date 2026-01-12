"""
Тест Groq LLM провайдера.

Запуск:
    cd new-voice
    python scripts/test_groq.py YOUR_API_KEY
    
    или с переменной окружения:
    set GROQ_API_KEY=gsk_xxx
    python scripts/test_groq.py
"""

import sys
import os
sys.path.insert(0, 'src')

from providers.groq_llm import GroqLLMProvider


def main():
    # API ключ из переменной окружения или аргумента
    API_KEY = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GROQ_API_KEY")
    
    if not API_KEY:
        print("❌ API ключ не указан!")
        print("Использование:")
        print("  python scripts/test_groq.py YOUR_API_KEY")
        print("  или установите GROQ_API_KEY в переменных окружения")
        return
    
    print("=" * 50)
    print("Тест Groq LLM Provider")
    print("=" * 50)
    
    # Создаём провайдер
    try:
        provider = GroqLLMProvider(api_key=API_KEY)
        print("✅ Провайдер создан")
    except Exception as e:
        print(f"❌ Ошибка создания провайдера: {e}")
        return
    
    # Тест подключения
    print("\n1. Тест подключения...")
    if provider.test_connection():
        print("✅ Подключение работает!")
    else:
        print("❌ Ошибка подключения")
        print("\nВозможные причины:")
        print("  1. API ключ неактивен или истёк")
        print("  2. Нужно создать новый ключ на https://console.groq.com/keys")
        print("  3. Проверь что ключ начинается с 'gsk_'")
        return
    
    # Тест генерации на русском
    print("\n2. Тест генерации (русский)...")
    response = provider.generate(
        system_prompt="""Ты администратор салона красоты "Бьюти".
Твоя задача — записать клиента на услугу.
Отвечай коротко и дружелюбно.""",
        messages=[
            {"role": "user", "content": "Привет, хочу записаться на маникюр"}
        ]
    )
    print(f"Бот: {response}")
    
    # Тест генерации на английском
    print("\n3. Тест генерации (английский)...")
    response = provider.generate(
        system_prompt="""You are a receptionist at "Beauty" salon.
Your task is to book appointments.
Be friendly and concise.""",
        messages=[
            {"role": "user", "content": "Hi, I want to book a manicure"}
        ]
    )
    print(f"Bot: {response}")
    
    # Тест диалога
    print("\n4. Тест диалога...")
    messages = []
    system = """Ты администратор салона красоты.
Собери информацию: имя, услуга, дата, время.
Отвечай коротко."""
    
    # Симуляция диалога
    user_messages = [
        "Здравствуйте, хочу записаться",
        "Меня зовут Анна",
        "На маникюр",
        "Завтра в 14:00"
    ]
    
    for user_msg in user_messages:
        messages.append({"role": "user", "content": user_msg})
        print(f"\nКлиент: {user_msg}")
        
        response = provider.generate(
            system_prompt=system,
            messages=messages
        )
        print(f"Бот: {response}")
        
        messages.append({"role": "assistant", "content": response})
    
    print("\n" + "=" * 50)
    print("✅ Все тесты пройдены!")
    print("=" * 50)


if __name__ == "__main__":
    main()
