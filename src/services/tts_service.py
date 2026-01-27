"""
TTS Service - Text-to-Speech generation service.

Provides abstraction layer for TTS providers (Cartesia, ElevenLabs, etc.)
"""

import os
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TTSError(Exception):
    """Base exception for TTS errors."""
    pass


class CartesiaTTSProvider:
    """Cartesia TTS provider implementation."""
    
    def __init__(self, api_key: str):
        """
        Initialize Cartesia TTS provider.
        
        Args:
            api_key: Cartesia API key
        """
        self.api_key = api_key
        self.base_url = "https://api.cartesia.ai"
        self.api_version = "2024-11-13"
    
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        language: str = "ru",
        output_format: str = "mp3"
    ) -> bytes:
        """
        Synthesize speech from text using Cartesia API.
        
        Args:
            text: Text to convert to speech
            voice_id: Cartesia voice ID
            language: Language code (ru, en, etc.)
            output_format: Audio format (mp3, wav)
            
        Returns:
            Audio bytes
            
        Raises:
            TTSError: If synthesis fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Cartesia API endpoint for TTS
                url = f"{self.base_url}/tts/bytes"
                
                headers = {
                    "X-API-Key": self.api_key,
                    "Cartesia-Version": self.api_version,
                    "Content-Type": "application/json"
                }
                
                # Request payload
                payload = {
                    "model_id": "sonic-2",
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": voice_id
                    },
                    "language": language,
                    "output_format": {
                        "container": output_format,
                        "encoding": "pcm_f32le" if output_format == "wav" else "mp3",
                        "sample_rate": 44100
                    }
                }
                
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    return response.content
                else:
                    error_msg = f"Cartesia API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg += f" - {error_data.get('error', response.text[:100])}"
                    except:
                        error_msg += f" - {response.text[:100]}"
                    
                    raise TTSError(error_msg)
                    
        except httpx.TimeoutException:
            raise TTSError("TTS request timed out")
        except httpx.RequestError as e:
            raise TTSError(f"TTS request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, TTSError):
                raise
            raise TTSError(f"Unexpected error during TTS synthesis: {str(e)}")


class TTSService:
    """Service for text-to-speech generation."""
    
    def __init__(self, provider: str = "cartesia", api_key: Optional[str] = None):
        """
        Initialize TTS service.
        
        Args:
            provider: TTS provider name (currently only "cartesia" supported)
            api_key: API key for the provider (if None, reads from env)
        """
        self.provider = provider
        
        if provider == "cartesia":
            if api_key is None:
                api_key = os.getenv("CARTESIA_API_KEY")
                if not api_key:
                    raise ValueError("CARTESIA_API_KEY not found in environment")
            
            self.client = CartesiaTTSProvider(api_key)
        else:
            raise ValueError(f"Unsupported TTS provider: {provider}")
    
    async def generate_audio(
        self,
        text: str,
        voice_id: str,
        language: str = "ru",
        output_format: str = "mp3"
    ) -> bytes:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice identifier
            language: Language code (ru, en)
            output_format: Audio format (mp3, wav)
            
        Returns:
            Audio bytes
            
        Raises:
            TTSError: If generation fails
        """
        if not text or not text.strip():
            raise TTSError("Text cannot be empty")
        
        if len(text) > 5000:
            raise TTSError("Text too long (max 5000 characters)")
        
        return await self.client.synthesize(
            text=text,
            voice_id=voice_id,
            language=language,
            output_format=output_format
        )


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """
    Get singleton TTS service instance.
    
    Returns:
        TTSService instance
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
