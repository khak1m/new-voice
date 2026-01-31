"""
API для просмотра звонков.

Эндпоинты:
- GET /api/calls — список звонков
- GET /api/calls/{id} — детали звонка
- GET /api/calls/{id}/messages — сообщения звонка
- GET /api/calls/{id}/transcript — транскрипт звонка
- GET /api/calls/{id}/recording — запись звонка
- POST /api/calls/{id}/rate — оценка звонка (нужно фронту)
"""

import os
from uuid import UUID
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Call, Message

# Recording storage path (can be configured via environment)
RECORDINGS_PATH = Path(os.getenv("RECORDINGS_PATH", "/var/lib/new-voice/recordings"))

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================


class CallResponse(BaseModel):
    """Схема ответа звонка."""

    id: UUID
    bot_id: Optional[UUID]
    company_id: Optional[UUID]
    skillbase_id: Optional[UUID]
    campaign_id: Optional[UUID]
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


class TranscriptMessageResponse(BaseModel):
    """Схема сообщения транскрипта (для frontend)."""

    id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    timestamp: str  # ISO format string

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    """Ответ транскрипта."""

    messages: list[TranscriptMessageResponse]


class CallDetailResponse(BaseModel):
    """Детальная информация о звонке."""

    call: CallResponse
    messages: list[MessageResponse]


class CallRateRequest(BaseModel):
    rating: int


# =============================================================================
# Эндпоинты
# =============================================================================


@router.get("", response_model=CallListResponse)
async def list_calls(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
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
        if skillbase_id:
            query = query.where(Call.skillbase_id == skillbase_id)
        if campaign_id:
            query = query.where(Call.campaign_id == campaign_id)
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
        if skillbase_id:
            count_query = count_query.where(Call.skillbase_id == skillbase_id)
        if campaign_id:
            count_query = count_query.where(Call.campaign_id == campaign_id)

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
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
):
    """Получить статистику по звонкам."""
    async with get_async_db() as db:
        query = select(Call)

        if company_id:
            query = query.where(Call.company_id == company_id)
        if bot_id:
            query = query.where(Call.bot_id == bot_id)
        if skillbase_id:
            query = query.where(Call.skillbase_id == skillbase_id)
        if campaign_id:
            query = query.where(Call.campaign_id == campaign_id)

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


# =============================================================================
# Transcript & Recording Endpoints
# =============================================================================


@router.get("/{call_id}/transcript", response_model=TranscriptResponse)
async def get_call_transcript(call_id: UUID):
    """
    Получить транскрипт звонка.

    Возвращает список сообщений в хронологическом порядке.
    Формат ответа оптимизирован для frontend.

    - **call_id**: UUID звонка

    Returns:
        TranscriptResponse: Список сообщений транскрипта

    Raises:
        400: Некорректный UUID
        404: Звонок не найден
    """
    # Validate UUID format
    try:
        call_uuid = UUID(str(call_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    async with get_async_db() as db:
        # Check if call exists
        call = await db.get(Call, call_uuid)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Get messages ordered by timestamp
        result = await db.execute(
            select(Message)
            .where(Message.call_id == call_uuid)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        # Convert to frontend format
        transcript_messages = []
        for msg in messages:
            # Extract values from ORM model
            msg_id = str(getattr(msg, "id", ""))
            msg_role = getattr(msg, "role", None) or "system"
            msg_content = getattr(msg, "content", None) or ""
            msg_created = getattr(msg, "created_at", None)
            msg_timestamp = msg_created.isoformat() if msg_created else ""

            transcript_messages.append(
                TranscriptMessageResponse(
                    id=msg_id,
                    role=msg_role,
                    content=msg_content,
                    timestamp=msg_timestamp,
                )
            )

        return TranscriptResponse(messages=transcript_messages)


@router.post("/{call_id}/rate")
async def rate_call(call_id: UUID, data: CallRateRequest):
    """Сохранить оценку звонка.

    Фронт отправляет число (например 1..5). Мы сохраняем это в outcome_data.
    """
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")

    async with get_async_db() as db:
        call = await db.get(Call, call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        outcome_data = call.outcome_data or {}
        outcome_data["rating"] = data.rating
        call.outcome_data = outcome_data

        await db.commit()

        return {"call_id": str(call_id), "rating": data.rating}


@router.get("/{call_id}/recording")
async def get_call_recording(call_id: UUID):
    """
    Получить запись звонка.

    Возвращает аудио файл записи звонка с поддержкой стриминга.
    Поддерживаемые форматы: WAV, MP3, OGG.

    - **call_id**: UUID звонка

    Returns:
        FileResponse: Аудио файл записи

    Raises:
        400: Некорректный UUID
        404: Звонок или запись не найдены
    """
    # Validate UUID format
    try:
        call_uuid = UUID(str(call_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    async with get_async_db() as db:
        # Check if call exists
        call = await db.get(Call, call_uuid)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

    # Look for recording file in various formats
    recording_file = None
    media_type = None

    for ext, mime in [
        ("wav", "audio/wav"),
        ("mp3", "audio/mpeg"),
        ("ogg", "audio/ogg"),
    ]:
        potential_path = RECORDINGS_PATH / f"{call_id}.{ext}"
        if potential_path.exists():
            recording_file = potential_path
            media_type = mime
            break

    # Also check if there's a livekit recording path
    livekit_room_id = getattr(call, "livekit_room_id", None)
    if not recording_file and livekit_room_id:
        for ext, mime in [
            ("wav", "audio/wav"),
            ("mp3", "audio/mpeg"),
            ("ogg", "audio/ogg"),
        ]:
            potential_path = RECORDINGS_PATH / f"{livekit_room_id}.{ext}"
            if potential_path.exists():
                recording_file = potential_path
                media_type = mime
                break

    if not recording_file:
        raise HTTPException(
            status_code=404,
            detail="Recording not found. The call may not have been recorded or the recording has been deleted.",
        )

    return FileResponse(
        path=str(recording_file),
        media_type=media_type,
        filename=f"call_{call_id}.{recording_file.suffix[1:]}",
        headers={"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=3600"},
    )
