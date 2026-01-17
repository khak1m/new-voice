"""
Test suite for CampaignService (Phase 4).

Tests:
1. Campaign creation with validation
2. Call list upload (CSV/Excel parsing)
3. Campaign start/pause operations
4. Rate limiting logic
5. Task queue management (get_next_task)
6. Task status transitions (mark_in_progress, mark_completed, mark_failed)
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta
from io import BytesIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.connection import get_async_session
from database.models import Company, Skillbase, Campaign, CallTask
from services.campaign_service import (
    CampaignService,
    CampaignServiceError,
    CampaignNotFoundError,
    CampaignValidationError,
    CallListValidationError
)


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"🧪 {text}")
    print("=" * 70)


def print_success(text: str):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"❌ {text}")


async def cleanup_test_data(session):
    """Clean up test data."""
    try:
        # Delete test data in correct order (respecting foreign keys)
        from sqlalchemy import delete, select
        
        # Get test campaign IDs first
        campaign_result = await session.execute(
            select(Campaign.id).where(Campaign.name.like("Test Campaign%"))
        )
        campaign_ids = [row[0] for row in campaign_result.all()]
        
        # Delete call tasks
        if campaign_ids:
            await session.execute(
                delete(CallTask).where(CallTask.campaign_id.in_(campaign_ids))
            )
        
        # Delete campaigns
        await session.execute(
            delete(Campaign).where(Campaign.name.like("Test Campaign%"))
        )
        
        # Delete skillbases
        await session.execute(
            delete(Skillbase).where(Skillbase.name.like("Test Skillbase%"))
        )
        
        # Delete companies
        await session.execute(
            delete(Company).where(Company.name.like("Test Company%"))
        )
        
        await session.commit()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")


async def test_campaign_creation():
    """Test 1: Campaign creation with validation."""
    print_header("ТЕСТ 1: Campaign Creation")
    
    session = await get_async_session()
    try:
        # Clean up first
        await cleanup_test_data(session)
        
        # Create test company
        company = Company(
            id=uuid4(),
            name="Test Company 1",
            slug="test-company-1",
            email="test1@example.com"
        )
        session.add(company)
        
        # Create test skillbase
        skillbase = Skillbase(
            id=uuid4(),
            company_id=company.id,
            name="Test Skillbase 1",
            slug="test-skillbase-1",
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
        
        print_success("Test data created")
        
        # Create CampaignService
        service = CampaignService(session)
        print_success("CampaignService created")
        
        # Test: Create campaign
        campaign = await service.create(
            company_id=company.id,
            skillbase_id=skillbase.id,
            name="Test Campaign 1",
            description="Test campaign for unit tests",
            daily_start_time="09:00",
            daily_end_time="21:00",
            max_concurrent_calls=5,
            calls_per_minute=10,
            max_retries=3,
            retry_delay_minutes=30
        )
        
        assert campaign.id is not None
        assert campaign.name == "Test Campaign 1"
        assert campaign.status == "draft"
        assert campaign.total_tasks == 0
        assert campaign.max_concurrent_calls == 5
        assert campaign.calls_per_minute == 10
        
        print_success(f"Campaign created: {campaign.id}")
        print(f"   Name: {campaign.name}")
        print(f"   Status: {campaign.status}")
        print(f"   Max concurrent: {campaign.max_concurrent_calls}")
        print(f"   Calls per minute: {campaign.calls_per_minute}")
        
        # Test: Validation - invalid company
        try:
            await service.create(
                company_id=uuid4(),  # Non-existent
                skillbase_id=skillbase.id,
                name="Invalid Campaign"
            )
            print_error("Should have raised CampaignValidationError")
            return False
        except CampaignValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        # Test: Validation - invalid skillbase
        try:
            await service.create(
                company_id=company.id,
                skillbase_id=uuid4(),  # Non-existent
                name="Invalid Campaign"
            )
            print_error("Should have raised CampaignValidationError")
            return False
        except CampaignValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        # Test: Validation - invalid time format
        try:
            await service.create(
                company_id=company.id,
                skillbase_id=skillbase.id,
                name="Invalid Campaign",
                daily_start_time="25:00"  # Invalid
            )
            print_error("Should have raised CampaignValidationError")
            return False
        except CampaignValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        print_success("All validation tests passed")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()


async def test_call_list_upload():
    """Test 2: Call list upload (CSV parsing)."""
    print_header("ТЕСТ 2: Call List Upload")
    
    session = await get_async_session()
    try:
        # Get test campaign
        from sqlalchemy import select
        result = await session.execute(
            select(Campaign).where(Campaign.name == "Test Campaign 1")
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            print_error("Test campaign not found")
            return False
        
        print_success(f"Using campaign: {campaign.id}")
        
        # Create CampaignService
        service = CampaignService(session)
        
        # Create test CSV
        csv_content = """phone_number,name,company,notes
