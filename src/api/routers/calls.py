"""
API для просмотра звонков.

Эндпоинты:
- GET /api/calls — список звонков
- GET /api/calls/{id} — детали звонка
- GET /api/calls/{id}/messages — сообщения звонка
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Call, Message

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class CallResponse(BaseModel):
    """Схема ответа звонка."""
    id: UUID
    bot_id: Optional[UUID]
    company_id: Optional[UUID]
    direction: str
    caller_number: Optional[str]
    callee_number: Optional[str]
    outcome: Optional[str]
    outcome_data: dict
    collected_data: dict
    duration_sec: int
    turn_count: int
    language: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    """Список звонков."""
    items: list[CallResponse]
    total: int


class MessageResponse(BaseModel):
    """Схема сообщения."""
    id: UUID
    role: str
    content: str
    state_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CallDetailResponse(BaseModel):
    """Детальная информация о звонке."""
    call: CallResponse
    messages: list[MessageResponse]


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=CallListResponse)
async def list_calls(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    outcome: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """Получить список звонков."""
    async with get_async_db() as db:
        query = select(Call).order_by(desc(Call.started_at))
        
        if company_id:
            query = query.where(Call.company_id == company_id)
        if bot_id:
            query = query.where(Call.bot_id == bot_id)
        if outcome:
            query = query.where(Call.outcome == outcome)
        if status:
            query = query.where(Call.status == status)
        
        # Считаем общее количество
        count_query = select(Call)
        if company_id:
            count_query = count_query.where(Call.company_id == company_id)
        if bot_id:
            count_query = count_query.where(Call.bot_id == bot_id)
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Получаем страницу
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        calls = result.scalars().all()
        
        return CallListResponse(
            items=[CallResponse.model_validate(call) for call in calls],
            total=total,
        )


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call(call_id: UUID):
    """Получить детали звонка с сообщениями."""
    async with get_async_db() as db:
        call = await db.get(Call, call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Получаем сообщения
        result = await db.execute(
            select(Message)
            .where(Message.call_id == call_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        return CallDetailResponse(
            call=CallResponse.model_validate(call),
            messages=[MessageResponse.model_validate(msg) for msg in messages],
        )


@router.get("/{call_id}/messages", response_model=list[MessageResponse])
async def get_call_messages(call_id: UUID):
    """Получить сообщения звонка."""
    async with get_async_db() as db:
        call = await db.get(Call, call_id)
        
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        result = await db.execute(
            select(Message)
            .where(Message.call_id == call_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        return [MessageResponse.model_validate(msg) for msg in messages]


@router.get("/stats/summary")
async def get_calls_stats(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
):
    """Получить статистику по звонкам."""
    async with get_async_db() as db:
        query = select(Call)
        
        if company_id:
            query = query.where(Call.company_id == company_id)
        if bot_id:
            query = query.where(Call.bot_id == bot_id)
        
        result = await db.execute(query)
        calls = result.scalars().all()
        
        # Считаем статистику
        total = len(calls)
        by_outcome = {}
        by_status = {}
        total_duration = 0
        
        for call in calls:
            outcome = call.outcome or "unknown"
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
            
            status = call.status or "unknown"
            by_status[status] = by_status.get(status, 0) + 1
            
            total_duration += call.duration_sec or 0
        
        return {
            "total_calls": total,
            "by_outcome": by_outcome,
            "by_status": by_status,
            "total_duration_sec": total_duration,
            "avg_duration_sec": total_duration / total if total > 0 else 0,
        }
