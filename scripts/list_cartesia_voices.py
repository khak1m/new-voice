"""
Скрипт для получения списка голосов Cartesia.
Запуск: python scripts/list_cartesia_voices.py
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CARTESIA_API_KEY")

def list_voices():
    """Получить список всех голосов Cartesia."""
    
    headers = {
        "X-API-Key": API_KEY,
        "Cartesia-Version": "2024-06-10",
    }
    
    response = httpx.get(
        "https://api.cartesia.ai/voices",
        headers=headers,
    )
    
    if response.status_code != 200:
        print(f"Ошибка: {response.status_code}")
        print(response.text)
        return
    
    voices = response.json()
    
    print("=" * 60)
    print("ГОЛОСА CARTESIA")
    print("=" * 60)
    
    # Фильтруем голоса с поддержкой русского
    russian_voices = []
    multilingual_voices = []
    
    for voice in voices:
        name = voice.get("name", "Unknown")
        voice_id = voice.get("id", "")
        language = voice.get("language", "")
        description = voice.get("description", "")[:50]
        
        # Проверяем поддержку русского
        if "ru" in language.lower() or "russian" in language.lower():
            russian_voices.append(voice)
        elif "multilingual" in language.lower() or "multi" in str(voice).lower():
            multilingual_voices.append(voice)
    
    print("\n🇷🇺 РУССКИЕ ГОЛОСА:")
    print("-" * 60)
    for v in russian_voices:
        print(f"  Имя: {v.get('name')}")
        print(f"  ID: {v.get('id')}")
        print(f"  Язык: {v.get('language')}")
        print(f"  Описание: {v.get('description', '')[:80]}")
        print()
    
    print("\n🌍 МУЛЬТИЯЗЫЧНЫЕ ГОЛОСА:")
    print("-" * 60)
    for v in multilingual_voices[:10]:  # Первые 10
        print(f"  Имя: {v.get('name')}")
        print(f"  ID: {v.get('id')}")
        print(f"  Язык: {v.get('language')}")
        print()
    
    print("\n📋 ВСЕ ГОЛОСА (первые 20):")
    print("-" * 60)
    for v in voices[:20]:
        print(f"  {v.get('name'):30} | {v.get('id')[:20]}... | {v.get('language', 'N/A')}")
    
    print(f"\nВсего голосов: {len(voices)}")


if __name__ == "__main__":
    list_voices()
