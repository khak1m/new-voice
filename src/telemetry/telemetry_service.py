"""
TelemetryService - Collects and aggregates call metrics.

This service:
1. Buffers per-turn metrics in memory during a call
2. Aggregates metrics when call ends
3. Persists to call_metrics and call_logs tables
4. Thread-safe for concurrent calls
"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import CallMetrics, CallLog

logger = logging.getLogger(__name__)


@dataclass
class TurnMetrics:
    """Metrics for a single conversation turn."""
    turn_number: int
    role: str  # user, assistant, system
    content: str
    state_id: Optional[str] = None
    
    # Latency metrics (milliseconds)
    ttfb_stt: Optional[float] = None
    latency_llm: Optional[float] = None
    ttfb_tts: Optional[float] = None
    eou_latency: Optional[float] = None
    
    # Token counts
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    tts_characters: int = 0
    
    # Timestamp
    timestamp: Optional[datetime] = None


class TelemetryService:
    """
    Collects and persists call metrics.
    
    Thread-safe service for buffering per-turn metrics and aggregating
    them into call-level statistics.
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize TelemetryService.
        
        Args:
            db_session: Async database session for persistence
        """
        self.db_session = db_session
        self._metrics_buffer: Dict[str, List[TurnMetrics]] = {}
        self._lock = asyncio.Lock()
        logger.info("TelemetryService initialized")
    
    async def record_turn(
        self, 
        call_id: str, 
        metrics: TurnMetrics
    ) -> None:
        """
        Record metrics for a single turn (non-blocking).
        
        Args:
            call_id: Unique call identifier
            metrics: Turn metrics to record
        """
        try:
            async with self._lock:
                if call_id not in self._metrics_buffer:
                    self._metrics_buffer[call_id] = []
                
                # Set timestamp if not provided
                if metrics.timestamp is None:
                    metrics.timestamp = datetime.utcnow()
                
                self._metrics_buffer[call_id].append(metrics)
                
                logger.debug(
                    f"Recorded turn {metrics.turn_number} for call {call_id}",
                    extra={
                        "call_id": call_id,
                        "turn_number": metrics.turn_number,
                        "role": metrics.role
                    }
                )
        except Exception as e:
            logger.error(
                f"Failed to record turn metrics: {e}",
                extra={"call_id": call_id},
                exc_info=True
            )
    
    async def finalize_call(
        self, 
        call_id: UUID,
        outcome: str,
        outcome_confidence: float,
        outcome_reason: Optional[str] = None,
        interruption_count: int = 0,
        sentiment_score: Optional[float] = None,
        stt_duration_sec: float = 0.0,
        livekit_duration_sec: float = 0.0
    ) -> Optional[CallMetrics]:
        """
        Aggregate buffered metrics and persist to database.
        
        Args:
            call_id: Unique call identifier
            outcome: Call outcome (success, fail, voicemail, no_answer, busy)
            outcome_confidence: Confidence score for outcome (0.0-1.0)
            outcome_reason: Optional reason for outcome
            interruption_count: Number of user interruptions
            sentiment_score: Sentiment score (-1.0 to 1.0)
            stt_duration_sec: Total STT processing duration
            livekit_duration_sec: Total LiveKit session duration
        
        Returns:
            CallMetrics object if successful, None otherwise
        """
        try:
            call_id_str = str(call_id)
            
            async with self._lock:
                turns = self._metrics_buffer.get(call_id_str, [])
                
                if not turns:
                    logger.warning(
                        f"No metrics found for call {call_id}",
                        extra={"call_id": call_id_str}
                    )
                    return None
                
                # Calculate aggregates
                aggregates = self._calculate_aggregates(turns)
                
                # Calculate interruption rate
                turn_count = len(turns)
                interruption_rate = (
                    interruption_count / turn_count if turn_count > 0 else 0.0
                )
                
                # Create CallMetrics record
                call_metrics = CallMetrics(
                    call_id=call_id,
                    
                    # Latency aggregates
                    avg_ttfb_stt=aggregates["avg_ttfb_stt"],
                    avg_latency_llm=aggregates["avg_latency_llm"],
                    avg_ttfb_tts=aggregates["avg_ttfb_tts"],
                    avg_eou_latency=aggregates["avg_eou_latency"],
                    
                    min_ttfb_stt=aggregates["min_ttfb_stt"],
                    max_ttfb_stt=aggregates["max_ttfb_stt"],
                    min_latency_llm=aggregates["min_latency_llm"],
                    max_latency_llm=aggregates["max_latency_llm"],
                    min_ttfb_tts=aggregates["min_ttfb_tts"],
                    max_ttfb_tts=aggregates["max_ttfb_tts"],
                    min_eou_latency=aggregates["min_eou_latency"],
                    max_eou_latency=aggregates["max_eou_latency"],
                    
                    # Usage metrics
                    stt_duration_sec=stt_duration_sec,
                    llm_input_tokens=aggregates["total_llm_input_tokens"],
                    llm_output_tokens=aggregates["total_llm_output_tokens"],
                    tts_characters=aggregates["total_tts_characters"],
                    livekit_duration_sec=livekit_duration_sec,
                    
                    # Quality metrics
                    turn_count=turn_count,
                    interruption_count=interruption_count,
                    interruption_rate=interruption_rate,
                    sentiment_score=sentiment_score,
                    
                    # Outcome
                    outcome=outcome,
                    outcome_confidence=outcome_confidence,
                    outcome_reason=outcome_reason
                )
                
                self.db_session.add(call_metrics)
                
                # Create CallLog records for each turn
                for turn in turns:
                    call_log = CallLog(
                        call_id=call_id,
                        turn_number=turn.turn_number,
                        role=turn.role,
                        content=turn.content,
                        state_id=turn.state_id,
                        ttfb_stt=turn.ttfb_stt,
                        latency_llm=turn.latency_llm,
                        ttfb_tts=turn.ttfb_tts,
                        eou_latency=turn.eou_latency,
                        llm_input_tokens=turn.llm_input_tokens,
                        llm_output_tokens=turn.llm_output_tokens,
                        tts_characters=turn.tts_characters,
                        timestamp=turn.timestamp
                    )
                    self.db_session.add(call_log)
                
                # Commit to database
                await self.db_session.commit()
                
                # Clear buffer
                del self._metrics_buffer[call_id_str]
                
                logger.info(
                    f"Finalized call metrics for {call_id}",
                    extra={
                        "call_id": call_id_str,
                        "turn_count": turn_count,
                        "outcome": outcome
                    }
                )
                
                return call_metrics
                
        except Exception as e:
            logger.error(
                f"Failed to finalize call metrics: {e}",
                extra={"call_id": str(call_id)},
                exc_info=True
            )
            await self.db_session.rollback()
            return None
    
    def _calculate_aggregates(self, turns: List[TurnMetrics]) -> dict:
        """
        Calculate aggregate statistics from turn metrics.
        
        Args:
            turns: List of turn metrics
        
        Returns:
            Dictionary with aggregated metrics
        """
        # Collect non-None values for each metric
        ttfb_stt_values = [t.ttfb_stt for t in turns if t.ttfb_stt is not None]
        latency_llm_values = [t.latency_llm for t in turns if t.latency_llm is not None]
        ttfb_tts_values = [t.ttfb_tts for t in turns if t.ttfb_tts is not None]
        eou_latency_values = [t.eou_latency for t in turns if t.eou_latency is not None]
        
        # Helper function for safe aggregation
        def safe_avg(values: List[float]) -> Optional[float]:
            return sum(values) / len(values) if values else None
        
        def safe_min(values: List[float]) -> Optional[float]:
            return min(values) if values else None
        
        def safe_max(values: List[float]) -> Optional[float]:
            return max(values) if values else None
        
        return {
            # Latency averages
            "avg_ttfb_stt": safe_avg(ttfb_stt_values),
            "avg_latency_llm": safe_avg(latency_llm_values),
            "avg_ttfb_tts": safe_avg(ttfb_tts_values),
            "avg_eou_latency": safe_avg(eou_latency_values),
            
            # Latency min/max
            "min_ttfb_stt": safe_min(ttfb_stt_values),
            "max_ttfb_stt": safe_max(ttfb_stt_values),
            "min_latency_llm": safe_min(latency_llm_values),
            "max_latency_llm": safe_max(latency_llm_values),
            "min_ttfb_tts": safe_min(ttfb_tts_values),
            "max_ttfb_tts": safe_max(ttfb_tts_values),
            "min_eou_latency": safe_min(eou_latency_values),
            "max_eou_latency": safe_max(eou_latency_values),
            
            # Token/character totals
            "total_llm_input_tokens": sum(t.llm_input_tokens for t in turns),
            "total_llm_output_tokens": sum(t.llm_output_tokens for t in turns),
            "total_tts_characters": sum(t.tts_characters for t in turns),
        }
    
    async def get_call_metrics(self, call_id: UUID) -> Optional[CallMetrics]:
        """
        Retrieve persisted call metrics.
        
        Args:
            call_id: Unique call identifier
        
        Returns:
            CallMetrics object if found, None otherwise
        """
        try:
            result = await self.db_session.execute(
                select(CallMetrics).where(CallMetrics.call_id == call_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Failed to retrieve call metrics: {e}",
                extra={"call_id": str(call_id)},
                exc_info=True
            )
            return None
    
    async def get_call_logs(self, call_id: UUID) -> List[CallLog]:
        """
        Retrieve persisted call logs.
        
        Args:
            call_id: Unique call identifier
        
        Returns:
            List of CallLog objects ordered by turn_number
        """
        try:
            result = await self.db_session.execute(
                select(CallLog)
                .where(CallLog.call_id == call_id)
                .order_by(CallLog.turn_number)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(
                f"Failed to retrieve call logs: {e}",
                extra={"call_id": str(call_id)},
                exc_info=True
            )
            return []
