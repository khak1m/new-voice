"""
RAG (Retrieval-Augmented Generation) модуль.

Позволяет боту отвечать на вопросы из базы знаний клиента.
"""

from .knowledge_base import KnowledgeBaseManager
from .embeddings import EmbeddingProvider, get_embedding_provider
from .search import RAGSearch

__all__ = [
    "KnowledgeBaseManager",
    "EmbeddingProvider",
    "get_embedding_provider",
    "RAGSearch",
]
