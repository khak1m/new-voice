"""
Embeddings — преобразование текста в векторы.

Используем sentence-transformers для мультиязычных эмбеддингов.
Модель работает локально, не требует API ключей.
"""

import os
from typing import Protocol, Optional
from abc import abstractmethod


class EmbeddingProvider(Protocol):
    """Интерфейс для провайдера эмбеддингов."""
    
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Получить эмбеддинг для текста."""
        ...
    
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Получить эмбеддинги для списка текстов."""
        ...
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Размерность эмбеддингов."""
        ...


class SentenceTransformerProvider:
    """
    Провайдер эмбеддингов на базе sentence-transformers.
    
    Модель по умолчанию: paraphrase-multilingual-MiniLM-L12-v2
    - Поддерживает 50+ языков включая русский
    - Размерность: 384
    - Быстрая и лёгкая
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Инициализация провайдера.
        
        Args:
            model_name: Название модели (по умолчанию из env или multilingual)
        """
        self.model_name = model_name or os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self._model = None
        self._dimension = 384  # Для MiniLM
    
    def _load_model(self):
        """Ленивая загрузка модели."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"[RAG] Загружаю модель эмбеддингов: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                print(f"[RAG] Модель загружена, размерность: {self._dimension}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers не установлен. "
                    "Выполни: pip install sentence-transformers"
                )
    
    def embed(self, text: str) -> list[float]:
        """Получить эмбеддинг для текста."""
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Получить эмбеддинги для списка текстов."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]
    
    @property
    def dimension(self) -> int:
        """Размерность эмбеддингов."""
        return self._dimension


class SimpleEmbeddingProvider:
    """
    Простой провайдер для тестирования (без ML модели).
    
    Генерирует псевдо-эмбеддинги на основе хэша текста.
    НЕ использовать в продакшене!
    """
    
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
    
    def embed(self, text: str) -> list[float]:
        """Псевдо-эмбеддинг на основе хэша."""
        import hashlib
        
        # Хэшируем текст
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        # Преобразуем в числа от -1 до 1
        result = []
        for i in range(self._dimension):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] / 127.5) - 1.0
            result.append(value)
        
        return result
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension


# =============================================================================
# Фабрика
# =============================================================================

_provider_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider(use_simple: bool = False) -> EmbeddingProvider:
    """
    Получить провайдер эмбеддингов (singleton).
    
    Args:
        use_simple: Использовать простой провайдер (для тестов)
    """
    global _provider_instance
    
    if _provider_instance is None:
        if use_simple:
            _provider_instance = SimpleEmbeddingProvider()
        else:
            _provider_instance = SentenceTransformerProvider()
    
    return _provider_instance
