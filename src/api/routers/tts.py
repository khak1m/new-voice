"""
TTS Router - Text-to-Speech preview endpoints.

Provides endpoints for generating TTS audio previews.
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, validator
from typing import Literal

from src.services import get_tts_service, TTSError


router = APIRouter()


class TTSPreviewRequest(BaseModel):
    """Request model for TTS preview."""
    
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice_id: str = Field(..., min_length=1, description="Cartesia voice ID")
    language: str = Field(default="ru", description="Language code (ru, en)")
    output_format: Literal["mp3", "wav"] = Field(default="mp3", description="Audio format")
    
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
        # Get TTS service
        tts_service = get_tts_service()
        
        # Generate audio
        audio_bytes = await tts_service.generate_audio(
            text=request.text,
            voice_id=request.voice_id,
            language=request.language,
            output_format=request.output_format
        )
        
        # Determine content type
        content_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"
        
        # Return audio response
        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f'inline; filename="preview.{request.output_format}"',
                "Cache-Control": "no-cache"
            }
        )
        
    except TTSError as e:
        # TTS service errors (API failures, timeouts, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )
    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
