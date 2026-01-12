"""
Groq LLM Provider — генерация ответов через Groq API (Llama 3.1).

Groq — быстрый и бесплатный API для LLM.
Используем для MVP, потом можно переключить на свой GPU.
"""

import os
from typing import Optional
from dataclasses import dataclass

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None


@dataclass
class LLMResponse:
    """Ответ от LLM."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str


class GroqLLMProvider:
    """
    Провайдер LLM через Groq API.
    
    Использование:
        provider = GroqLLMProvider(api_key="gsk_...")
        
        response = provider.generate(
            system_prompt="Ты администратор салона красоты",
            messages=[
                {"role": "user", "content": "Хочу записаться"}
            ]
        )
        print(response)  # "Конечно! На какой день хотите записаться?"
    """
    
    # Доступные модели Groq
    MODELS = {
        "llama-3.1-70b": "llama-3.1-70b-versatile",      # Большая, умная
        "llama-3.1-8b": "llama-3.1-8b-instant",          # Быстрая, лёгкая
        "llama-3.2-90b": "llama-3.2-90b-vision-preview", # Самая большая
        "mixtral": "mixtral-8x7b-32768",                  # Mixtral
    }
    
    DEFAULT_MODEL = "llama-3.1-8b-instant"  # Быстрая для MVP
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 150
    ):
        """
        Args:
            api_key: Groq API ключ. Если не указан — берётся из GROQ_API_KEY
            model: Модель для генерации
            temperature: Креативность (0-1)
            max_tokens: Максимум токенов в ответе
        """
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq не установлен. Выполните: pip install groq"
            )
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API ключ не указан. Передайте api_key или установите GROQ_API_KEY"
            )
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Создаём клиент
        self.client = Groq(api_key=self.api_key)
    
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Сгенерировать ответ.
        
        Args:
            system_prompt: Системный промпт (роль бота)
            messages: История сообщений [{"role": "user/assistant", "content": "..."}]
            max_tokens: Лимит токенов (опционально)
            temperature: Креативность (опционально)
            
        Returns:
            Текст ответа
        """
        # Формируем сообщения для API
        api_messages = [
            {"role": "system", "content": system_prompt}
        ]
        api_messages.extend(messages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Логируем ошибку и возвращаем fallback
            print(f"[GroqLLM] Ошибка: {e}")
            return self._fallback_response(messages)
    
    def generate_with_details(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Сгенерировать ответ с деталями (токены, модель).
        """
        api_messages = [
            {"role": "system", "content": system_prompt}
        ]
        api_messages.extend(messages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
            )
            
            choice = response.choices[0]
            
            return LLMResponse(
                text=choice.message.content.strip(),
                model=response.model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=choice.finish_reason or "unknown"
            )
            
        except Exception as e:
            print(f"[GroqLLM] Ошибка: {e}")
            return LLMResponse(
                text=self._fallback_response(messages),
                model="fallback",
                tokens_used=0,
                finish_reason="error"
            )
    
    def _fallback_response(self, messages: list[dict]) -> str:
        """Fallback ответ при ошибке API."""
        # Определяем язык по последнему сообщению
        last_msg = messages[-1]["content"] if messages else ""
        is_russian = any(c in last_msg for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        
        if is_russian:
            return "Извините, произошла ошибка. Повторите, пожалуйста."
        return "Sorry, an error occurred. Please repeat."
    
    def set_model(self, model: str) -> None:
        """Сменить модель."""
        if model in self.MODELS:
            self.model = self.MODELS[model]
        else:
            self.model = model
    
    def test_connection(self) -> bool:
        """Проверить подключение к API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a test bot."},
                    {"role": "user", "content": "Say OK"}
                ],
                max_tokens=10
            )
            return len(response.choices[0].message.content) > 0
        except Exception as e:
            print(f"[GroqLLM] Ошибка подключения: {e}")
            return False
