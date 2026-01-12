"""
Провайдеры внешних сервисов.

- LLM (Ollama, Groq, OpenAI)
- STT (Deepgram)
- TTS (Cartesia)
- Telephony (MTS Exolve)
"""

from .ollama_llm import OllamaLLMProvider
from .groq_llm import GroqLLMProvider

__all__ = [
    "OllamaLLMProvider",
    "GroqLLMProvider",
]
