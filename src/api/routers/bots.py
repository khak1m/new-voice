"""
API для управления ботами.

Эндпоинты:
- GET /api/bots — список ботов
- POST /api/bots — создать бота
- GET /api/bots/{id} — получить бота
- PUT /api/bots/{id} — обновить бота
- DELETE /api/bots/{id} — удалить бота
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Bot, Company

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class BotCreate(BaseModel):
    """Схема создания бота."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    company_id: UUID
    scenario_config: dict = Field(default_factory=dict)
    voice_config: Optional[dict] = None
    llm_config: Optional[dict] = None


class BotUpdate(BaseModel):
    """Схема обновления бота."""
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_config: Optional[dict] = None
    voice_config: Optional[dict] = None
    llm_config: Optional[dict] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class BotResponse(BaseModel):
    """Схема ответа бота."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    company_id: UUID
    scenario_config: dict
    voice_config: dict
    llm_config: dict
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BotListResponse(BaseModel):
    """Список ботов."""
    items: list[BotResponse]
    total: int


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=BotListResponse)
async def list_bots(
    company_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
):
    """Получить список ботов."""
    async with get_async_db() as db:
        query = select(Bot)
        
        if company_id:
            query = query.where(Bot.company_id == company_id)
        if is_active is not None:
            query = query.where(Bot.is_active == is_active)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        bots = result.scalars().all()
        
        # Считаем общее количество
        count_query = select(Bot)
        if company_id:
            count_query = count_query.where(Bot.company_id == company_id)
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return BotListResponse(
            items=[BotResponse.model_validate(bot) for bot in bots],
            total=total,
        )


@router.post("", response_model=BotResponse, status_code=201)
async def create_bot(data: BotCreate):
    """Создать нового бота."""
    async with get_async_db() as db:
        # Проверяем существование компании
        company = await db.get(Company, data.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Проверяем уникальность slug
        existing = await db.execute(
            select(Bot).where(
                Bot.company_id == data.company_id,
                Bot.slug == data.slug,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Bot with this slug already exists")
        
        # Создаём бота
        bot = Bot(
            name=data.name,
            slug=data.slug,
            description=data.description,
            company_id=data.company_id,
            scenario_config=data.scenario_config,
            voice_config=data.voice_config or {
                "tts_provider": "cartesia",
                "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                "stt_provider": "deepgram",
                "stt_language": "ru",
            },
            llm_config=data.llm_config or {
                "provider": "ollama",
                "model": "qwen2:1.5b",
                "temperature": 0.7,
            },
        )
        
        db.add(bot)
        await db.commit()
        await db.refresh(bot)
        
        return BotResponse.model_validate(bot)


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(bot_id: UUID):
    """Получить бота по ID."""
    async with get_async_db() as db:
        bot = await db.get(Bot, bot_id)
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        return BotResponse.model_validate(bot)


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: UUID, data: BotUpdate):
    """Обновить бота."""
    async with get_async_db() as db:
        bot = await db.get(Bot, bot_id)
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Обновляем поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bot, field, value)
        
        await db.commit()
        await db.refresh(bot)
        
        return BotResponse.model_validate(bot)


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(bot_id: UUID):
    """Удалить бота."""
    async with get_async_db() as db:
        bot = await db.get(Bot, bot_id)
        
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        await db.delete(bot)
        await db.commit()
