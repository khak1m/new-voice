"""
CostCalculator - Calculates call costs based on usage metrics.

This calculator:
1. Uses configurable pricing rates per provider
2. Calculates per-component costs (STT, LLM, TTS, LiveKit)
3. Provides detailed cost breakdown
4. Supports different pricing tiers
"""

import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PricingConfig:
    """
    Provider pricing rates configuration.
    
    All costs are in USD. Rates are based on provider pricing as of 2026.
    """
    # Deepgram STT: per second of audio
    stt_per_second: Decimal = Decimal("0.0043")
    
    # Groq LLM: per 1M tokens
    llm_input_per_million: Decimal = Decimal("0.05")
    llm_output_per_million: Decimal = Decimal("0.08")
    
    # Cartesia TTS: per 1000 characters
    tts_per_thousand_chars: Decimal = Decimal("0.015")
    
    # LiveKit: per minute of session
    livekit_per_minute: Decimal = Decimal("0.004")
    
    def __post_init__(self):
        """Validate pricing configuration."""
        if self.stt_per_second < 0:
            raise ValueError("STT price cannot be negative")
        if self.llm_input_per_million < 0 or self.llm_output_per_million < 0:
            raise ValueError("LLM prices cannot be negative")
        if self.tts_per_thousand_chars < 0:
            raise ValueError("TTS price cannot be negative")
        if self.livekit_per_minute < 0:
            raise ValueError("LiveKit price cannot be negative")


@dataclass
class CostBreakdown:
    """
    Detailed cost breakdown for a call.
    
    All costs are in USD cents for precision (multiply by 100 from Decimal).
    """
    cost_stt: Decimal
    cost_llm: Decimal
    cost_tts: Decimal
    cost_livekit: Decimal
    cost_total: Decimal
    
    def to_dict(self) -> dict:
        """Convert to dictionary with float values."""
        return {
            "cost_stt": float(self.cost_stt),
            "cost_llm": float(self.cost_llm),
            "cost_tts": float(self.cost_tts),
            "cost_livekit": float(self.cost_livekit),
            "cost_total": float(self.cost_total),
        }
    
    def to_cents_dict(self) -> dict:
        """Convert to dictionary with values in cents (for database storage)."""
        return {
            "cost_stt": self.cost_stt,
            "cost_llm": self.cost_llm,
            "cost_tts": self.cost_tts,
            "cost_livekit": self.cost_livekit,
            "cost_total": self.cost_total,
        }


