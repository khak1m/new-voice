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
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from livekit import api

from database.models import CallTask, Campaign, Call
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
        livekit_url: str,
        livekit_api_key: str,
        livekit_api_secret: str,
        sip_trunk_id: Optional[str] = None,
        voice_agent_factory: Optional[Callable] = None,
        poll_interval: float = 1.0
    ):
        """
        Initialize CampaignWorker.
        
        Args:
            db_session: Async database session
            livekit_url: LiveKit server URL
            livekit_api_key: LiveKit API key
            livekit_api_secret: LiveKit API secret
            sip_trunk_id: SIP trunk ID for outbound calls (optional)
            voice_agent_factory: Factory function to create VoiceAgent instances (optional)
            poll_interval: Seconds between polling cycles (default: 1.0)
        """
        self.db_session = db_session
        self.campaign_service = CampaignService(db_session)
        self.voice_agent_factory = voice_agent_factory
        self.poll_interval = poll_interval
        
        # LiveKit configuration
        self.livekit_url = livekit_url
        self.livekit_api_key = livekit_api_key
        self.livekit_api_secret = livekit_api_secret
        self.sip_trunk_id = sip_trunk_id
        
        # Initialize LiveKit API client
        self.livekit_api = api.LiveKitAPI(
            url=livekit_url,
            api_key=livekit_api_key,
            api_secret=livekit_api_secret
        )
        
        self._running = False
        self._active_tasks = set()
        
        logger.info(
            "CampaignWorker initialized",
            extra={
                "livekit_url": livekit_url,
                "sip_trunk_id": sip_trunk_id
            }
        )
    
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
        
        # Close LiveKit API client
        try:
            await self.livekit_api.aclose()
            logger.debug("LiveKit API client closed")
        except Exception as e:
            logger.warning(f"Error closing LiveKit API client: {e}")
        
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
        call_id = None
        
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
            
            # Step 1: Create LiveKit room
            room_name = f"campaign-{task.campaign_id}-{task_id}"
            logger.debug(f"Creating LiveKit room: {room_name}")
            
            room = await self.livekit_api.room.create_room(
                api.CreateRoomRequest(name=room_name)
            )
            
            logger.info(
                f"LiveKit room created: {room.name}",
                extra={"room_name": room.name, "task_id": str(task_id)}
            )
            
            # Step 2: Create Call record in database
            call_id = uuid4()
            call = Call(
                id=call_id,
                company_id=task.campaign.company_id,
                skillbase_id=task.campaign.skillbase_id,
                phone_number=phone_number,
                direction="outbound",
                status="initiated",
                room_name=room.name
            )
            self.db_session.add(call)
            await self.db_session.commit()
            
            logger.info(
                f"Call record created: {call_id}",
                extra={"call_id": str(call_id), "task_id": str(task_id)}
            )
            
            # Step 3: Dial phone number via SIP
            if self.sip_trunk_id:
                logger.debug(f"Dialing {phone_number} via SIP trunk {self.sip_trunk_id}")
                
                try:
                    participant = await self.livekit_api.sip.create_sip_participant(
                        api.CreateSIPParticipantRequest(
                            sip_trunk_id=self.sip_trunk_id,
                            sip_call_to=phone_number,
                            room_name=room.name,
                            participant_identity=f"caller-{task_id}",
                            participant_name=task.contact_name or "Caller"
                        )
                    )
                    
                    logger.info(
                        f"SIP participant created: {participant.participant_id}",
                        extra={
                            "participant_id": participant.participant_id,
                            "phone_number": phone_number,
                            "task_id": str(task_id)
                        }
                    )
                except Exception as sip_error:
                    logger.error(
                        f"Failed to create SIP participant: {sip_error}",
                        extra={"task_id": str(task_id)},
                        exc_info=True
                    )
                    raise CampaignWorkerError(f"SIP dial failed: {sip_error}")
            else:
                logger.warning(
                    "No SIP trunk configured, skipping dial",
                    extra={"task_id": str(task_id)}
                )
            
            # Step 4: Run VoiceAgent (if factory provided)
            if self.voice_agent_factory:
                logger.debug(f"Running VoiceAgent for task {task_id}")
                
                try:
                    # Create agent instance with skillbase config
                    agent = await self.voice_agent_factory(
                        skillbase_id=task.campaign.skillbase_id,
                        room_name=room.name,
                        call_id=call_id
                    )
                    
                    # Run agent (this will block until call ends)
                    result = await agent.run()
                    
                    logger.info(
                        f"VoiceAgent completed for task {task_id}",
                        extra={
                            "task_id": str(task_id),
                            "outcome": result.get("outcome", "unknown")
                        }
                    )
                    
                    # Extract outcome from result
                    outcome = result.get("outcome", "completed")
                    
                except Exception as agent_error:
                    logger.error(
                        f"VoiceAgent failed: {agent_error}",
                        extra={"task_id": str(task_id)},
                        exc_info=True
                    )
                    outcome = "agent_error"
            else:
                logger.warning(
                    "No VoiceAgent factory configured, simulating call",
                    extra={"task_id": str(task_id)}
                )
                # Simulate call duration
                await asyncio.sleep(5)
                outcome = "success"
            
            # Step 5: Mark task as completed
            await self.campaign_service.mark_completed(
                task_id=task_id,
                call_id=call_id,
                outcome=outcome
            )
            
            logger.info(
                f"Task {task_id} completed successfully",
                extra={
                    "task_id": str(task_id),
                    "call_id": str(call_id),
                    "outcome": outcome
                }
            )
        
        except Exception as e:
            logger.error(
                f"Task {task_id} failed: {e}",
                extra={
                    "task_id": str(task_id),
                    "call_id": str(call_id) if call_id else None,
                    "error": str(e)
                },
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
        
        finally:
            # Cleanup: close LiveKit room if created
            if call_id:
                try:
                    await self.livekit_api.room.delete_room(
                        api.DeleteRoomRequest(room=room_name)
                    )
                    logger.debug(f"LiveKit room deleted: {room_name}")
                except Exception as cleanup_error:
                    logger.warning(
                        f"Failed to cleanup room {room_name}: {cleanup_error}"
                    )
