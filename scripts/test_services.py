"""
Тест подключения к внешним сервисам.

Проверяет:
- Deepgram (STT)
- Cartesia (TTS)
- LiveKit

Запуск:
    cd new-voice
    source venv/bin/activate
    python scripts/test_services.py
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


def test_env_vars():
    """Проверить что все переменные окружения установлены."""
    print("\n1. Проверка переменных окружения...")
    
    required = [
        "DEEPGRAM_API_KEY",
        "CARTESIA_API_KEY",
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
    ]
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            # Показываем только первые 10 символов
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var} = {masked}")
        else:
            print(f"   ❌ {var} не установлен")
            missing.append(var)
    
    return len(missing) == 0


async def test_deepgram():
    """Проверить подключение к Deepgram."""
    print("\n2. Тест Deepgram (STT)...")
    
    try:
        import httpx
        
        api_key = os.getenv("DEEPGRAM_API_KEY")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                print("   ✅ Deepgram подключен!")
                return True
            else:
                print(f"   ❌ Deepgram ошибка: {response.status_code}")
                print(f"      {response.text[:100]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Deepgram ошибка: {e}")
        return False


async def test_cartesia():
    """Проверить подключение к Cartesia."""
    print("\n3. Тест Cartesia (TTS)...")
    
    try:
        import httpx
        
        api_key = os.getenv("CARTESIA_API_KEY")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.cartesia.ai/voices",
                headers={
                    "X-API-Key": api_key,
                    "Cartesia-Version": "2024-11-13"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                voices = response.json()
                print(f"   ✅ Cartesia подключен! Доступно голосов: {len(voices)}")
                return True
            else:
                print(f"   ❌ Cartesia ошибка: {response.status_code}")
                print(f"      {response.text[:100]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Cartesia ошибка: {e}")
        return False


async def test_livekit():
    """Проверить подключение к LiveKit."""
    print("\n4. Тест LiveKit...")
    
    try:
        from livekit import api
        
        livekit_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        
        # Создаём клиент
        lk_api = api.LiveKitAPI(
            url=livekit_url.replace("wss://", "https://"),
            api_key=api_key,
            api_secret=api_secret,
        )
        
        # Пробуем получить список комнат
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
        
        print(f"   ✅ LiveKit подключен!")
        print(f"      URL: {livekit_url}")
        print(f"      Активных комнат: {len(rooms.rooms)}")
        
        await lk_api.aclose()
        return True
        
    except Exception as e:
        print(f"   ❌ LiveKit ошибка: {e}")
        return False


async def main():
    print("=" * 50)
    print("Тест подключения к сервисам")
    print("=" * 50)
    
    results = {}
    
    # Проверка переменных
    results["env"] = test_env_vars()
    
    if not results["env"]:
        print("\n❌ Установите недостающие переменные в .env файле")
        return
    
    # Тесты сервисов
    results["deepgram"] = await test_deepgram()
    results["cartesia"] = await test_cartesia()
    results["livekit"] = await test_livekit()
    
    # Итог
    print("\n" + "=" * 50)
    print("ИТОГ:")
    print("=" * 50)
    
    all_ok = all(results.values())
    
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"   {status} {name}")
    
    if all_ok:
        print("\n🎉 Все сервисы работают! Можно запускать Voice Agent.")
    else:
        print("\n⚠️ Некоторые сервисы недоступны. Проверьте API ключи.")


if __name__ == "__main__":
    asyncio.run(main())