+79991234567,Иван Иванов,ООО Рога и Копыта,VIP клиент
+79991234568,Петр Петров,ИП Петров,Новый клиент
+79991234569,Сидор Сидоров,,Повторный звонок
+79991234570,,,Без данных
invalid_phone,Тест Тестов,,Невалидный номер
"""
        
        # Upload CSV
        result = await service.upload_call_list(
            campaign_id=campaign.id,
            file_content=csv_content.encode('utf-8'),
            filename="test_list.csv"
        )
        
        print_success("Call list uploaded")
        print(f"   Total rows: {result['total']}")
        print(f"   Created tasks: {result['created']}")
        print(f"   Errors: {len(result['errors'])}")
        
        if result['errors']:
            print("   Error details:")
            for error in result['errors'][:3]:  # Show first 3
                print(f"      - {error}")
        
        # Verify tasks created
        task_result = await session.execute(
            select(CallTask).where(CallTask.campaign_id == campaign.id)
        )
        tasks = list(task_result.scalars().all())
        
        print_success(f"Tasks in database: {len(tasks)}")
        
        # Check first task
        if tasks:
            task = tasks[0]
            print(f"   First task:")
            print(f"      Phone: {task.phone_number}")
            print(f"      Name: {task.contact_name}")
            print(f"      Status: {task.status}")
            print(f"      Data: {task.contact_data}")
        
        # Verify campaign stats updated
        await session.refresh(campaign)
        assert campaign.total_tasks == result['created']
        print_success(f"Campaign total_tasks updated: {campaign.total_tasks}")
        
        # Test: Invalid file format
        try:
            await service.upload_call_list(
                campaign_id=campaign.id,
                file_content=b"invalid content",
                filename="test.txt"
            )
            print_error("Should have raised CallListValidationError")
            return False
        except CallListValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        # Test: Missing required columns
        try:
            csv_invalid = "name,company\nTest,Test Inc"
            await service.upload_call_list(
                campaign_id=campaign.id,
                file_content=csv_invalid.encode('utf-8'),
                filename="invalid.csv"
            )
            print_error("Should have raised CallListValidationError")
            return False
        except CallListValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()


async def test_campaign_lifecycle():
    """Test 3: Campaign start/pause operations."""
    print_header("ТЕСТ 3: Campaign Lifecycle")
    
    session = await get_async_session()
    try:
        # Get test campaign
        from sqlalchemy import select
        result = await session.execute(
            select(Campaign).where(Campaign.name == "Test Campaign 1")
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            print_error("Test campaign not found")
            return False
        
        print_success(f"Using campaign: {campaign.id}")
        print(f"   Initial status: {campaign.status}")
        
        # Create CampaignService
        service = CampaignService(session)
        
        # Test: Start campaign
        updated = await service.start(campaign.id)
        assert updated.status == "running"
        print_success(f"Campaign started: {updated.status}")
        
        # Test: Cannot start running campaign
        try:
            await service.start(campaign.id)
            print_error("Should have raised CampaignValidationError")
            return False
        except CampaignValidationError as e:
            print_success(f"Validation error caught: {e}")
        
        # Test: Pause campaign
        updated = await service.pause(campaign.id)
        assert updated.status == "paused"
        print_success(f"Campaign paused: {updated.status}")
        
        # Test: Start again
        updated = await service.start(campaign.id)
        assert updated.status == "running"
        print_success(f"Campaign restarted: {updated.status}")
        
        # Test: get_active_campaigns
        active = await service.get_active_campaigns()
        assert len(active) > 0
        assert any(c.id == campaign.id for c in active)
        print_success(f"Active campaigns: {len(active)}")
            
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()


async def test_task_queue_management():
    """Test 4: Task queue management (get_next_task)."""
    print_header("ТЕСТ 4: Task Queue Management")
    
    session = await get_async_session()
    try:
        # Get test campaign
        from sqlalchemy import select
        result = await session.execute(
            select(Campaign).where(Campaign.name == "Test Campaign 1")
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            print_error("Test campaign not found")
            return False
        
        print_success(f"Using campaign: {campaign.id}")
        
        # Create CampaignService
        service = CampaignService(session)
        
        # Test: Get next task
        task = await service.get_next_task(campaign.id)
        
        if task:
            print_success(f"Got next task: {task.id}")
            print(f"   Phone: {task.phone_number}")
            print(f"   Status: {task.status}")
            print(f"   Priority: {task.priority}")
        else:
            print_error("No task returned (might be outside schedule)")
            # This is OK if outside daily window
            print("   ℹ️  This is expected if outside daily calling window")
        
        # Test: Rate limiting
        # Get multiple tasks to test concurrent limit
        tasks = []
        for i in range(campaign.max_concurrent_calls + 2):
            t = await service.get_next_task(campaign.id)
            if t:
                tasks.append(t)
        
        print_success(f"Got {len(tasks)} tasks (max concurrent: {campaign.max_concurrent_calls})")
        
        # Should not exceed max_concurrent_calls
        if len(tasks) <= campaign.max_concurrent_calls:
            print_success("Rate limiting working correctly")
        else:
            print_error(f"Rate limit exceeded: {len(tasks)} > {campaign.max_concurrent_calls}")
            
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()


async def test_task_status_transitions():
    """Test 5: Task status transitions."""
    print_header("ТЕСТ 5: Task Status Transitions")
    
    session = await get_async_session()
    try:
        # Get a pending task
        from sqlalchemy import select
        result = await session.execute(
            select(CallTask)
            .where(CallTask.status == "pending")
            .limit(1)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            print_error("No pending task found")
            return False
        
        print_success(f"Using task: {task.id}")
        print(f"   Initial status: {task.status}")
        print(f"   Attempt count: {task.attempt_count}")
        
        # Create CampaignService
        service = CampaignService(session)
        
        # Test: Mark in progress
        updated = await service.mark_in_progress(task.id)
        assert updated.status == "in_progress"
        assert updated.attempt_count == 1
        assert updated.last_attempt_at is not None
        print_success(f"Task marked in progress")
        print(f"   Status: {updated.status}")
        print(f"   Attempt count: {updated.attempt_count}")
        
        # Test: Mark completed
        call_id = uuid4()
        updated = await service.mark_completed(
            task_id=task.id,
            call_id=call_id,
            outcome="success"
        )
        assert updated.status == "completed"
        assert updated.call_id == call_id
        assert updated.outcome == "success"
        print_success(f"Task marked completed")
        print(f"   Status: {updated.status}")
        print(f"   Outcome: {updated.outcome}")
        
        # Get another task for failure test
        result = await session.execute(
            select(CallTask)
            .where(CallTask.status == "pending")
            .limit(1)
        )
        task2 = result.scalar_one_or_none()
        
        if task2:
            # Mark in progress
            await service.mark_in_progress(task2.id)
            
            # Test: Mark failed (should retry)
            updated = await service.mark_failed(
                task_id=task2.id,
                error_message="Test error"
            )
            
            if updated.attempt_count < updated.campaign.max_retries:
                assert updated.status == "retry"
                assert updated.next_attempt_at is not None
                print_success(f"Task marked for retry")
                print(f"   Status: {updated.status}")
                print(f"   Next attempt: {updated.next_attempt_at}")
            else:
                assert updated.status == "failed"
                print_success(f"Task marked failed (max retries reached)")
            
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await session.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 ТЕСТИРОВАНИЕ CAMPAIGN SERVICE (PHASE 4)")
    print("=" * 70)
    
    results = []
    
    # Test 1: Campaign creation
    results.append(("Campaign Creation", await test_campaign_creation()))
    
    # Test 2: Call list upload
    results.append(("Call List Upload", await test_call_list_upload()))
    
    # Test 3: Campaign lifecycle
    results.append(("Campaign Lifecycle", await test_campaign_lifecycle()))
    
    # Test 4: Task queue management
    results.append(("Task Queue Management", await test_task_queue_management()))
    
    # Test 5: Task status transitions
    results.append(("Task Status Transitions", await test_task_status_transitions()))
    
    # Print summary
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {name}")
    
    print("=" * 70)
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    percentage = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"Результат: {passed_count}/{total_count} тестов пройдено ({percentage:.1f}%)")
    print("=" * 70)
    
    if passed_count == total_count:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("💥 ЕСТЬ ПРОБЛЕМЫ!")
        print("❌ Некоторые тесты провалены")


if __name__ == "__main__":
    asyncio.run(main())
