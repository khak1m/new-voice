"""
Ollama LLM Provider — локальный LLM на сервере.

Ollama позволяет запускать LLM (Llama, Mistral и др.) локально.
Работает без блокировок, бесплатно, полный контроль.

Установка на сервере:
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull llama3.1:8b
"""

import os
from typing import Optional
from dataclasses import dataclass

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@dataclass
class LLMResponse:
    """Ответ от LLM."""
    text: str
    model: str
    tokens_used: int
    finish_reason: str


class OllamaLLMProvider:
    """
    Провайдер LLM через Ollama (локальный сервер).
    
    Использование:
        provider = OllamaLLMProvider(host="http://77.233.212.58:11434")
        
        response = provider.generate(
            system_prompt="Ты администратор салона красоты",
            messages=[
                {"role": "user", "content": "Хочу записаться"}
            ]
        )
        print(response)  # "Конечно! На какой день хотите записаться?"
    """
    
    # Рекомендуемые модели для разных задач
    MODELS = {
        "llama3.1:8b": "Llama 3.1 8B — быстрая, хорошее качество",
        "llama3.1:70b": "Llama 3.1 70B — умная, требует много RAM",
        "mistral:7b": "Mistral 7B — быстрая альтернатива",
        "qwen2:7b": "Qwen2 7B — хорошо работает с русским",
    }
    
    DEFAULT_MODEL = "llama3.1:8b"
    
    def __init__(
        self, 
        host: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 150
    ):
        """
        Args:
            host: URL Ollama сервера. По умолчанию localhost:11434
            model: Модель для генерации
            temperature: Креативность (0-1)
            max_tokens: Максимум токенов в ответе
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx не установлен. Выполните: pip install httpx")
        
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Убираем trailing slash
        self.host = self.host.rstrip("/")
    
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
        # Формируем сообщения для API (OpenAI-совместимый формат)
        api_messages = [
            {"role": "system", "content": system_prompt}
        ]
        api_messages.extend(messages)
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature or self.temperature,
                            "num_predict": max_tokens or self.max_tokens,
                        }
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
                
        except httpx.ConnectError:
            print(f"[Ollama] Не удалось подключиться к {self.host}")
            print("[Ollama] Убедитесь что Ollama запущен: ollama serve")
            return self._fallback_response(messages)
        except Exception as e:
            print(f"[Ollama] Ошибка: {e}")
            return self._fallback_response(messages)
    
    def generate_with_details(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """Сгенерировать ответ с деталями."""
        api_messages = [
            {"role": "system", "content": system_prompt}
        ]
        api_messages.extend(messages)
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": api_messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature or self.temperature,
                            "num_predict": max_tokens or self.max_tokens,
                        }
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                return LLMResponse(
                    text=data.get("message", {}).get("content", "").strip(),
                    model=data.get("model", self.model),
                    tokens_used=data.get("eval_count", 0),
                    finish_reason=data.get("done_reason", "stop")
                )
                
        except Exception as e:
            print(f"[Ollama] Ошибка: {e}")
            return LLMResponse(
                text=self._fallback_response(messages),
                model="fallback",
                tokens_used=0,
                finish_reason="error"
            )
    
    def _fallback_response(self, messages: list[dict]) -> str:
        """Fallback ответ при ошибке."""
        last_msg = messages[-1]["content"] if messages else ""
        is_russian = any(c in last_msg for c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
        
        if is_russian:
            return "Извините, произошла ошибка. Повторите, пожалуйста."
        return "Sorry, an error occurred. Please repeat."
    
    def test_connection(self) -> bool:
        """Проверить подключение к Ollama."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> list[str]:
        """Получить список установленных моделей."""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
    
    def pull_model(self, model: str) -> bool:
        """Скачать модель (может занять время)."""
        try:
            with httpx.Client(timeout=600.0) as client:  # 10 минут на скачивание
                response = client.post(
                    f"{self.host}/api/pull",
                    json={"name": model, "stream": False}
                )
                return response.status_code == 200
        except Exception as e:
            print(f"[Ollama] Ошибка скачивания модели: {e}")
            return False
    
    def set_model(self, model: str) -> None:
        """Сменить модель."""
        self.model = model
