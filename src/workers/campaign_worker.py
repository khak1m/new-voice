"""
CampaignWorker - Background worker for processing outbound calling campaigns.

This worker:
1. Polls active campaigns for pending tasks
2. Respects rate limits and scheduling windows
3. Creates LiveKit rooms and dials phone numbers
4. Runs VoiceAgent for each call
5. Updates task status (completed/failed/retry)
6. Handles errors and automatic recovery
"""

import asyncio
import logging
from typing import Optional, Callable, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CallTask, Campaign
from services.campaign_service import CampaignService

logger = logging.getLogger(__name__)


class CampaignWorkerError(Exception):
    """Base exception for CampaignWorker errors."""
    pass


class CampaignWorker:
    """
    Background worker for outbound calling campaigns.
    
    Continuously polls active campaigns and processes pending call tasks.
    Handles task execution, error recovery, and graceful shutdown.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        voice_agent_factory: Optional[Callable] = None,
        livekit_client: Optional[Any] = None,
        poll_interval: float = 1.0
    ):
        """
        Initialize CampaignWorker.
        
        Args:
            db_session: Async database session
            voice_agent_factory: Factory function to create VoiceAgent instances
            livekit_client: LiveKit client for room creation and dialing
            poll_interval: Seconds between polling cycles (default: 1.0)
        """
        self.db_session = db_session
        self.campaign_service = CampaignService(db_session)
        self.voice_agent_factory = voice_agent_factory
        self.livekit_client = livekit_client
        self.poll_interval = poll_interval
        
        self._running = False
        self._active_tasks = set()
        
        logger.info("CampaignWorker initialized")
    
    async def start(self) -> None:
        """
        Start the campaign worker.
        
        Begins the main processing loop that polls for pending tasks
        and executes them in the background.
        """
        if self._running:
            logger.warning("CampaignWorker already running")
            return
        
        self._running = True
        logger.info("CampaignWorker started")
        
        try:
            while self._running:
                await self._process_pending_tasks()
                await asyncio.sleep(self.poll_interval)
        except Exception as e:
            logger.error(f"CampaignWorker crashed: {e}", exc_info=True)
            raise
        finally:
            logger.info("CampaignWorker stopped")
    
    async def stop(self) -> None:
        """
        Stop the campaign worker gracefully.
        
        Waits for active tasks to complete before shutting down.
        """
        if not self._running:
            logger.warning("CampaignWorker not running")
            return
        
        logger.info("Stopping CampaignWorker...")
        self._running = False
        
        # Wait for active tasks to complete
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks to complete...")
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        
        logger.info("CampaignWorker stopped gracefully")
    
    async def _process_pending_tasks(self) -> None:
        """
        Process pending call tasks from all active campaigns.
        
        Polls each active campaign for the next available task
        and spawns a background task to execute it.
        """
        try:
            # Get all active campaigns
            campaigns = await self.campaign_service.get_active_campaigns()
            
            if not campaigns:
                return
            
            logger.debug(f"Processing {len(campaigns)} active campaigns")
            
            for campaign in campaigns:
                # Get next task respecting rate limits
                task = await self.campaign_service.get_next_task(campaign.id)
                
                if task:
                    # Spawn background task for execution
                    bg_task = asyncio.create_task(self._execute_task(task))
                    self._active_tasks.add(bg_task)
                    bg_task.add_done_callback(self._active_tasks.discard)
                    
                    logger.info(
                        f"Spawned task execution for task {task.id}",
                        extra={
                            "task_id": str(task.id),
                            "campaign_id": str(campaign.id),
                            "phone_number": task.phone_number
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}", exc_info=True)
    
    async def _execute_task(self, task: CallTask) -> None:
        """
        Execute a single call task.
        
        Creates LiveKit room, dials phone number, runs VoiceAgent,
        and updates task status based on result.
        
        Args:
            task: CallTask to execute
        """
        task_id = task.id
        phone_number = task.phone_number
        
        try:
            logger.info(
                f"Executing task {task_id}",
                extra={
                    "task_id": str(task_id),
                    "phone_number": phone_number,
                    "attempt": task.attempt_count + 1
                }
            )
            
            # Mark task as in progress
            await self.campaign_service.mark_in_progress(task_id)
            
            # TODO: Implement actual call execution
            # This is a placeholder for the actual implementation
            # which will be done in Task 15.2
            
            if not self.livekit_client or not self.voice_agent_factory:
                raise CampaignWorkerError(
                    "LiveKit client or VoiceAgent factory not configured"
                )
            
            # Create LiveKit room
            logger.debug(f"Creating LiveKit room for task {task_id}")
            # room = await self.livekit_client.create_room()
            
            # Dial phone number
            logger.debug(f"Dialing {phone_number}")
            # await self.livekit_client.dial_phone(room.name, phone_number)
            
            # Run voice agent
            logger.debug(f"Running VoiceAgent for task {task_id}")
            # agent = self.voice_agent_factory(task.campaign.skillbase)
            # result = await agent.run(room)
            
            # For now, simulate success
            await asyncio.sleep(0.1)  # Simulate call duration
            
            # Mark task as completed
            await self.campaign_service.mark_completed(
                task_id=task_id,
                call_id=None,  # Will be real call_id in Task 15.2
                outcome="success"
            )
            
            logger.info(
                f"Task {task_id} completed successfully",
                extra={"task_id": str(task_id)}
            )
        
        except Exception as e:
            logger.error(
                f"Task {task_id} failed: {e}",
                extra={"task_id": str(task_id), "error": str(e)},
                exc_info=True
            )
            
            # Mark task as failed (will retry if attempts remaining)
            try:
                await self.campaign_service.mark_failed(
                    task_id=task_id,
                    error_message=str(e)
                )
            except Exception as mark_error:
                logger.error(
                    f"Failed to mark task {task_id} as failed: {mark_error}",
                    exc_info=True
                )
