"""
API для дашборда.

Эндпоинты:
- GET /api/dashboard/stats — общая статистика
"""

from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Bot, Call, Lead

router = APIRouter()


class DashboardStats(BaseModel):
    """Статистика для дашборда."""
    total_calls: int
    total_calls_week: int
    calls_change_percent: float
    
    active_bots: int
    total_bots: int
    
    new_leads: int
    leads_pending: int
    leads_change_percent: float
    
    avg_duration_sec: int
    avg_duration_min: float
    
    calls_by_day: list[dict]
    calls_by_outcome: dict[str, int]


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(company_id: Optional[UUID] = None):
    """Получить статистику для дашборда."""
    async with get_async_db() as db:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Запросы для звонков
        calls_query = select(Call)
        if company_id:
            calls_query = calls_query.where(Call.company_id == company_id)
        
        result = await db.execute(calls_query)
        all_calls = result.scalars().all()
        
        # Звонки за неделю
        calls_this_week = [c for c in all_calls if c.started_at and c.started_at >= week_ago]
        calls_last_week = [c for c in all_calls if c.started_at and two_weeks_ago <= c.started_at < week_ago]
        
        # Изменение в процентах
        if len(calls_last_week) > 0:
            calls_change = ((len(calls_this_week) - len(calls_last_week)) / len(calls_last_week)) * 100
        else:
            calls_change = 100 if len(calls_this_week) > 0 else 0
        
        # Боты
        bots_query = select(Bot)
        if company_id:
            bots_query = bots_query.where(Bot.company_id == company_id)
        
        result = await db.execute(bots_query)
        all_bots = result.scalars().all()
        active_bots = len([b for b in all_bots if b.is_active])
        
        # Лиды
        leads_query = select(Lead)
        if company_id:
            leads_query = leads_query.where(Lead.company_id == company_id)
        
        result = await db.execute(leads_query)
        all_leads = result.scalars().all()
        
        leads_this_week = [l for l in all_leads if l.created_at and l.created_at >= week_ago]
        leads_last_week = [l for l in all_leads if l.created_at and two_weeks_ago <= l.created_at < week_ago]
        leads_pending = len([l for l in all_leads if l.status in ("new", "pending")])
        
        if len(leads_last_week) > 0:
            leads_change = ((len(leads_this_week) - len(leads_last_week)) / len(leads_last_week)) * 100
        else:
            leads_change = 100 if len(leads_this_week) > 0 else 0
        
        # Средняя длительность
        durations = [c.duration_sec for c in all_calls if c.duration_sec]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Звонки по дням (последние 7 дней)
        calls_by_day = []
        for i in range(7):
            day = now - timedelta(days=6-i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_calls = len([
                c for c in all_calls 
                if c.started_at and day_start <= c.started_at < day_end
            ])
            
            calls_by_day.append({
                "date": day_start.strftime("%d %b"),
                "count": day_calls,
            })
        
        # Звонки по результатам
        calls_by_outcome = {}
        for call in all_calls:
            outcome = call.outcome or "unknown"
            calls_by_outcome[outcome] = calls_by_outcome.get(outcome, 0) + 1
        
        return DashboardStats(
            total_calls=len(all_calls),
            total_calls_week=len(calls_this_week),
            calls_change_percent=round(calls_change, 1),
            
            active_bots=active_bots,
            total_bots=len(all_bots),
            
            new_leads=len(leads_this_week),
            leads_pending=leads_pending,
            leads_change_percent=round(leads_change, 1),
            
            avg_duration_sec=int(avg_duration),
            avg_duration_min=round(avg_duration / 60, 1) if avg_duration else 0,
            
            calls_by_day=calls_by_day,
            calls_by_outcome=calls_by_outcome,
        )
