"""
API для аналитики и метрик (Task 19).

Эндпоинты:
- GET /api/analytics/calls — история звонков с фильтрацией
- GET /api/analytics/calls/{id}/metrics — метрики конкретного звонка
- GET /api/analytics/metrics — агрегированные метрики
- WS /api/analytics/ws/calls/{id} — real-time мониторинг звонка
"""

from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.connection import get_async_db
from src.database.models import Call, CallMetrics, CallLog, Skillbase, Campaign

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class CallHistoryItem(BaseModel):
    """Элемент истории звонков."""
    id: UUID
    skillbase_id: Optional[UUID]
    campaign_id: Optional[UUID]
    phone_number: Optional[str]
    outcome: Optional[str]
    duration_sec: int
    turn_count: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    
    # Метрики (если есть)
    avg_eou_latency: Optional[float] = None
    cost_total: Optional[float] = None
    
    class Config:
        from_attributes = True


class CallHistoryResponse(BaseModel):
    """История звонков."""
    items: List[CallHistoryItem]
    total: int
    page: int
    page_size: int


class CallMetricsResponse(BaseModel):
    """Метрики звонка."""
    call_id: UUID
    
    # Latency metrics (ms)
    avg_ttfb_stt: Optional[float]
    avg_latency_llm: Optional[float]
    avg_ttfb_tts: Optional[float]
    avg_eou_latency: Optional[float]
    
    min_ttfb_stt: Optional[float]
    max_ttfb_stt: Optional[float]
    min_latency_llm: Optional[float]
    max_latency_llm: Optional[float]
    min_ttfb_tts: Optional[float]
    max_ttfb_tts: Optional[float]
    min_eou_latency: Optional[float]
    max_eou_latency: Optional[float]
    
    # Usage metrics
    stt_duration_sec: Optional[float]
    llm_input_tokens: Optional[int]
    llm_output_tokens: Optional[int]
    tts_characters: Optional[int]
    livekit_duration_sec: Optional[float]
    
    # Cost breakdown (USD)
    cost_stt: Optional[float]
    cost_llm: Optional[float]
    cost_tts: Optional[float]
    cost_livekit: Optional[float]
    cost_total: Optional[float]
    
    # Quality metrics
    turn_count: Optional[int]
    interruption_count: Optional[int]
    interruption_rate: Optional[float]
    sentiment_score: Optional[float]
    
    # Outcome
    outcome: Optional[str]
    outcome_confidence: Optional[float]
    outcome_reason: Optional[str]
    
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AggregatedMetrics(BaseModel):
    """Агрегированные метрики."""
    # Период
    start_date: date
    end_date: date
    
    # Общая статистика
    total_calls: int
    completed_calls: int
    failed_calls: int
    
    # Средние метрики
    avg_duration_sec: Optional[float]
    avg_turn_count: Optional[float]
    avg_eou_latency: Optional[float]
    avg_interruption_rate: Optional[float]
    
    # Стоимость
    total_cost: Optional[float]
    avg_cost_per_call: Optional[float]
    
    # Outcomes
    outcome_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Фильтры
    skillbase_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("/calls", response_model=CallHistoryResponse)
