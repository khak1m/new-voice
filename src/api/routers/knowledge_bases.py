"""
API для управления базами знаний.

Эндпоинты:
- GET /api/knowledge-bases — список баз знаний
- POST /api/knowledge-bases — создать базу знаний
- GET /api/knowledge-bases/{id} — получить базу знаний
- PUT /api/knowledge-bases/{id} — обновить базу знаний (нужно фронту)
- DELETE /api/knowledge-bases/{id} — удалить базу знаний
- POST /api/knowledge-bases/{id}/documents — добавить документ
- DELETE /api/knowledge-bases/{id}/documents/{docId} — удалить документ (нужно фронту)
- POST /api/knowledge-bases/{id}/search — поиск по базе знаний
"""

from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import KnowledgeBase, Document, Company
from src.rag import KnowledgeBaseManager, RAGSearch

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================


class KnowledgeBaseCreate(BaseModel):
    """Схема создания базы знаний."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    # Frontend может прислать UUID или slug (например "default-company")
    company_id: str


class KnowledgeBaseUpdate(BaseModel):
    """Схема обновления базы знаний."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    """Схема ответа базы знаний."""

    id: UUID
    name: str
    description: Optional[str]
    company_id: UUID
    document_count: int
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """Схема добавления документа."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source_type: str = "text"


class DocumentResponse(BaseModel):
    """Схема ответа документа."""

    id: UUID
    title: str
    source_type: str
    chunk_count: int
    is_indexed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Запрос на поиск."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchResultItem(BaseModel):
    """Результат поиска."""

    content: str
    score: float
    title: str


class SearchResponse(BaseModel):
    """Ответ поиска."""

    results: list[SearchResultItem]
    query: str


# =============================================================================
# Эндпоинты
# =============================================================================


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(company_id: Optional[UUID] = None):
    """Получить список баз знаний."""
    async with get_async_db() as db:
        query = select(KnowledgeBase)

        if company_id:
            query = query.where(KnowledgeBase.company_id == company_id)

        result = await db.execute(query)
        kbs = result.scalars().all()

        return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(data: KnowledgeBaseCreate):
    """Создать базу знаний."""
    async with get_async_db() as db:
        from src.services.company_utils import resolve_company

        try:
            company = await resolve_company(
                db, data.company_id, default_name="Default Company"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Создаём в PostgreSQL
        kb_id = uuid4()
        collection_name = f"kb_{kb_id.hex[:8]}"

        kb = KnowledgeBase(
            id=kb_id,
            name=data.name,
            description=data.description,
            company_id=company.id,
            qdrant_collection=collection_name,
        )

        db.add(kb)
        await db.commit()
        await db.refresh(kb)

        # Создаём коллекцию в Qdrant
        try:
            manager = KnowledgeBaseManager()
            manager.create_collection(collection_name)
        except Exception as e:
            # Откатываем если Qdrant недоступен
            await db.delete(kb)
            await db.commit()
            raise HTTPException(
                status_code=500, detail=f"Failed to create Qdrant collection: {e}"
            )

        return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: UUID):
    """Получить базу знаний."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        return KnowledgeBaseResponse.model_validate(kb)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(kb_id: UUID, data: KnowledgeBaseUpdate):
    """Обновить базу знаний (нужно фронту)."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kb, field, value)

        await db.commit()
        await db.refresh(kb)
        return KnowledgeBaseResponse.model_validate(kb)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: UUID):
    """Удалить базу знаний."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # Удаляем коллекцию из Qdrant
        if kb.qdrant_collection:
            try:
                manager = KnowledgeBaseManager()
                manager.delete_collection(kb.qdrant_collection)
            except Exception:
                pass  # Игнорируем ошибки Qdrant

        await db.delete(kb)
        await db.commit()


@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=201)
async def add_document(kb_id: UUID, data: DocumentCreate):
    """Добавить документ в базу знаний."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # Создаём документ в PostgreSQL
        doc = Document(
            knowledge_base_id=kb_id,
            title=data.title,
            content=data.content,
            source_type=data.source_type,
        )

        db.add(doc)

        # Индексируем в Qdrant
        try:
            manager = KnowledgeBaseManager()
            chunk_count = manager.add_text(
                collection_name=kb.qdrant_collection,
                text=data.content,
                title=data.title,
                metadata={"document_id": str(doc.id)},
            )

            doc.is_indexed = True
            doc.chunk_count = chunk_count

            # Обновляем счётчики базы знаний
            kb.document_count = (kb.document_count or 0) + 1
            kb.chunk_count = (kb.chunk_count or 0) + chunk_count

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to index document: {e}"
            )

        await db.commit()
        await db.refresh(doc)

        return DocumentResponse.model_validate(doc)


@router.get("/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(kb_id: UUID):
    """Получить список документов базы знаний."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        result = await db.execute(
            select(Document).where(Document.knowledge_base_id == kb_id)
        )
        docs = result.scalars().all()

        return [DocumentResponse.model_validate(doc) for doc in docs]


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
async def delete_document(kb_id: UUID, doc_id: UUID):
    """Удалить документ из базы знаний (нужно фронту)."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        doc = await db.get(Document, doc_id)
        if not doc or doc.knowledge_base_id != kb_id:
            raise HTTPException(status_code=404, detail="Document not found")

        # Try to delete from Qdrant (best-effort)
        if kb.qdrant_collection:
            try:
                manager = KnowledgeBaseManager()
                manager.delete_document(
                    collection_name=kb.qdrant_collection, document_id=str(doc_id)
                )
            except Exception:
                pass

        # Update counters (best-effort)
        try:
            kb.document_count = max(0, (kb.document_count or 0) - 1)
            kb.chunk_count = max(0, (kb.chunk_count or 0) - (doc.chunk_count or 0))
        except Exception:
            pass

        await db.delete(doc)
        await db.commit()


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search_knowledge_base(kb_id: UUID, data: SearchRequest):
    """Поиск по базе знаний."""
    async with get_async_db() as db:
        kb = await db.get(KnowledgeBase, kb_id)

        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        if not kb.qdrant_collection:
            raise HTTPException(status_code=400, detail="Knowledge base not indexed")

        # Поиск
        try:
            rag = RAGSearch()
            results = rag.search(
                collection_name=kb.qdrant_collection,
                query=data.query,
                top_k=data.top_k,
            )

            return SearchResponse(
                query=data.query,
                results=[
                    SearchResultItem(
                        content=r.content,
                        score=r.score,
                        title=r.metadata.get("title", ""),
                    )
                    for r in results
                ],
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")
