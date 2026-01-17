"""
CampaignService - Manages outbound calling campaigns.

This service:
1. Creates and manages campaigns
2. Uploads call lists (CSV/Excel)
3. Manages campaign lifecycle (start, pause, stop)
4. Provides next task with rate limiting
5. Tracks campaign statistics
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from database.models import Campaign, CallTask, Skillbase, Company

logger = logging.getLogger(__name__)


class CampaignServiceError(Exception):
    """Base exception for CampaignService errors."""
    pass


class CampaignNotFoundError(CampaignServiceError):
    """Campaign not found."""
    pass


class CampaignValidationError(CampaignServiceError):
    """Campaign validation failed."""
    pass


class CallListValidationError(CampaignServiceError):
    """Call list validation failed."""
    pass


class CampaignService:
    """
    Manages outbound calling campaigns.
    
    Handles campaign lifecycle, call list uploads, and task queue management
    with rate limiting and scheduling.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize CampaignService.
        
        Args:
            db_session: Async database session
        """
        self.db_session = db_session
        self._rate_limit_cache: Dict[UUID, Dict[str, Any]] = {}
        self._cache_lock = asyncio.Lock()
        logger.info("CampaignService initialized")
    
    async def create(
        self,
        company_id: UUID,
        skillbase_id: UUID,
        name: str,
        description: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        daily_start_time: str = "09:00",
        daily_end_time: str = "21:00",
        timezone: str = "Europe/Moscow",
        max_concurrent_calls: int = 5,
        calls_per_minute: int = 10,
        max_retries: int = 3,
        retry_delay_minutes: int = 30
    ) -> Campaign:
        """
        Create a new campaign.
        
        Args:
            company_id: Company ID
            skillbase_id: Skillbase ID to use for calls
            name: Campaign name
            description: Optional description
            start_time: Campaign start time (None = immediate)
            end_time: Campaign end time (None = no end)
            daily_start_time: Daily calling window start (HH:MM)
            daily_end_time: Daily calling window end (HH:MM)
            timezone: Timezone for scheduling
            max_concurrent_calls: Max concurrent calls
            calls_per_minute: Rate limit (calls per minute)
            max_retries: Max retry attempts per task
            retry_delay_minutes: Delay between retries
        
        Returns:
            Created Campaign object
        
        Raises:
            CampaignValidationError: If validation fails
        """
        try:
            # Validate company exists
            company_result = await self.db_session.execute(
                select(Company).where(Company.id == company_id)
            )
            company = company_result.scalar_one_or_none()
            if not company:
                raise CampaignValidationError(f"Company {company_id} not found")
            
            # Validate skillbase exists and belongs to company
            skillbase_result = await self.db_session.execute(
                select(Skillbase).where(
                    and_(
                        Skillbase.id == skillbase_id,
                        Skillbase.company_id == company_id
                    )
                )
            )
            skillbase = skillbase_result.scalar_one_or_none()
            if not skillbase:
                raise CampaignValidationError(
                    f"Skillbase {skillbase_id} not found or doesn't belong to company"
                )
            
            # Validate time format
            try:
                datetime.strptime(daily_start_time, "%H:%M")
                datetime.strptime(daily_end_time, "%H:%M")
            except ValueError as e:
                raise CampaignValidationError(f"Invalid time format: {e}")
            
            # Create campaign
            campaign = Campaign(
                company_id=company_id,
                skillbase_id=skillbase_id,
                name=name,
                description=description,
                status="draft",
                start_time=start_time,
                end_time=end_time,
                daily_start_time=daily_start_time,
                daily_end_time=daily_end_time,
                timezone=timezone,
                max_concurrent_calls=max_concurrent_calls,
                calls_per_minute=calls_per_minute,
                max_retries=max_retries,
                retry_delay_minutes=retry_delay_minutes,
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0
            )
            
            self.db_session.add(campaign)
            await self.db_session.commit()
            await self.db_session.refresh(campaign)
            
            logger.info(
                f"Created campaign {campaign.id}",
                extra={
                    "campaign_id": str(campaign.id),
                    "company_id": str(company_id),
                    "skillbase_id": str(skillbase_id),
                    "name": name
                }
            )
            
            return campaign
            
        except CampaignValidationError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to create campaign: {e}",
                extra={"company_id": str(company_id)},
                exc_info=True
            )
            raise CampaignServiceError(f"Failed to create campaign: {e}")
    
    async def upload_call_list(
        self,
        campaign_id: UUID,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Upload and parse call list from CSV or Excel file.
        
        Args:
            campaign_id: Campaign ID
            file_content: File content as bytes
            filename: Original filename
        
        Returns:
            Dictionary with upload results:
            {
                "total": int,
                "created": int,
                "errors": List[str]
            }
        
        Raises:
            CampaignNotFoundError: If campaign not found
            CallListValidationError: If file validation fails
        """
        try:
            # Get campaign
            campaign = await self.get_by_id(campaign_id)
            if not campaign:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
            
            # Parse file
            file_io = BytesIO(file_content)
            
            if filename.endswith('.csv'):
                df = pd.read_csv(file_io)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_io)
            else:
                raise CallListValidationError(
                    "Unsupported file format. Use CSV or Excel (.xlsx, .xls)"
                )
            
            # Validate required columns
            required_columns = ['phone_number']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise CallListValidationError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            # Process rows
            created_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    phone_number = str(row['phone_number']).strip()
                    
                    # Basic phone validation
                    if not phone_number or phone_number == 'nan':
                        errors.append(f"Row {idx + 2}: Empty phone number")
                        continue
                    
                    # Extract optional fields
                    contact_name = row.get('name', row.get('contact_name', None))
                    if contact_name and str(contact_name) != 'nan':
                        contact_name = str(contact_name).strip()
                    else:
                        contact_name = None
                    
                    # Extract additional data
                    contact_data = {}
                    for col in df.columns:
                        if col not in ['phone_number', 'name', 'contact_name']:
                            value = row[col]
                            if pd.notna(value):
                                contact_data[col] = str(value)
                    
                    # Create CallTask
                    call_task = CallTask(
                        campaign_id=campaign_id,
                        phone_number=phone_number,
                        contact_name=contact_name,
                        contact_data=contact_data,
                        status="pending",
                        attempt_count=0,
                        priority=0
                    )
                    
                    self.db_session.add(call_task)
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {idx + 2}: {str(e)}")
            
            # Update campaign stats
            campaign.total_tasks += created_count
            
            await self.db_session.commit()
            
            logger.info(
                f"Uploaded call list for campaign {campaign_id}",
                extra={
                    "campaign_id": str(campaign_id),
                    "total_rows": len(df),
                    "created": created_count,
                    "errors": len(errors)
                }
            )
            
            return {
                "total": len(df),
                "created": created_count,
                "errors": errors
            }
            
        except (CampaignNotFoundError, CallListValidationError):
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to upload call list: {e}",
                extra={"campaign_id": str(campaign_id)},
                exc_info=True
            )
            raise CampaignServiceError(f"Failed to upload call list: {e}")
    
    async def start(self, campaign_id: UUID) -> Campaign:
        """
        Start campaign processing.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Updated Campaign object
        
        Raises:
            CampaignNotFoundError: If campaign not found
            CampaignValidationError: If campaign cannot be started
        """
        try:
            campaign = await self.get_by_id(campaign_id)
            if not campaign:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
            
            # Validate campaign can be started
            if campaign.status == "running":
                raise CampaignValidationError("Campaign is already running")
            
            if campaign.total_tasks == 0:
                raise CampaignValidationError("Campaign has no tasks")
            
            # Update status
            campaign.status = "running"
            
            await self.db_session.commit()
            await self.db_session.refresh(campaign)
            
            logger.info(
                f"Started campaign {campaign_id}",
                extra={"campaign_id": str(campaign_id)}
            )
            
            return campaign
            
        except (CampaignNotFoundError, CampaignValidationError):
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to start campaign: {e}",
                extra={"campaign_id": str(campaign_id)},
                exc_info=True
            )
            raise CampaignServiceError(f"Failed to start campaign: {e}")
    
    async def pause(self, campaign_id: UUID) -> Campaign:
        """
        Pause campaign processing.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Updated Campaign object
        
        Raises:
            CampaignNotFoundError: If campaign not found
        """
        try:
            campaign = await self.get_by_id(campaign_id)
            if not campaign:
                raise CampaignNotFoundError(f"Campaign {campaign_id} not found")
            
            campaign.status = "paused"
            
            await self.db_session.commit()
            await self.db_session.refresh(campaign)
            
            logger.info(
                f"Paused campaign {campaign_id}",
                extra={"campaign_id": str(campaign_id)}
            )
            
            return campaign
            
        except CampaignNotFoundError:
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(
                f"Failed to pause campaign: {e}",
                extra={"campaign_id": str(campaign_id)},
                exc_info=True
            )
            raise CampaignServiceError(f"Failed to pause campaign: {e}")
    
    async def get_by_id(
        self,
        campaign_id: UUID,
        eager_load: bool = False
    ) -> Optional[Campaign]:
        """
        Get campaign by ID.
        
        Args:
            campaign_id: Campaign ID
            eager_load: Whether to eager load relationships
        
        Returns:
            Campaign object or None
        """
        try:
            query = select(Campaign).where(Campaign.id == campaign_id)
            
            if eager_load:
                query = query.options(
                    selectinload(Campaign.skillbase),
                    selectinload(Campaign.company)
                )
            
            result = await self.db_session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(
                f"Failed to get campaign: {e}",
                extra={"campaign_id": str(campaign_id)},
                exc_info=True
            )
            return None
    
    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all active (running) campaigns.
        
        Returns:
            List of Campaign objects
        """
        try:
            result = await self.db_session.execute(
                select(Campaign)
                .where(Campaign.status == "running")
                .options(selectinload(Campaign.skillbase))
            )
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(
                f"Failed to get active campaigns: {e}",
                exc_info=True
            )
            return []
    
    async def get_next_task(
        self,
        campaign_id: UUID
    ) -> Optional[CallTask]:
        """
        Get next pending task respecting rate limits and scheduling.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            CallTask object or None if no tasks available
        """
        try:
            campaign = await self.get_by_id(campaign_id)
            if not campaign:
                return None
            
            # Check if within scheduling window
            if not await self._is_within_schedule(campaign):
                return None
            
            # Check rate limits
            if not await self._check_rate_limits(campaign):
                return None
            
            # Get next pending or retry task
            now = datetime.utcnow()
            
            result = await self.db_session.execute(
                select(CallTask)
                .where(
                    and_(
                        CallTask.campaign_id == campaign_id,
                        or_(
                            CallTask.status == "pending",
                            and_(
                                CallTask.status == "retry",
                                CallTask.next_attempt_at <= now
                            )
                        )
                    )
                )
                .order_by(CallTask.priority.desc(), CallTask.created_at)
                .limit(1)
            )
            
            task = result.scalar_one_or_none()
            
            if task:
                # Update rate limit cache
                await self._update_rate_limit_cache(campaign_id)
            
            return task
            
        except Exception as e:
            logger.error(
                f"Failed to get next task: {e}",
                extra={"campaign_id": str(campaign_id)},
                exc_info=True
            )
            return None
    
    async def _is_within_schedule(self, campaign: Campaign) -> bool:
        """Check if current time is within campaign schedule."""
        now = datetime.utcnow()
        
        # Check campaign start/end time
        if campaign.start_time and now < campaign.start_time:
            return False
        
        if campaign.end_time and now > campaign.end_time:
            return False
        
        # Check daily window (simplified - assumes UTC)
        current_time = now.strftime("%H:%M")
        
        if campaign.daily_start_time and current_time < campaign.daily_start_time:
            return False
        
        if campaign.daily_end_time and current_time > campaign.daily_end_time:
            return False
        
        return True
    
    async def _check_rate_limits(self, campaign: Campaign) -> bool:
        """Check if campaign is within rate limits."""
        async with self._cache_lock:
            cache = self._rate_limit_cache.get(campaign.id, {})
            
            now = datetime.utcnow()
            
            # Check concurrent calls
            concurrent = cache.get("concurrent", 0)
            if concurrent >= campaign.max_concurrent_calls:
                return False
            
            # Check calls per minute
            minute_key = now.strftime("%Y-%m-%d %H:%M")
            minute_calls = cache.get(f"minute_{minute_key}", 0)
            if minute_calls >= campaign.calls_per_minute:
                return False
            
            return True
    
    async def _update_rate_limit_cache(self, campaign_id: UUID) -> None:
        """Update rate limit cache after task assignment."""
        async with self._cache_lock:
            if campaign_id not in self._rate_limit_cache:
                self._rate_limit_cache[campaign_id] = {}
            
            cache = self._rate_limit_cache[campaign_id]
            
            # Increment concurrent
            cache["concurrent"] = cache.get("concurrent", 0) + 1
            
            # Increment minute counter
            now = datetime.utcnow()
            minute_key = now.strftime("%Y-%m-%d %H:%M")
            cache[f"minute_{minute_key}"] = cache.get(f"minute_{minute_key}", 0) + 1
    
    async def mark_in_progress(self, task_id: UUID) -> CallTask:
        """Mark task as in progress."""
        try:
            result = await self.db_session.execute(
                select(CallTask).where(CallTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise CampaignServiceError(f"Task {task_id} not found")
            
            task.status = "in_progress"
            task.attempt_count += 1
            task.last_attempt_at = datetime.utcnow()
            
            await self.db_session.commit()
            await self.db_session.refresh(task)
            
            return task
            
        except Exception as e:
            try:
                await self.db_session.rollback()
            except Exception:
                pass  # Ignore rollback errors (session may be in invalid state)
            logger.error(f"Failed to mark task in progress: {e}", exc_info=True)
            raise
    
    async def mark_completed(
        self,
        task_id: UUID,
        call_id: Optional[UUID],
        outcome: str
    ) -> CallTask:
        """Mark task as completed."""
        try:
            result = await self.db_session.execute(
                select(CallTask).where(CallTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise CampaignServiceError(f"Task {task_id} not found")
            
            task.status = "completed"
            if call_id:
                task.call_id = call_id
            task.outcome = outcome
            
            # Update campaign stats
            campaign = await self.get_by_id(task.campaign_id)
            if campaign:
                campaign.completed_tasks += 1
            
            await self.db_session.commit()
            await self.db_session.refresh(task)
            
            # Decrement concurrent counter
            await self._decrement_concurrent(task.campaign_id)
            
            return task
            
        except Exception as e:
            try:
                await self.db_session.rollback()
            except Exception:
                pass  # Ignore rollback errors (session may be in invalid state)
            logger.error(f"Failed to mark task completed: {e}", exc_info=True)
            raise
    
    async def mark_failed(
        self,
        task_id: UUID,
        error_message: str
    ) -> CallTask:
        """Mark task as failed or retry."""
        try:
            # Eager load campaign relationship to avoid lazy loading in async context
            result = await self.db_session.execute(
                select(CallTask)
                .where(CallTask.id == task_id)
                .options(selectinload(CallTask.campaign))
            )
            task = result.scalar_one_or_none()
            
            if not task:
                raise CampaignServiceError(f"Task {task_id} not found")
            
            # Campaign is already loaded via eager loading
            campaign = task.campaign
            
            if task.attempt_count < campaign.max_retries:
                # Schedule retry
                task.status = "retry"
                task.next_attempt_at = datetime.utcnow() + timedelta(
                    minutes=campaign.retry_delay_minutes
                )
            else:
                # Mark as failed
                task.status = "failed"
                if campaign:
                    campaign.failed_tasks += 1
            
            task.error_message = error_message
            
            await self.db_session.commit()
            await self.db_session.refresh(task)
            
            # Decrement concurrent counter
            await self._decrement_concurrent(task.campaign_id)
            
            return task
            
        except Exception as e:
            try:
                await self.db_session.rollback()
            except Exception:
                pass  # Ignore rollback errors (session may be in invalid state)
            logger.error(f"Failed to mark task failed: {e}", exc_info=True)
            raise
    
    async def _decrement_concurrent(self, campaign_id: UUID) -> None:
        """Decrement concurrent call counter."""
        async with self._cache_lock:
            if campaign_id in self._rate_limit_cache:
                cache = self._rate_limit_cache[campaign_id]
                cache["concurrent"] = max(0, cache.get("concurrent", 0) - 1)