class CostCalculator:
    """
    Calculates call costs based on usage metrics.
    
    Uses provider-specific pricing to calculate costs for:
    - STT (Speech-to-Text)
    - LLM (Language Model)
    - TTS (Text-to-Speech)
    - LiveKit (Session infrastructure)
    """
    
    def __init__(self, pricing: Optional[PricingConfig] = None):
        """
        Initialize CostCalculator.
        
        Args:
            pricing: Optional custom pricing configuration.
                    If None, uses default rates.
        """
        self.pricing = pricing or PricingConfig()
        logger.info(
            "CostCalculator initialized",
            extra={
                "stt_per_second": float(self.pricing.stt_per_second),
                "llm_input_per_million": float(self.pricing.llm_input_per_million),
                "llm_output_per_million": float(self.pricing.llm_output_per_million),
                "tts_per_thousand_chars": float(self.pricing.tts_per_thousand_chars),
                "livekit_per_minute": float(self.pricing.livekit_per_minute),
            }
        )
    
    def calculate(
        self,
        stt_duration_sec: float = 0.0,
        llm_input_tokens: int = 0,
        llm_output_tokens: int = 0,
        tts_characters: int = 0,
        livekit_duration_sec: float = 0.0
    ) -> CostBreakdown:
        """
        Calculate cost breakdown for a call.
        
        Args:
            stt_duration_sec: Total STT processing duration in seconds
            llm_input_tokens: Total LLM input tokens
            llm_output_tokens: Total LLM output tokens
            tts_characters: Total TTS characters
            livekit_duration_sec: Total LiveKit session duration in seconds
        
        Returns:
            CostBreakdown with per-component and total costs
        """
        try:
            # STT cost: duration * rate per second
            cost_stt = (
                self.pricing.stt_per_second * Decimal(str(stt_duration_sec))
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
            # LLM cost: (input_tokens / 1M * input_rate) + (output_tokens / 1M * output_rate)
            cost_llm_input = (
                self.pricing.llm_input_per_million * 
                Decimal(str(llm_input_tokens)) / Decimal("1000000")
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
            cost_llm_output = (
                self.pricing.llm_output_per_million * 
                Decimal(str(llm_output_tokens)) / Decimal("1000000")
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
            cost_llm = cost_llm_input + cost_llm_output
            
            # TTS cost: characters / 1000 * rate per thousand
            cost_tts = (
                self.pricing.tts_per_thousand_chars * 
                Decimal(str(tts_characters)) / Decimal("1000")
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
            # LiveKit cost: duration / 60 * rate per minute
            cost_livekit = (
                self.pricing.livekit_per_minute * 
                Decimal(str(livekit_duration_sec)) / Decimal("60")
            ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            
            # Total cost
            cost_total = cost_stt + cost_llm + cost_tts + cost_livekit
            
            breakdown = CostBreakdown(
                cost_stt=cost_stt,
                cost_llm=cost_llm,
                cost_tts=cost_tts,
                cost_livekit=cost_livekit,
                cost_total=cost_total
            )
            
            logger.debug(
                "Cost calculated",
                extra={
                    "stt_duration_sec": stt_duration_sec,
                    "llm_input_tokens": llm_input_tokens,
                    "llm_output_tokens": llm_output_tokens,
                    "tts_characters": tts_characters,
                    "livekit_duration_sec": livekit_duration_sec,
                    "cost_total": float(cost_total)
                }
            )
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Failed to calculate costs: {e}", exc_info=True)
            # Return zero costs on error
            return CostBreakdown(
                cost_stt=Decimal("0"),
                cost_llm=Decimal("0"),
                cost_tts=Decimal("0"),
                cost_livekit=Decimal("0"),
                cost_total=Decimal("0")
            )
    
    def calculate_from_metrics(self, metrics: dict) -> CostBreakdown:
        """
        Calculate costs from CallMetrics dictionary.
        
        Args:
            metrics: Dictionary with metric values
        
        Returns:
            CostBreakdown with calculated costs
        """
        return self.calculate(
            stt_duration_sec=metrics.get("stt_duration_sec", 0.0),
            llm_input_tokens=metrics.get("llm_input_tokens", 0),
            llm_output_tokens=metrics.get("llm_output_tokens", 0),
            tts_characters=metrics.get("tts_characters", 0),
            livekit_duration_sec=metrics.get("livekit_duration_sec", 0.0)
        )
    
    def estimate_cost_per_minute(
        self,
        turns_per_minute: int = 10,
        avg_user_speech_sec: float = 3.0,
        avg_bot_response_chars: int = 100,
        avg_llm_tokens_per_turn: int = 200
    ) -> Decimal:
        """
        Estimate cost per minute of conversation.
        
        Args:
            turns_per_minute: Average turns per minute
            avg_user_speech_sec: Average user speech duration per turn
            avg_bot_response_chars: Average bot response length
            avg_llm_tokens_per_turn: Average LLM tokens per turn (input + output)
        
        Returns:
            Estimated cost per minute in USD
        """
        # Calculate per-turn costs
        stt_per_turn = self.pricing.stt_per_second * Decimal(str(avg_user_speech_sec))
        
        llm_per_turn = (
            self.pricing.llm_input_per_million * 
            Decimal(str(avg_llm_tokens_per_turn)) / Decimal("1000000")
        )
        
        tts_per_turn = (
            self.pricing.tts_per_thousand_chars * 
            Decimal(str(avg_bot_response_chars)) / Decimal("1000")
        )
        
        livekit_per_minute = self.pricing.livekit_per_minute
        
        # Total per minute
        cost_per_minute = (
            (stt_per_turn + llm_per_turn + tts_per_turn) * Decimal(str(turns_per_minute)) +
            livekit_per_minute
        ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        
        logger.info(
            f"Estimated cost per minute: ${float(cost_per_minute):.4f}",
            extra={
                "turns_per_minute": turns_per_minute,
                "cost_per_minute": float(cost_per_minute)
            }
        )
        
        return cost_per_minute
