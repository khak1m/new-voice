"""
RAG Search — поиск с генерацией ответа.

Объединяет:
1. Поиск релевантных документов в Qdrant
2. Формирование контекста для LLM
3. Генерация ответа
"""

import os
from typing import Optional, Protocol
from dataclasses import dataclass

from .knowledge_base import KnowledgeBaseManager, SearchResult


class LLMProvider(Protocol):
    """Интерфейс для LLM провайдера."""
    
    def generate(self, prompt: str, max_tokens: int = 200) -> str:
        """Сгенерировать ответ."""
        ...


@dataclass
class RAGResponse:
    """Ответ RAG системы."""
    answer: str
    sources: list[SearchResult]
    has_answer: bool


class RAGSearch:
    """
    RAG поиск с генерацией ответа.
    
    Использование:
        rag = RAGSearch(kb_manager)
        
        # Простой поиск
        results = rag.search("salon_kb", "сколько стоит маникюр")
        
        # Поиск с генерацией ответа (нужен LLM)
        rag.set_llm(ollama_provider)
        response = rag.ask("salon_kb", "сколько стоит маникюр")
        print(response.answer)
    """
    
    def __init__(
        self,
        kb_manager: Optional[KnowledgeBaseManager] = None,
        llm: Optional[LLMProvider] = None,
    ):
        """
        Инициализация.
        
        Args:
            kb_manager: Менеджер базы знаний
            llm: LLM провайдер для генерации ответов
        """
        self.kb = kb_manager or KnowledgeBaseManager()
        self._llm = llm
        
        # Настройки
        self.top_k = int(os.getenv("RAG_TOP_K", "3"))
        self.min_score = float(os.getenv("RAG_MIN_SCORE", "0.5"))
    
    def set_llm(self, llm: LLMProvider) -> None:
        """Установить LLM провайдер."""
        self._llm = llm
    
    def search(
        self,
        collection_name: str,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> list[SearchResult]:
        """
        Поиск релевантных документов.
        
        Args:
            collection_name: Название коллекции
            query: Поисковый запрос
            top_k: Количество результатов
            min_score: Минимальный score
            
        Returns:
            Список результатов поиска
        """
        return self.kb.search(
            collection_name=collection_name,
            query=query,
            top_k=top_k or self.top_k,
            min_score=min_score or self.min_score,
        )
    
    def ask(
        self,
        collection_name: str,
        question: str,
        top_k: Optional[int] = None,
        language: str = "ru",
    ) -> RAGResponse:
        """
        Задать вопрос и получить ответ на основе базы знаний.
        
        Args:
            collection_name: Название коллекции
            question: Вопрос пользователя
            top_k: Количество документов для контекста
            language: Язык ответа
            
        Returns:
            RAGResponse с ответом и источниками
        """
        # Ищем релевантные документы
        results = self.search(
            collection_name=collection_name,
            query=question,
            top_k=top_k,
        )
        
        if not results:
            return RAGResponse(
                answer=self._no_answer_message(language),
                sources=[],
                has_answer=False,
            )
        
        # Если нет LLM — возвращаем лучший результат как есть
        if self._llm is None:
            best = results[0]
            return RAGResponse(
                answer=best.content,
                sources=results,
                has_answer=True,
            )
        
        # Формируем контекст для LLM
        context = self._build_context(results)
        prompt = self._build_prompt(question, context, language)
        
        # Генерируем ответ
        answer = self._llm.generate(prompt, max_tokens=200)
        
        return RAGResponse(
            answer=answer,
            sources=results,
            has_answer=True,
        )
    
    def get_context_for_llm(
        self,
        collection_name: str,
        question: str,
        top_k: Optional[int] = None,
    ) -> str:
        """
        Получить контекст из базы знаний для добавления в промпт LLM.
        
        Используется для интеграции с Voice Agent.
        
        Args:
            collection_name: Название коллекции
            question: Вопрос пользователя
            top_k: Количество документов
            
        Returns:
            Текст контекста или пустая строка
        """
        results = self.search(
            collection_name=collection_name,
            query=question,
            top_k=top_k,
        )
        
        if not results:
            return ""
        
        return self._build_context(results)
    
    # =========================================================================
    # Вспомогательные методы
    # =========================================================================
    
    def _build_context(self, results: list[SearchResult]) -> str:
        """Построить контекст из результатов поиска."""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            title = result.metadata.get("title", "Документ")
            context_parts.append(f"[{i}] {title}:\n{result.content}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(
        self,
        question: str,
        context: str,
        language: str,
    ) -> str:
        """Построить промпт для LLM."""
        
        if language == "ru":
            return f"""Ответь на вопрос пользователя, используя только информацию из контекста ниже.
Если в контексте нет ответа — скажи что не знаешь.
Отвечай кратко, 1-2 предложения.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ОТВЕТ:"""
        else:
            return f"""Answer the user's question using only the information from the context below.
If the context doesn't contain the answer, say you don't know.
Keep your answer brief, 1-2 sentences.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    def _no_answer_message(self, language: str) -> str:
        """Сообщение когда ответ не найден."""
        if language == "ru":
            return "К сожалению, у меня нет информации по этому вопросу."
        return "I'm sorry, I don't have information about that."
