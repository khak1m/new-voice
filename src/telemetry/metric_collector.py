"""
MetricCollector - Timing hooks for voice pipeline.

This collector:
1. Tracks timing for STT, LLM, TTS operations
2. Calculates TTFB (Time To First Byte) metrics
3. Calculates EOU (End Of Utterance) latency
4. Non-blocking metric recording
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass

from .telemetry_service import TelemetryService, TurnMetrics

logger = logging.getLogger(__name__)


@dataclass
class TurnContext:
    """Context for tracking a single conversation turn."""
    turn_number: int
    role: str
    content: str
    state_id: Optional[str] = None
    
    # Timing markers
    turn_start: Optional[float] = None
    stt_start: Optional[float] = None
    stt_first_byte: Optional[float] = None
    llm_start: Optional[float] = None
    llm_complete: Optional[float] = None
    tts_start: Optional[float] = None
    tts_first_byte: Optional[float] = None
    audio_playback_start: Optional[float] = None
    
    # Token counts
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    tts_characters: int = 0


class MetricCollector:
    """
    Collects timing metrics during voice pipeline execution.
    
    Provides hooks for STT, LLM, and TTS operations to track
    latency and throughput metrics.
    """
    
    def __init__(self, call_id: str, telemetry: TelemetryService):
        """
        Initialize MetricCollector.
        
        Args:
            call_id: Unique call identifier
            telemetry: TelemetryService for persisting metrics
        """
        self.call_id = call_id
        self.telemetry = telemetry
        self._current_turn: Optional[TurnContext] = None
        self._turn_counter = 0
        logger.debug(f"MetricCollector initialized for call {call_id}")
    
    def start_turn(
        self, 
        role: str, 
        content: str = "", 
        state_id: Optional[str] = None
    ) -> None:
        """
        Start tracking a new conversation turn.
        
        Args:
            role: Role for this turn (user, assistant, system)
            content: Turn content (can be updated later)
            state_id: Optional state identifier
        """
        self._turn_counter += 1
        self._current_turn = TurnContext(
            turn_number=self._turn_counter,
            role=role,
            content=content,
            state_id=state_id,
            turn_start=time.perf_counter()
        )
        logger.debug(
            f"Started turn {self._turn_counter} for call {self.call_id}",
            extra={"call_id": self.call_id, "turn_number": self._turn_counter, "role": role}
        )
    
    def update_turn_content(self, content: str) -> None:
        """
        Update content for current turn.
        
        Args:
            content: Updated content
        """
        if self._current_turn:
            self._current_turn.content = content
    
    def on_user_speech_start(self) -> None:
        """Called when user starts speaking."""
        if self._current_turn:
            self._current_turn.turn_start = time.perf_counter()
            logger.debug(f"User speech started for call {self.call_id}")
    
    def on_stt_start(self) -> None:
        """Called when STT processing starts."""
        if self._current_turn:
            self._current_turn.stt_start = time.perf_counter()
            logger.debug(f"STT started for call {self.call_id}")
    
    def on_stt_first_byte(self) -> Optional[float]:
        """
        Called when first STT result arrives.
        
        Returns:
            TTFB in milliseconds, or None if timing not available
        """
        if self._current_turn and self._current_turn.stt_start:
            ttfb = (time.perf_counter() - self._current_turn.stt_start) * 1000
            self._current_turn.stt_first_byte = ttfb
            logger.debug(
                f"STT first byte for call {self.call_id}: {ttfb:.2f}ms",
                extra={"call_id": self.call_id, "ttfb_stt": ttfb}
            )
            return ttfb
        return None
    
    def on_llm_start(self) -> None:
        """Called when LLM request starts."""
        if self._current_turn:
            self._current_turn.llm_start = time.perf_counter()
            logger.debug(f"LLM started for call {self.call_id}")
    
    def on_llm_complete(
        self, 
        input_tokens: int = 0, 
        output_tokens: int = 0
    ) -> Optional[float]:
        """
        Called when LLM response complete.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Latency in milliseconds, or None if timing not available
        """
        if self._current_turn and self._current_turn.llm_start:
            latency = (time.perf_counter() - self._current_turn.llm_start) * 1000
            self._current_turn.llm_complete = latency
            self._current_turn.llm_input_tokens = input_tokens
            self._current_turn.llm_output_tokens = output_tokens
            logger.debug(
                f"LLM complete for call {self.call_id}: {latency:.2f}ms",
                extra={
                    "call_id": self.call_id,
                    "latency_llm": latency,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            return latency
        return None
    
    def on_tts_start(self, text: str) -> None:
        """
        Called when TTS request starts.
        
        Args:
            text: Text being synthesized
        """
        if self._current_turn:
            self._current_turn.tts_start = time.perf_counter()
            self._current_turn.tts_characters = len(text)
            logger.debug(
                f"TTS started for call {self.call_id}: {len(text)} chars",
                extra={"call_id": self.call_id, "tts_characters": len(text)}
            )
    
    def on_tts_first_byte(self) -> Optional[float]:
        """
        Called when first TTS audio arrives.
        
        Returns:
            TTFB in milliseconds, or None if timing not available
        """
        if self._current_turn and self._current_turn.tts_start:
            ttfb = (time.perf_counter() - self._current_turn.tts_start) * 1000
            self._current_turn.tts_first_byte = ttfb
            logger.debug(
                f"TTS first byte for call {self.call_id}: {ttfb:.2f}ms",
                extra={"call_id": self.call_id, "ttfb_tts": ttfb}
            )
            return ttfb
        return None
    
    def on_audio_playback_start(self) -> Optional[float]:
        """
        Called when audio starts playing.
        
        Returns:
            EOU latency in milliseconds, or None if timing not available
        """
        if self._current_turn and self._current_turn.turn_start:
            eou_latency = (time.perf_counter() - self._current_turn.turn_start) * 1000
            self._current_turn.audio_playback_start = eou_latency
            logger.debug(
                f"Audio playback started for call {self.call_id}: {eou_latency:.2f}ms EOU",
                extra={"call_id": self.call_id, "eou_latency": eou_latency}
            )
            return eou_latency
        return None
    
    async def finalize_turn(self) -> None:
        """
        Finalize current turn and record metrics.
        
        This method is non-blocking and safe to call from async context.
        """
        if not self._current_turn:
            logger.warning(f"No active turn to finalize for call {self.call_id}")
            return
        
        try:
            # Create TurnMetrics from context
            metrics = TurnMetrics(
                turn_number=self._current_turn.turn_number,
                role=self._current_turn.role,
                content=self._current_turn.content,
                state_id=self._current_turn.state_id,
                ttfb_stt=self._current_turn.stt_first_byte,
                latency_llm=self._current_turn.llm_complete,
                ttfb_tts=self._current_turn.tts_first_byte,
                eou_latency=self._current_turn.audio_playback_start,
                llm_input_tokens=self._current_turn.llm_input_tokens,
                llm_output_tokens=self._current_turn.llm_output_tokens,
                tts_characters=self._current_turn.tts_characters
            )
            
            # Record to telemetry (non-blocking)
            await self.telemetry.record_turn(self.call_id, metrics)
            
            logger.info(
                f"Finalized turn {self._current_turn.turn_number} for call {self.call_id}",
                extra={
                    "call_id": self.call_id,
                    "turn_number": self._current_turn.turn_number,
                    "role": self._current_turn.role
                }
            )
            
            # Clear current turn
            self._current_turn = None
            
        except Exception as e:
            logger.error(
                f"Failed to finalize turn: {e}",
                extra={"call_id": self.call_id},
                exc_info=True
            )
    
    def get_turn_count(self) -> int:
        """
        Get total number of turns recorded.
        
        Returns:
            Turn count
        """
        return self._turn_counter