async def get_call_history(
    # Фильтры
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    outcome: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    
    # Пагинация
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """
    Получить историю звонков с фильтрацией.
    
    Фильтры:
    - skillbase_id: фильтр по Skillbase
    - campaign_id: фильтр по Campaign
    - outcome: фильтр по результату (success, fail, voicemail, no_answer, busy)
    - status: фильтр по статусу (active, completed, failed)
    - start_date: начало периода (YYYY-MM-DD)
    - end_date: конец периода (YYYY-MM-DD)
    
    Пагинация:
    - page: номер страницы (начиная с 1)
    - page_size: размер страницы (default: 50, max: 100)
    """
    async with get_async_db() as db:
        # Базовый запрос с eager loading метрик
        query = select(Call).options(
            selectinload(Call.metrics)
        ).order_by(Call.started_at.desc())
        
        # Применяем фильтры
        filters = []
        
        if skillbase_id:
            # Для Skillbase нужно джойнить через Campaign или напрямую если есть поле
            # Предполагаем что у Call есть skillbase_id или campaign.skillbase_id
            filters.append(Call.skillbase_id == skillbase_id)
        
        if campaign_id:
            filters.append(Call.campaign_id == campaign_id)
        
        if outcome:
            filters.append(Call.outcome == outcome)
        
        if status:
            filters.append(Call.status == status)
        
        if start_date:
            filters.append(Call.started_at >= datetime.combine(start_date, datetime.min.time()))
        
        if end_date:
            filters.append(Call.started_at <= datetime.combine(end_date, datetime.max.time()))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Считаем total
        count_query = select(func.count()).select_from(Call)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Применяем пагинацию
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await db.execute(query)
        calls = list(result.scalars().all())
        
        # Формируем ответ
        items = []
        for call in calls:
            item_data = {
                "id": call.id,
                "skillbase_id": getattr(call, "skillbase_id", None),
                "campaign_id": getattr(call, "campaign_id", None),
                "phone_number": call.caller_number or call.callee_number,
                "outcome": call.outcome,
                "duration_sec": call.duration_sec,
                "turn_count": call.turn_count,
                "status": call.status,
                "started_at": call.started_at,
                "ended_at": call.ended_at,
            }
            
            # Добавляем метрики если есть
            if call.metrics:
                item_data["avg_eou_latency"] = call.metrics.avg_eou_latency
                item_data["cost_total"] = float(call.metrics.cost_total) if call.metrics.cost_total else None
            
            items.append(CallHistoryItem(**item_data))
        
        return CallHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/calls/{call_id}/metrics", response_model=CallMetricsResponse)
async def get_call_metrics(call_id: UUID):
    """
    Получить метрики конкретного звонка.
    
    Возвращает детальные метрики:
    - Latency (TTFB STT, LLM, TTFB TTS, EOU)
    - Usage (tokens, characters, duration)
    - Cost breakdown
    - Quality metrics (interruptions, sentiment)
    - Outcome classification
    """
    async with get_async_db() as db:
        # Загружаем метрики
        result = await db.execute(
            select(CallMetrics).where(CallMetrics.call_id == call_id)
        )
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Call metrics not found")
        
        # Конвертируем Decimal в float для JSON
        response_data = {
            "call_id": metrics.call_id,
            "avg_ttfb_stt": metrics.avg_ttfb_stt,
            "avg_latency_llm": metrics.avg_latency_llm,
            "avg_ttfb_tts": metrics.avg_ttfb_tts,
            "avg_eou_latency": metrics.avg_eou_latency,
            "min_ttfb_stt": metrics.min_ttfb_stt,
            "max_ttfb_stt": metrics.max_ttfb_stt,
            "min_latency_llm": metrics.min_latency_llm,
            "max_latency_llm": metrics.max_latency_llm,
            "min_ttfb_tts": metrics.min_ttfb_tts,
            "max_ttfb_tts": metrics.max_ttfb_tts,
            "min_eou_latency": metrics.min_eou_latency,
            "max_eou_latency": metrics.max_eou_latency,
            "stt_duration_sec": metrics.stt_duration_sec,
            "llm_input_tokens": metrics.llm_input_tokens,
            "llm_output_tokens": metrics.llm_output_tokens,
            "tts_characters": metrics.tts_characters,
            "livekit_duration_sec": metrics.livekit_duration_sec,
            "cost_stt": float(metrics.cost_stt) if metrics.cost_stt else None,
            "cost_llm": float(metrics.cost_llm) if metrics.cost_llm else None,
            "cost_tts": float(metrics.cost_tts) if metrics.cost_tts else None,
            "cost_livekit": float(metrics.cost_livekit) if metrics.cost_livekit else None,
            "cost_total": float(metrics.cost_total) if metrics.cost_total else None,
            "turn_count": metrics.turn_count,
            "interruption_count": metrics.interruption_count,
            "interruption_rate": metrics.interruption_rate,
            "sentiment_score": metrics.sentiment_score,
            "outcome": metrics.outcome,
            "outcome_confidence": metrics.outcome_confidence,
            "outcome_reason": metrics.outcome_reason,
            "created_at": metrics.created_at,
        }
        
        return CallMetricsResponse(**response_data)


@router.get("/metrics", response_model=AggregatedMetrics)
async def get_aggregated_metrics(
    # Фильтры
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    start_date: Optional[date] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="End date (YYYY-MM-DD)"),
):
    """
    Получить агрегированные метрики.
    
    Возвращает:
    - Общую статистику звонков
    - Средние метрики (duration, latency, interruption rate)
    - Общую стоимость
    - Распределение outcomes
    
    Фильтры:
    - skillbase_id: фильтр по Skillbase
    - campaign_id: фильтр по Campaign
    - start_date: начало периода (default: 30 дней назад)
    - end_date: конец периода (default: сегодня)
    """
    async with get_async_db() as db:
        # Дефолтные даты
        if not end_date:
            end_date = date.today()
        if not start_date:
            from datetime import timedelta
            start_date = end_date - timedelta(days=30)
        
        # Базовый запрос
        filters = [
            Call.started_at >= datetime.combine(start_date, datetime.min.time()),
            Call.started_at <= datetime.combine(end_date, datetime.max.time()),
        ]
        
        if skillbase_id:
            filters.append(Call.skillbase_id == skillbase_id)
        
        if campaign_id:
            filters.append(Call.campaign_id == campaign_id)
        
        # Общая статистика
        stats_query = select(
            func.count(Call.id).label("total_calls"),
            func.count(Call.id).filter(Call.status == "completed").label("completed_calls"),
            func.count(Call.id).filter(Call.status == "failed").label("failed_calls"),
            func.avg(Call.duration_sec).label("avg_duration_sec"),
            func.avg(Call.turn_count).label("avg_turn_count"),
        ).where(and_(*filters))
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.one()
        
        # Метрики из CallMetrics
        metrics_query = select(
            func.avg(CallMetrics.avg_eou_latency).label("avg_eou_latency"),
            func.avg(CallMetrics.interruption_rate).label("avg_interruption_rate"),
            func.sum(CallMetrics.cost_total).label("total_cost"),
        ).select_from(Call).join(
            CallMetrics, Call.id == CallMetrics.call_id, isouter=True
        ).where(and_(*filters))
        
        metrics_result = await db.execute(metrics_query)
        metrics = metrics_result.one()
        
        # Распределение outcomes
        outcome_query = select(
            Call.outcome,
            func.count(Call.id).label("count"),
        ).where(
            and_(*filters),
            Call.outcome.isnot(None)
        ).group_by(Call.outcome)
        
        outcome_result = await db.execute(outcome_query)
        outcome_distribution = {row.outcome: row.count for row in outcome_result}
        
        # Средняя стоимость
        avg_cost_per_call = None
        if stats.total_calls and metrics.total_cost:
            avg_cost_per_call = float(metrics.total_cost) / stats.total_calls
        
        return AggregatedMetrics(
            start_date=start_date,
            end_date=end_date,
            total_calls=stats.total_calls or 0,
            completed_calls=stats.completed_calls or 0,
            failed_calls=stats.failed_calls or 0,
            avg_duration_sec=float(stats.avg_duration_sec) if stats.avg_duration_sec else None,
            avg_turn_count=float(stats.avg_turn_count) if stats.avg_turn_count else None,
            avg_eou_latency=float(metrics.avg_eou_latency) if metrics.avg_eou_latency else None,
            avg_interruption_rate=float(metrics.avg_interruption_rate) if metrics.avg_interruption_rate else None,
            total_cost=float(metrics.total_cost) if metrics.total_cost else None,
            avg_cost_per_call=avg_cost_per_call,
            outcome_distribution=outcome_distribution,
            skillbase_id=skillbase_id,
            campaign_id=campaign_id,
        )


