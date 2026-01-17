"""
Quality Metrics - Tracks call quality indicators.

This module provides:
1. Interruption tracking (user interrupting bot)
2. Sentiment analysis interface
3. Outcome classification
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CallOutcome(str, Enum):
    """Call outcome classification."""
    SUCCESS = "success"
    FAIL = "fail"
    VOICEMAIL = "voicemail"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    UNKNOWN = "unknown"


@dataclass
class OutcomeResult:
    """Result of outcome classification."""
    outcome: CallOutcome
    confidence: float  # 0.0 to 1.0
    reason: Optional[str] = None


class InterruptionTracker:
    """
    Tracks user interruptions during bot speech.
    
    An interruption occurs when the user starts speaking
    while the bot is still speaking.
    """
    
    def __init__(self):
        """Initialize InterruptionTracker."""
        self._interruption_count = 0
        self._bot_speaking = False
        self._total_turns = 0
        logger.debug("InterruptionTracker initialized")
    
    def on_bot_speech_start(self) -> None:
        """Called when bot starts speaking."""
        self._bot_speaking = True
        logger.debug("Bot speech started")
    
    def on_bot_speech_end(self) -> None:
        """Called when bot finishes speaking."""
        self._bot_speaking = False
        logger.debug("Bot speech ended")
    
    def on_user_speech_start(self) -> bool:
        """
        Called when user starts speaking.
        
        Returns:
            True if this is an interruption, False otherwise
        """
        self._total_turns += 1
        
        if self._bot_speaking:
            self._interruption_count += 1
            logger.info(
                f"Interruption detected (count: {self._interruption_count})",
                extra={"interruption_count": self._interruption_count}
            )
            # Bot was interrupted, stop speaking
            self._bot_speaking = False
            return True
        
        return False
    
    def get_interruption_count(self) -> int:
        """
        Get total number of interruptions.
        
        Returns:
            Interruption count
        """
        return self._interruption_count
    
    def get_interruption_rate(self) -> float:
        """
        Calculate interruption rate.
        
        Returns:
            Interruption rate (interruptions / total_turns)
        """
        if self._total_turns == 0:
            return 0.0
        
        rate = self._interruption_count / self._total_turns
        logger.debug(
            f"Interruption rate: {rate:.2%}",
            extra={
                "interruption_count": self._interruption_count,
                "total_turns": self._total_turns,
                "interruption_rate": rate
            }
        )
        return rate
    
    def reset(self) -> None:
        """Reset tracker state."""
        self._interruption_count = 0
        self._bot_speaking = False
        self._total_turns = 0
        logger.debug("InterruptionTracker reset")


class SentimentAnalyzer:
    """
    Interface for sentiment analysis.
    
    This is a placeholder for future sentiment analysis integration.
    Can be implemented with external services like:
    - OpenAI GPT-4 for sentiment
    - Hugging Face sentiment models
    - Custom sentiment models
    """
    
    def __init__(self):
        """Initialize SentimentAnalyzer."""
        logger.info("SentimentAnalyzer initialized (placeholder)")
    
    async def analyze(self, transcript: str) -> float:
        """
        Analyze sentiment of conversation transcript.
        
        Args:
            transcript: Full conversation transcript
        
        Returns:
            Sentiment score from -1.0 (negative) to 1.0 (positive)
        """
        # Placeholder implementation
        # TODO: Integrate with actual sentiment analysis service
        logger.debug("Sentiment analysis requested (not implemented)")
        return 0.0
    
    async def analyze_turn(self, text: str, role: str) -> float:
        """
        Analyze sentiment of a single turn.
        
        Args:
            text: Turn text
            role: Speaker role (user, assistant)
        
        Returns:
            Sentiment score from -1.0 (negative) to 1.0 (positive)
        """
        # Placeholder implementation
        logger.debug(f"Turn sentiment analysis requested for {role} (not implemented)")
        return 0.0


class OutcomeClassifier:
    """
    Classifies call outcomes based on conversation flow.
    
    Outcomes:
    - success: Goal achieved, positive outcome
    - fail: Goal not achieved, negative outcome
    - voicemail: Reached voicemail
    - no_answer: No one answered
    - busy: Line was busy
    """
    
    def __init__(self):
        """Initialize OutcomeClassifier."""
        logger.info("OutcomeClassifier initialized")
    
    def classify_from_state(
        self, 
        final_state: str,
        turn_count: int,
        duration_sec: float
    ) -> OutcomeResult:
        """
        Classify outcome based on final conversation state.
        
        Args:
            final_state: Final state ID from ScenarioEngine
            turn_count: Number of conversation turns
            duration_sec: Call duration in seconds
        
        Returns:
            OutcomeResult with classification
        """
        # Simple heuristic-based classification
        # TODO: Implement ML-based classification
        
        # Check for success indicators
        if "success" in final_state.lower() or "complete" in final_state.lower():
            return OutcomeResult(
                outcome=CallOutcome.SUCCESS,
                confidence=0.9,
                reason=f"Reached success state: {final_state}"
            )
        
        # Check for failure indicators
        if "fail" in final_state.lower() or "error" in final_state.lower():
            return OutcomeResult(
                outcome=CallOutcome.FAIL,
                confidence=0.85,
                reason=f"Reached failure state: {final_state}"
            )
        
        # Check for voicemail indicators
        if "voicemail" in final_state.lower():
            return OutcomeResult(
                outcome=CallOutcome.VOICEMAIL,
                confidence=0.95,
                reason="Voicemail detected"
            )
        
        # Check for very short calls (likely no answer or busy)
        if turn_count < 2 and duration_sec < 10:
            return OutcomeResult(
                outcome=CallOutcome.NO_ANSWER,
                confidence=0.7,
                reason="Very short call, likely no answer"
            )
        
        # Default to unknown
        return OutcomeResult(
            outcome=CallOutcome.UNKNOWN,
            confidence=0.5,
            reason=f"Could not determine outcome from state: {final_state}"
        )
    
    async def classify_from_transcript(
        self, 
        transcript: List[dict],
        final_state: str
    ) -> OutcomeResult:
        """
        Classify outcome using LLM analysis of transcript.
        
        Args:
            transcript: List of turn dictionaries with role and content
            final_state: Final state ID
        
        Returns:
            OutcomeResult with classification
        """
        # Placeholder for LLM-based classification
        # TODO: Implement LLM-based outcome classification
        
        logger.debug("LLM-based outcome classification requested (not implemented)")
        
        # Fall back to state-based classification
        turn_count = len(transcript)
        duration_sec = turn_count * 10  # Rough estimate
        
        return self.classify_from_state(final_state, turn_count, duration_sec)
    
    def classify_from_keywords(
        self, 
        transcript_text: str
    ) -> OutcomeResult:
        """
        Classify outcome based on keyword matching.
        
        Args:
            transcript_text: Full transcript as text
        
        Returns:
            OutcomeResult with classification
        """
        text_lower = transcript_text.lower()
        
        # Success keywords
        success_keywords = [
            "спасибо", "отлично", "хорошо", "договорились",
            "записал", "записала", "подтверждаю", "согласен"
        ]
        
        # Failure keywords
        failure_keywords = [
            "не интересно", "не нужно", "не хочу", "откажусь",
            "не звоните", "удалите", "отстаньте"
        ]
        
        # Voicemail keywords
        voicemail_keywords = [
            "оставьте сообщение", "после сигнала", "голосовая почта"
        ]
        
        # Count keyword matches
        success_count = sum(1 for kw in success_keywords if kw in text_lower)
        failure_count = sum(1 for kw in failure_keywords if kw in text_lower)
        voicemail_count = sum(1 for kw in voicemail_keywords if kw in text_lower)
        
        # Classify based on highest count
        if voicemail_count > 0:
            return OutcomeResult(
                outcome=CallOutcome.VOICEMAIL,
                confidence=0.9,
                reason="Voicemail keywords detected"
            )
        
        if success_count > failure_count and success_count > 0:
            confidence = min(0.6 + (success_count * 0.1), 0.95)
            return OutcomeResult(
                outcome=CallOutcome.SUCCESS,
                confidence=confidence,
                reason=f"Success keywords detected ({success_count})"
            )
        
        if failure_count > success_count and failure_count > 0:
            confidence = min(0.6 + (failure_count * 0.1), 0.95)
            return OutcomeResult(
                outcome=CallOutcome.FAIL,
                confidence=confidence,
                reason=f"Failure keywords detected ({failure_count})"
            )
        
        # Default to unknown
        return OutcomeResult(
            outcome=CallOutcome.UNKNOWN,
            confidence=0.4,
            reason="No clear outcome indicators"
        )


class QualityMetricsCollector:
    """
    Aggregates all quality metrics for a call.
    
    Combines:
    - Interruption tracking
    - Sentiment analysis
    - Outcome classification
    """
    
    def __init__(self):
        """Initialize QualityMetricsCollector."""
        self.interruption_tracker = InterruptionTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.outcome_classifier = OutcomeClassifier()
        logger.info("QualityMetricsCollector initialized")
    
    def on_bot_speech_start(self) -> None:
        """Called when bot starts speaking."""
        self.interruption_tracker.on_bot_speech_start()
    
    def on_bot_speech_end(self) -> None:
        """Called when bot finishes speaking."""
        self.interruption_tracker.on_bot_speech_end()
    
    def on_user_speech_start(self) -> bool:
        """
        Called when user starts speaking.
        
        Returns:
            True if this is an interruption
        """
        return self.interruption_tracker.on_user_speech_start()
    
    def get_interruption_metrics(self) -> dict:
        """
        Get interruption metrics.
        
        Returns:
            Dictionary with interruption_count and interruption_rate
        """
        return {
            "interruption_count": self.interruption_tracker.get_interruption_count(),
            "interruption_rate": self.interruption_tracker.get_interruption_rate()
        }
    
    async def get_sentiment_score(self, transcript: str) -> float:
        """
        Get sentiment score for full transcript.
        
        Args:
            transcript: Full conversation transcript
        
        Returns:
            Sentiment score (-1.0 to 1.0)
        """
        return await self.sentiment_analyzer.analyze(transcript)
    
    def classify_outcome(
        self, 
        final_state: str,
        turn_count: int,
        duration_sec: float
    ) -> OutcomeResult:
        """
        Classify call outcome.
        
        Args:
            final_state: Final conversation state
            turn_count: Number of turns
            duration_sec: Call duration
        
        Returns:
            OutcomeResult with classification
        """
        return self.outcome_classifier.classify_from_state(
            final_state, turn_count, duration_sec
        )
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.interruption_tracker.reset()
        logger.info("QualityMetricsCollector reset")
