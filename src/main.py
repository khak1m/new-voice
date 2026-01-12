"""
NEW-VOICE 2.0 - Main Entry Point
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()


async def main():
    print("=" * 50)
    print("NEW-VOICE 2.0 - Voice AI Platform")
    print("=" * 50)
    print()
    print("Статус: В разработке")
    print()
    print("Следующие шаги:")
    print("1. Заполни .env файл с API ключами")
    print("2. Запусти docker-compose up -d")
    print("3. Протестируй каждый сервис отдельно")
    print()


if __name__ == "__main__":
    asyncio.run(main())
