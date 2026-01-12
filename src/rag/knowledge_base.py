"""
Knowledge Base Manager — управление базами знаний.

Функции:
- Создание коллекций в Qdrant
- Загрузка документов (текст, файлы)
- Разбиение на чанки
- Индексация в Qdrant
"""

import os
import uuid
import hashlib
from typing import Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from .embeddings import get_embedding_provider, EmbeddingProvider


@dataclass
class Document:
    """Документ для индексации."""
    id: str
    title: str
    content: str
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Chunk:
    """Чанк документа."""
    id: str
    document_id: str
    content: str
    metadata: dict


@dataclass
class SearchResult:
    """Результат поиска."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict


class KnowledgeBaseManager:
    """
    Менеджер базы знаний.
    
    Использование:
        manager = KnowledgeBaseManager()
        
        # Создать базу знаний
        manager.create_collection("salon_kb")
        
        # Добавить документы
        manager.add_document("salon_kb", Document(
            id="price",
            title="Прайс-лист",
            content="Маникюр - 1500 руб. Педикюр - 2000 руб..."
        ))
        
        # Поиск
        results = manager.search("salon_kb", "сколько стоит маникюр")
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        """
        Инициализация менеджера.
        
        Args:
            host: Хост Qdrant (по умолчанию из env или localhost)
            port: Порт Qdrant (по умолчанию 6333)
            embedding_provider: Провайдер эмбеддингов
        """
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        
        self.client = QdrantClient(host=self.host, port=self.port)
        self.embeddings = embedding_provider or get_embedding_provider()
        
        # Настройки чанкинга
        self.chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "500"))
        self.chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
    
    # =========================================================================
    # Коллекции
    # =========================================================================
    
    def create_collection(self, name: str) -> bool:
        """
        Создать коллекцию в Qdrant.
        
        Args:
            name: Название коллекции
            
        Returns:
            True если создана, False если уже существует
        """
        # Проверяем существование
        collections = self.client.get_collections().collections
        if any(c.name == name for c in collections):
            print(f"[RAG] Коллекция '{name}' уже существует")
            return False
        
        # Создаём
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=self.embeddings.dimension,
                distance=Distance.COSINE,
            ),
        )
        print(f"[RAG] Создана коллекция '{name}'")
        return True
    
    def delete_collection(self, name: str) -> bool:
        """Удалить коллекцию."""
        try:
            self.client.delete_collection(name)
            print(f"[RAG] Удалена коллекция '{name}'")
            return True
        except Exception as e:
            print(f"[RAG] Ошибка удаления коллекции: {e}")
            return False
    
    def collection_exists(self, name: str) -> bool:
        """Проверить существование коллекции."""
        collections = self.client.get_collections().collections
        return any(c.name == name for c in collections)
    
    # =========================================================================
    # Документы
    # =========================================================================
    
    def add_document(
        self,
        collection_name: str,
        document: Document,
    ) -> int:
        """
        Добавить документ в базу знаний.
        
        Args:
            collection_name: Название коллекции
            document: Документ для добавления
            
        Returns:
            Количество добавленных чанков
        """
        # Создаём коллекцию если не существует
        if not self.collection_exists(collection_name):
            self.create_collection(collection_name)
        
        # Разбиваем на чанки
        chunks = self._split_into_chunks(document)
        
        if not chunks:
            print(f"[RAG] Документ '{document.title}' пустой")
            return 0
        
        # Получаем эмбеддинги
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embeddings.embed_batch(texts)
        
        # Создаём точки для Qdrant
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point = PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "title": document.title,
                    **chunk.metadata,
                },
            )
            points.append(point)
        
        # Загружаем в Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )
        
        print(f"[RAG] Добавлен документ '{document.title}': {len(chunks)} чанков")
        return len(chunks)
    
    def add_text(
        self,
        collection_name: str,
        text: str,
        title: str = "Документ",
        metadata: dict = None,
    ) -> int:
        """
        Добавить текст в базу знаний (упрощённый метод).
        
        Args:
            collection_name: Название коллекции
            text: Текст документа
            title: Заголовок
            metadata: Дополнительные метаданные
        """
        doc = Document(
            id=str(uuid.uuid4()),
            title=title,
            content=text,
            metadata=metadata or {},
        )
        return self.add_document(collection_name, doc)
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Удалить документ из коллекции."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            )
            print(f"[RAG] Удалён документ '{document_id}'")
            return True
        except Exception as e:
            print(f"[RAG] Ошибка удаления документа: {e}")
            return False
    
    # =========================================================================
    # Поиск
    # =========================================================================
    
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3,
        min_score: float = 0.5,
    ) -> list[SearchResult]:
        """
        Поиск по базе знаний.
        
        Args:
            collection_name: Название коллекции
            query: Поисковый запрос
            top_k: Количество результатов
            min_score: Минимальный score для фильтрации
            
        Returns:
            Список результатов поиска
        """
        if not self.collection_exists(collection_name):
            print(f"[RAG] Коллекция '{collection_name}' не найдена")
            return []
        
        # Получаем эмбеддинг запроса
        query_embedding = self.embeddings.embed(query)
        
        # Ищем в Qdrant
        results = self.client.query_points(
            collection_name=collection_name,
            query=query_embedding,
            limit=top_k,
        ).points
        
        # Фильтруем и форматируем
        search_results = []
        for result in results:
            if result.score >= min_score:
                search_results.append(SearchResult(
                    chunk_id=str(result.id),
                    document_id=result.payload.get("document_id", ""),
                    content=result.payload.get("content", ""),
                    score=result.score,
                    metadata={
                        k: v for k, v in result.payload.items()
                        if k not in ("document_id", "content")
                    },
                ))
        
        return search_results
    
    # =========================================================================
    # Вспомогательные методы
    # =========================================================================
    
    def _split_into_chunks(self, document: Document) -> list[Chunk]:
        """Разбить документ на чанки."""
        text = document.content.strip()
        
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Определяем конец чанка
            end = start + self.chunk_size
            
            # Пытаемся найти конец предложения
            if end < len(text):
                # Ищем точку, вопрос или восклицательный знак
                for sep in [". ", "? ", "! ", "\n"]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break
            
            # Извлекаем чанк
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_id = hashlib.md5(
                    f"{document.id}:{chunk_index}".encode()
                ).hexdigest()
                
                chunks.append(Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    content=chunk_text,
                    metadata={
                        "chunk_index": chunk_index,
                        **document.metadata,
                    },
                ))
                chunk_index += 1
            
            # Сдвигаем с учётом overlap
            start = end - self.chunk_overlap
            if start <= 0 or start >= len(text):
                break
        
        return chunks
    
    def get_collection_info(self, name: str) -> dict:
        """Получить информацию о коллекции."""
        try:
            info = self.client.get_collection(name)
            return {
                "name": name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            return {"error": str(e)}
