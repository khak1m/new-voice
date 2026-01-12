"""
API для управления лидами.

Эндпоинты:
- GET /api/leads — список лидов
- GET /api/leads/{id} — получить лид
- PUT /api/leads/{id} — обновить статус лида
- GET /api/leads/export — экспорт лидов
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Lead

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class LeadResponse(BaseModel):
    """Схема ответа лида."""
    id: UUID
    call_id: Optional[UUID]
    bot_id: Optional[UUID]
    company_id: Optional[UUID]
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    data: dict
    status: str
    notes: Optional[str]
    webhook_sent: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Список лидов."""
    items: list[LeadResponse]
    total: int


class LeadUpdate(BaseModel):
    """Схема обновления лида."""
    status: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=LeadListResponse)
async def list_leads(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Получить список лидов."""
    async with get_async_db() as db:
        query = select(Lead).order_by(desc(Lead.created_at))
        
        if company_id:
            query = query.where(Lead.company_id == company_id)
        if bot_id:
            query = query.where(Lead.bot_id == bot_id)
        if status:
            query = query.where(Lead.status == status)
        
        # Считаем общее количество
        count_query = select(Lead)
        if company_id:
            count_query = count_query.where(Lead.company_id == company_id)
        if bot_id:
            count_query = count_query.where(Lead.bot_id == bot_id)
        if status:
            count_query = count_query.where(Lead.status == status)
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Получаем страницу
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        leads = result.scalars().all()
        
        return LeadListResponse(
            items=[LeadResponse.model_validate(lead) for lead in leads],
            total=total,
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: UUID):
    """Получить лид по ID."""
    async with get_async_db() as db:
        lead = await db.get(Lead, lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return LeadResponse.model_validate(lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: UUID, data: LeadUpdate):
    """Обновить лид (статус, заметки)."""
    async with get_async_db() as db:
        lead = await db.get(Lead, lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Обновляем поля
        if data.status is not None:
            lead.status = data.status
        if data.notes is not None:
            lead.notes = data.notes
        
        await db.commit()
        await db.refresh(lead)
        
        return LeadResponse.model_validate(lead)


@router.get("/stats/summary")
async def get_leads_stats(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
):
    """Получить статистику по лидам."""
    async with get_async_db() as db:
        query = select(Lead)
        
        if company_id:
            query = query.where(Lead.company_id == company_id)
        if bot_id:
            query = query.where(Lead.bot_id == bot_id)
        
        result = await db.execute(query)
        leads = result.scalars().all()
        
        # Считаем статистику
        total = len(leads)
        by_status = {}
        
        for lead in leads:
            status = lead.status or "unknown"
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_leads": total,
            "by_status": by_status,
        }


@router.get("/export/csv")
async def export_leads_csv(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    status: Optional[str] = None,
):
    """Экспорт лидов в CSV."""
    import csv
    import io
    
    async with get_async_db() as db:
        query = select(Lead).order_by(desc(Lead.created_at))
        
        if company_id:
            query = query.where(Lead.company_id == company_id)
        if bot_id:
            query = query.where(Lead.bot_id == bot_id)
        if status:
            query = query.where(Lead.status == status)
        
        result = await db.execute(query)
        leads = result.scalars().all()
        
        # Создаём CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow([
            "ID", "Имя", "Телефон", "Email", "Статус", 
            "Дата создания", "Данные"
        ])
        
        # Данные
        for lead in leads:
            writer.writerow([
                str(lead.id),
                lead.name or "",
                lead.phone or "",
                lead.email or "",
                lead.status or "",
                lead.created_at.isoformat() if lead.created_at else "",
                str(lead.data) if lead.data else "",
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=leads.csv"
            },
        )
