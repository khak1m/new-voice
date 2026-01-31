"""
TTS Router - Text-to-Speech preview endpoints.

Provides endpoints for generating TTS audio previews.
"""

import io
import math
import wave

from typing import Optional

from fastapi import APIRouter, HTTPException, Response, Query
from pydantic import BaseModel, Field, validator
from typing import Literal

from src.services import get_tts_service, TTSError


router = APIRouter()


def _generate_fallback_wav(text: str, sample_rate: int = 22050) -> bytes:
    """Generate a short WAV tone as a safe fallback.

    We use WAV because it can be generated without external dependencies.
    Duration is derived from text length to feel "preview-like".
    """

    # 0.6s .. 6s based on text length
    duration_sec = max(0.6, min(6.0, len(text) * 0.03))
    freq_hz = 440.0
    frames = int(sample_rate * duration_sec)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        # Simple fade-in/fade-out to avoid clicks
        fade_frames = max(1, int(sample_rate * 0.02))

        for i in range(frames):
            t = i / sample_rate
            sample = math.sin(2 * math.pi * freq_hz * t)

            # Apply fade
            if i < fade_frames:
                sample *= i / fade_frames
            elif i > frames - fade_frames:
                sample *= max(0.0, (frames - i) / fade_frames)

            # Scale to int16
            v = int(sample * 32767)
            wf.writeframesraw(v.to_bytes(2, byteorder="little", signed=True))

    return buf.getvalue()


class TTSPreviewRequest(BaseModel):
    """Request model for TTS preview."""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Text to convert to speech"
    )
    voice_id: str = Field(default="sasha_v1", min_length=1, description="Voice ID")
    language: str = Field(default="ru", description="Language code (ru, en)")
    output_format: Literal["mp3", "wav"] = Field(
        default="mp3", description="Audio format"
    )

    @validator("text")
    def validate_text(cls, v):
        """Validate text is not empty after stripping."""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()

    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        allowed_languages = ["ru", "en", "es", "fr", "de", "it", "pt", "pl", "uk"]
        if v not in allowed_languages:
            raise ValueError(f"Language must be one of: {', '.join(allowed_languages)}")
        return v


@router.post("/preview")
async def preview_tts(request: TTSPreviewRequest):
    """
    Generate TTS audio preview.

    Args:
        request: TTS preview request with text, voice_id, language, format

    Returns:
        Audio file (mp3 or wav)

    Raises:
        400: Invalid request (validation errors)
        500: TTS generation failed
    """
    try:
        # Try real provider first
        tts_service = get_tts_service()

        audio_bytes = await tts_service.generate_audio(
            text=request.text,
            voice_id=request.voice_id,
            language=request.language,
            output_format=request.output_format,
        )

        content_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"

        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="preview.{request.output_format}"',
                "Cache-Control": "no-cache",
            },
        )

    except TTSError:
        # Fallback: always return WAV tone (keeps frontend functional)
        audio_bytes = _generate_fallback_wav(request.text)
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'inline; filename="preview.wav"',
                "Cache-Control": "no-cache",
            },
        )
    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/voices")
async def list_tts_voices(language: Optional[str] = Query(default=None)):
    """Return available voices (simple static list).

    Frontend uses this to populate voice dropdowns.
    """
    from src.schemas.skillbase_schemas import AVAILABLE_VOICES

    if language:
        # Current voice list doesn't carry language, so we just return all.
        return {"voices": AVAILABLE_VOICES, "language": language}

    return {"voices": AVAILABLE_VOICES}
