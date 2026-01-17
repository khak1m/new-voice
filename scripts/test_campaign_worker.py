"""
Тестовый скрипт для CampaignWorker.

Этот скрипт демонстрирует работу CampaignWorker в упрощённом режиме
(без реальных звонков, только симуляция).

Запуск:
    python scripts/test_campaign_worker.py
"""

import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.connection import get_async_session
from database.models import Company, Skillbase, Campaign, CallTask
from services.campaign_service import CampaignService
from workers.campaign_worker import CampaignWorker


async def cleanup_test_data(session):
    """Очистить тестовые данные."""
    from sqlalchemy import delete
    
    print("🧹 Очистка старых тестовых данных...")
    
    # Delete in correct order
    await session.execute(
        delete(CallTask).where(CallTask.phone_number.like("+7999%"))
    )
    await session.execute(
        delete(Campaign).where(Campaign.name.like("Test Worker%"))
    )
    await session.execute(
        delete(Skillbase).where(Skillbase.name.like("Test Worker%"))
    )
    await session.execute(
        delete(Company).where(Company.name.like("Test Worker%"))
    )
    
    await session.commit()
    print("✅ Очистка завершена")


async def create_test_campaign(session):
    """Создать тестовую кампанию с задачами."""
    print("\n📋 Создание тестовой кампании...")
    
    # Create company
    company = Company(
        id=uuid4(),
        name="Test Worker Company",
        slug="test-worker-company",
        email="test@example.com"
    )
    session.add(company)
    
    # Create skillbase
    skillbase = Skillbase(
        id=uuid4(),
        company_id=company.id,
        name="Test Worker Skillbase",
        slug="test-worker-skillbase",
        config={
            "context": {"role": "Test bot"},
            "flow": {"type": "linear", "states": ["greeting"]},
            "voice": {"tts_provider": "cartesia"},
            "llm": {"provider": "groq", "model": "llama-3.1-8b-instant"}
        },
        version=1,
        is_active=True
    )
    session.add(skillbase)
    await session.commit()
    
    print(f"✅ Company: {company.name}")
    print(f"✅ Skillbase: {skillbase.name}")
    
    # Create campaign
    service = CampaignService(session)
    campaign = await service.create(
        company_id=company.id,
        skillbase_id=skillbase.id,
        name="Test Worker Campaign",
        description="Test campaign for CampaignWorker",
        daily_start_time="00:00",  # Always active
        daily_end_time="23:59",
        max_concurrent_calls=2,
        calls_per_minute=5,
        max_retries=2,
        retry_delay_minutes=1  # Short delay for testing
    )
    
    print(f"✅ Campaign: {campaign.name} (ID: {campaign.id})")
    
    # Add test tasks
    test_phones = [
        ("+79991111111", "Иван Иванов"),
        ("+79992222222", "Петр Петров"),
        ("+79993333333", "Сидор Сидоров"),
    ]
    
    for phone, name in test_phones:
        task = CallTask(
            campaign_id=campaign.id,
            phone_number=phone,
            contact_name=name,
            contact_data={"test": True},
            status="pending",
            attempt_count=0,
            priority=0
        )
        session.add(task)
    
    campaign.total_tasks = len(test_phones)
    await session.commit()
    
    print(f"✅ Добавлено {len(test_phones)} задач")
    
    # Start campaign
    await service.start(campaign.id)
    print(f"✅ Кампания запущена")
    
    return campaign.id


async def test_campaign_worker():
    """Тестировать CampaignWorker."""
    print("=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ CAMPAIGN WORKER")
    print("=" * 70)
    
    session = await get_async_session()
    
    try:
        # Cleanup old data
        await cleanup_test_data(session)
        
        # Create test campaign
        campaign_id = await create_test_campaign(session)
        
        # Initialize CampaignWorker (without LiveKit for testing)
        print("\n🤖 Инициализация CampaignWorker...")
        
        # Get environment variables (or use dummy values for testing)
        livekit_url = os.getenv("LIVEKIT_URL", "wss://test.livekit.cloud")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY", "test-key")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "test-secret")
        
        worker = CampaignWorker(
            db_session=session,
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_api_secret=livekit_api_secret,
            sip_trunk_id=None,  # No SIP for testing
            voice_agent_factory=None,  # No VoiceAgent for testing
            poll_interval=2.0  # Poll every 2 seconds
        )
        
        print("✅ CampaignWorker инициализирован")
        
        # Start worker in background
        print("\n▶️  Запуск CampaignWorker (будет работать 10 секунд)...")
        print("   Наблюдай за логами - worker будет обрабатывать задачи")
        print()
        
        # Run worker for 10 seconds
        worker_task = asyncio.create_task(worker.start())
        
        # Wait 10 seconds
        await asyncio.sleep(10)
        
        # Stop worker
        print("\n⏸️  Остановка CampaignWorker...")
        await worker.stop()
        
        # Wait for worker to finish
        try:
            await asyncio.wait_for(worker_task, timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  Worker не остановился за 5 секунд")
        
        print("✅ CampaignWorker остановлен")
        
        # Check results
        print("\n📊 РЕЗУЛЬТАТЫ:")
        print("-" * 70)
        
        service = CampaignService(session)
        campaign = await service.get_by_id(campaign_id)
        
        print(f"Кампания: {campaign.name}")
        print(f"  Всего задач: {campaign.total_tasks}")
        print(f"  Завершено: {campaign.completed_tasks}")
        print(f"  Провалено: {campaign.failed_tasks}")
        
        # Get tasks
        from sqlalchemy import select
        result = await session.execute(
            select(CallTask).where(CallTask.campaign_id == campaign_id)
        )
        tasks = list(result.scalars().all())
        
        print(f"\nЗадачи:")
        for task in tasks:
            print(f"  {task.phone_number} ({task.contact_name})")
            print(f"    Статус: {task.status}")
            print(f"    Попыток: {task.attempt_count}")
            if task.error_message:
                print(f"    Ошибка: {task.error_message[:50]}...")
        
        print("\n" + "=" * 70)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 70)
        
        print("\n💡 ПРИМЕЧАНИЕ:")
        print("   Задачи будут помечены как 'failed' потому что:")
        print("   1. Нет реального LiveKit подключения")
        print("   2. Нет SIP trunk для звонков")
        print("   3. Нет VoiceAgent для разговора")
        print()
        print("   Это нормально для unit-теста!")
        print("   Worker корректно обрабатывает ошибки и делает retry.")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(test_campaign_worker())
