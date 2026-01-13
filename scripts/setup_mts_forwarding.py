#!/usr/bin/env python3
"""
Скрипт для настройки переадресации MTS Exolve на LiveKit через API.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Настройки
MTS_API_KEY = os.getenv("MTS_EXOLVE_API_KEY")  # Нужно добавить в .env
PHONE_NUMBER = 79346620875  # +7 934 662-08-75
LIVEKIT_SIP_URI = "55fzatq1dd8@sip.livekit.cloud"

# API endpoint
API_URL = "https://api.exolve.ru/number/v1/SetCallForwarding"

def setup_call_forwarding():
    """Настроить переадресацию на LiveKit SIP."""
    
    if not MTS_API_KEY:
        print("❌ Ошибка: MTS_EXOLVE_API_KEY не найден в .env")
        print("Добавьте в .env файл:")
        print("MTS_EXOLVE_API_KEY=ваш_api_ключ")
        return False
    
    headers = {
        "Authorization": f"Bearer {MTS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Данные для переадресации на внешний SIP
    payload = {
        "number_code": PHONE_NUMBER,
        "call_forwarding_type": 1,  # Переадресация на внешний SIP
        "call_forwarding_sip": {
            "sip_uri": LIVEKIT_SIP_URI
        }
    }
    
    print(f"📞 Настройка переадресации для номера +{PHONE_NUMBER}")
    print(f"🎯 Переадресация на: {LIVEKIT_SIP_URI}")
    print(f"🔄 Отправка запроса к MTS Exolve API...")
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Переадресация успешно настроена!")
            print(f"Ответ: {response.json()}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при выполнении запроса: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MTS Exolve → LiveKit Call Forwarding Setup")
    print("=" * 60)
    print()
    
    success = setup_call_forwarding()
    
    print()
    if success:
        print("🎉 Готово! Теперь можно звонить на +7 934 662-08-75")
        print("Звонок будет переадресован на LiveKit → Voice Agent")
    else:
        print("⚠️  Не удалось настроить переадресацию")
        print("Проверьте API ключ и попробуйте снова")
