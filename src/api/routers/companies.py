"""
API для управления Companies.

Эндпоинты:
- GET /api/companies — список компаний
- POST /api/companies — создать компанию
- GET /api/companies/{id} — получить компанию
- PUT /api/companies/{id} — обновить компанию
- DELETE /api/companies/{id} — удалить компанию
"""

from uuid import UUID
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.database.connection import get_async_db
from src.database.models import Company

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class CompanyCreate(BaseModel):
    """Схема создания компании."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class CompanyUpdate(BaseModel):
    """Схема обновления компании."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class CompanyResponse(BaseModel):
    """Схема ответа компании."""
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Список компаний."""
    items: List[CompanyResponse]
    total: int


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=CompanyListResponse)
async def list_companies(
    skip: int = 0,
    limit: int = 100,
):
    """
    Получить список компаний.
    
    Параметры:
    - skip: пропустить N записей (пагинация)
    - limit: максимум записей (default: 100)
    """
    async with get_async_db() as db:
        query = select(Company).offset(skip).limit(limit).order_by(Company.name)
        result = await db.execute(query)
        companies = list(result.scalars().all())
        
        # Считаем общее количество
        count_query = select(Company)
        count_result = await db.execute(count_query)
        total = len(list(count_result.scalars().all()))
        
        return CompanyListResponse(
            items=[CompanyResponse.model_validate(c) for c in companies],
            total=total,
        )


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(data: CompanyCreate):
    """
    Создать новую компанию.
    """
    async with get_async_db() as db:
        # Проверяем уникальность имени
        existing = await db.execute(
            select(Company).where(Company.name == data.name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Company with name '{data.name}' already exists"
            )
        
        company = Company(
            name=data.name,
            description=data.description,
        )
        
        db.add(company)
        await db.commit()
        await db.refresh(company)
        
        return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID):
    """
    Получить компанию по ID.
    """
    async with get_async_db() as db:
        company = await db.get(Company, company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyResponse.model_validate(company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: UUID, data: CompanyUpdate):
    """
    Обновить компанию.
    """
    async with get_async_db() as db:
        company = await db.get(Company, company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Проверяем уникальность имени (если меняется)
        if data.name and data.name != company.name:
            existing = await db.execute(
                select(Company).where(Company.name == data.name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Company with name '{data.name}' already exists"
                )
        
        if data.name is not None:
            company.name = data.name
        if data.description is not None:
            company.description = data.description
        
        await db.commit()
        await db.refresh(company)
        
        return CompanyResponse.model_validate(company)


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: UUID):
    """
    Удалить компанию.
    
    ВНИМАНИЕ: Удаление компании удалит все связанные Skillbases, Campaigns, CallTasks (CASCADE).
    """
    async with get_async_db() as db:
        company = await db.get(Company, company_id)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        await db.delete(company)
        await db.commit()