# =============================================================================
# WebSocket для real-time мониторинга
# =============================================================================

class ConnectionManager:
    """Менеджер WebSocket соединений."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, call_id: str, websocket: WebSocket):
        """Подключить клиента к мониторингу звонка."""
        await websocket.accept()
        if call_id not in self.active_connections:
            self.active_connections[call_id] = []
        self.active_connections[call_id].append(websocket)
    
    def disconnect(self, call_id: str, websocket: WebSocket):
        """Отключить клиента."""
        if call_id in self.active_connections:
            self.active_connections[call_id].remove(websocket)
            if not self.active_connections[call_id]:
                del self.active_connections[call_id]
    
    async def broadcast(self, call_id: str, message: dict):
        """Отправить сообщение всем подключенным клиентам."""
        if call_id in self.active_connections:
            for connection in self.active_connections[call_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/calls/{call_id}")
async def websocket_call_monitor(websocket: WebSocket, call_id: UUID):
    """
    WebSocket для real-time мониторинга звонка.
    
    Отправляет обновления:
    - Новые turn logs
    - Обновления метрик
    - Изменения статуса
    
    Формат сообщений:
    {
        "type": "turn" | "metrics" | "status",
        "data": {...}
    }
    """
    call_id_str = str(call_id)
    await manager.connect(call_id_str, websocket)
    
    try:
        # Отправляем начальное состояние
        async with get_async_db() as db:
            call = await db.get(Call, call_id)
            if not call:
                await websocket.send_json({"type": "error", "message": "Call not found"})
                return
            
            await websocket.send_json({
                "type": "init",
                "data": {
                    "call_id": str(call.id),
                    "status": call.status,
                    "started_at": call.started_at.isoformat(),
                }
            })
        
        # Слушаем сообщения от клиента (ping/pong)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(call_id_str, websocket)
    except Exception as e:
        manager.disconnect(call_id_str, websocket)
        print(f"WebSocket error: {e}")


# Функция для отправки обновлений (вызывается из VoiceAgent)
async def send_turn_update(call_id: UUID, turn_data: dict):
    """Отправить обновление turn через WebSocket."""
    await manager.broadcast(str(call_id), {
        "type": "turn",
        "data": turn_data,
    })


async def send_metrics_update(call_id: UUID, metrics_data: dict):
    """Отправить обновление метрик через WebSocket."""
    await manager.broadcast(str(call_id), {
        "type": "metrics",
        "data": metrics_data,
    })
