"""
NEW-VOICE 2.0 - Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    # Speech-to-Text
    deepgram_api_key: str = ""
    
    # Text-to-Speech
    cartesia_api_key: str = ""
    
    # LiveKit
    livekit_url: str = "ws://localhost:7880"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    
    # Telephony
    exolve_api_key: str = ""
    exolve_phone_number: str = ""
    
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
