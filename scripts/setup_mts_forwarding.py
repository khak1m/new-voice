#!/usr/bin/env python3
"""
Скрипт для настройки переадресации MTS Exolve на LiveKit через API.

Пробуем разные форматы SIP URI:
1. sip:+79346620875@sip.livekit.cloud:5060 (с номером и портом)
2. 55fzatq1dd8@sip.livekit.cloud (trunk ID)
3. sip:55fzatq1dd8@sip.livekit.cloud (с sip: префиксом)
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройки
MTS_API_KEY = os.getenv("MTS_EXOLVE_API_KEY")
PHONE_NUMBER = 79346620875  # +7 934 662-08-75

# Разные форматы SIP URI для тестирования
SIP_URI_FORMATS = {
    "1": "sip:+79346620875@sip.livekit.cloud:5060",  # С номером и портом
    "2": "55fzatq1dd8@sip.livekit.cloud",            # Trunk ID (текущий)
    "3": "sip:55fzatq1dd8@sip.livekit.cloud",        # С sip: префиксом
    "4": "sip:55fzatq1dd8@sip.livekit.cloud:5060",   # Trunk ID с портом
}

# API endpoint
API_URL = "https://api.exolve.ru/number/v1/SetCallForwarding"


def setup_call_forwarding(sip_uri: str):
    """Настроить переадресацию на указанный SIP URI."""
    
    if not MTS_API_KEY:
        print("❌ Ошибка: MTS_EXOLVE_API_KEY не найден в .env")
        return False
    
    api_key = MTS_API_KEY
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "number_code": PHONE_NUMBER,
        "call_forwarding_type": 1,
        "call_forwarding_sip": {
            "sip_uri": sip_uri
        }
    }
    
    print(f"📞 Номер: +{PHONE_NUMBER}")
    print(f"🎯 SIP URI: {sip_uri}")
    print(f"🔄 Отправка запроса...")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Переадресация настроена!")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def show_menu():
    """Показать меню выбора формата."""
    print("=" * 60)
    print("MTS Exolve → LiveKit: Выбор формата SIP URI")
    print("=" * 60)
    print()
    print("Выберите формат SIP URI для переадресации:")
    print()
    for key, uri in SIP_URI_FORMATS.items():
        print(f"  {key}. {uri}")
    print()
    print("  0. Выход")
    print()


if __name__ == "__main__":
    # Если передан аргумент - использовать его
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice in SIP_URI_FORMATS:
            setup_call_forwarding(SIP_URI_FORMATS[choice])
        else:
            print(f"❌ Неверный выбор: {choice}")
            print(f"Доступные: {list(SIP_URI_FORMATS.keys())}")
        sys.exit(0)
    
    # Интерактивный режим
    show_menu()
    
    choice = input("Ваш выбор (1-4): ").strip()
    
    if choice == "0":
        print("Выход")
        sys.exit(0)
    
    if choice not in SIP_URI_FORMATS:
        print(f"❌ Неверный выбор: {choice}")
        sys.exit(1)
    
    print()
    success = setup_call_forwarding(SIP_URI_FORMATS[choice])
    
    print()
    if success:
        print("🎉 Готово! Попробуй позвонить на +7 934 662-08-75")
    else:
        print("⚠️  Не удалось настроить")
