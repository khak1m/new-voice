#!/usr/bin/env python3
"""
Скрипт для проверки и настройки SIP в LiveKit.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_sip_config():
    """Проверить текущую конфигурацию SIP."""
    
    try:
        from livekit import api
    except ImportError:
        print("❌ livekit-api не установлен")
        print("Установи: pip install livekit-api")
        return
    
    lk = api.LiveKitAPI()
    
    print("=" * 60)
    print("LiveKit SIP Configuration Check")
    print("=" * 60)
    
    # 1. Проверяем Inbound Trunks
    print("\n📥 INBOUND TRUNKS:")
    print("-" * 40)
    try:
        inbound_trunks = await lk.sip.list_sip_inbound_trunk(
            api.ListSIPInboundTrunkRequest()
        )
        if inbound_trunks.items:
            for trunk in inbound_trunks.items:
                print(f"  ID: {trunk.sip_trunk_id}")
                print(f"  Name: {trunk.name}")
                print(f"  Numbers: {trunk.numbers}")
                print(f"  Allowed Addresses: {trunk.allowed_addresses}")
                print()
        else:
            print("  Нет inbound trunks")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # 2. Проверяем Outbound Trunks
    print("\n📤 OUTBOUND TRUNKS:")
    print("-" * 40)
    try:
        outbound_trunks = await lk.sip.list_sip_outbound_trunk(
            api.ListSIPOutboundTrunkRequest()
        )
        if outbound_trunks.items:
            for trunk in outbound_trunks.items:
                print(f"  ID: {trunk.sip_trunk_id}")
                print(f"  Name: {trunk.name}")
                print(f"  Address: {trunk.address}")
                print(f"  Numbers: {trunk.numbers}")
                print()
        else:
            print("  Нет outbound trunks")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    # 3. Проверяем Dispatch Rules
    print("\n📋 DISPATCH RULES:")
    print("-" * 40)
    try:
        dispatch_rules = await lk.sip.list_sip_dispatch_rule(
            api.ListSIPDispatchRuleRequest()
        )
        if dispatch_rules.items:
            for rule in dispatch_rules.items:
                print(f"  ID: {rule.sip_dispatch_rule_id}")
                print(f"  Name: {rule.name}")
                print(f"  Trunk IDs: {rule.trunk_ids}")
                print(f"  Rule: {rule.rule}")
                print()
        else:
            print("  Нет dispatch rules")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    await lk.aclose()
    
    print("=" * 60)
    print("Проверка завершена")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_sip_config())
