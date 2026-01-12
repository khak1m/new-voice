"""
Тест Ollama LLM провайдера.

Запуск:
    cd new-voice
    python scripts/test_ollama.py
    
    # Или с указанием хоста:
    python scripts/test_ollama.py http://77.233.212.58:11434
"""

import sys
sys.path.insert(0, 'src')

from providers.ollama_llm import OllamaLLMProvider


def main():
    # Хост из аргумента или localhost
    host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"
    
    print("=" * 50)
    print("Тест Ollama LLM Provider")
    print(f"Хост: {host}")
    print("=" * 50)
    
    # Создаём провайдер
    try:
        provider = OllamaLLMProvider(host=host)
        print("✅ Провайдер создан")
    except Exception as e:
        print(f"❌ Ошибка создания провайдера: {e}")
        return
    
    # Тест подключения
    print("\n1. Тест подключения...")
    if provider.test_connection():
        print("✅ Подключение работает!")
    else:
        print("❌ Не удалось подключиться к Ollama")
        print("\nУбедитесь что:")
        print("  1. Ollama установлен: curl -fsSL https://ollama.com/install.sh | sh")
        print("  2. Ollama запущен: ollama serve")
        print("  3. Порт открыт: 11434")
        return
    
    # Список моделей
    print("\n2. Установленные модели...")
    models = provider.list_models()
    if models:
        for m in models:
            print(f"   - {m}")
    else:
        print("   Нет установленных моделей!")
        print("   Скачайте модель: ollama pull qwen2:1.5b")
        return
    
    # Используем первую доступную модель
    model = models[0]
    provider.set_model(model)
    print(f"\n   Используем модель: {model}")
    
    # Тест генерации на русском
    print("\n3. Тест генерации (русский)...")
    response = provider.generate(
        system_prompt="""Ты администратор салона красоты "Бьюти".
Твоя задача — записать клиента на услугу.
Отвечай коротко и дружелюбно, максимум 2 предложения.""",
        messages=[
            {"role": "user", "content": "Привет, хочу записаться на маникюр"}
        ]
    )
    print(f"Бот: {response}")
    
    # Тест генерации на английском
    print("\n4. Тест генерации (английский)...")
    response = provider.generate(
        system_prompt="""You are a receptionist at "Beauty" salon.
Your task is to book appointments.
Be friendly and concise, max 2 sentences.""",
        messages=[
            {"role": "user", "content": "Hi, I want to book a manicure"}
        ]
    )
    print(f"Bot: {response}")
    
    # Тест диалога
    print("\n5. Тест диалога...")
    messages = []
    system = """Ты администратор салона красоты.
Собери информацию: имя, услуга, дата, время.
Отвечай коротко, максимум 1-2 предложения."""
    
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
            messages=messages,
            max_tokens=100
        )
        print(f"Бот: {response}")
        
        messages.append({"role": "assistant", "content": response})
    
    print("\n" + "=" * 50)
    print("✅ Все тесты пройдены!")
    print("=" * 50)


if __name__ == "__main__":
    main()
