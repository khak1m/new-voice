"""
API для управления Skillbases (Task 17).

Эндпоинты:
- GET /api/skillbases — список Skillbases
- POST /api/skillbases — создать Skillbase
- GET /api/skillbases/{id} — получить Skillbase
- PUT /api/skillbases/{id} — обновить Skillbase
- DELETE /api/skillbases/{id} — удалить Skillbase
"""

from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Skillbase, Company
from src.services.skillbase_service import SkillbaseService, SkillbaseValidationError

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class SkillbaseCreate(BaseModel):
    """Схема создания Skillbase."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    company_id: UUID
    config: Dict[str, Any] = Field(..., description="Skillbase configuration (context, flow, agent, tools, voice, llm)")
    knowledge_base_id: Optional[UUID] = None
    is_active: bool = True
    is_published: bool = False


class SkillbaseUpdate(BaseModel):
    """Схема обновления Skillbase."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    knowledge_base_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class SkillbaseResponse(BaseModel):
    """Схема ответа Skillbase."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    company_id: UUID
    config: Dict[str, Any]
    version: int
    knowledge_base_id: Optional[UUID]
    is_active: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillbaseListResponse(BaseModel):
    """Список Skillbases."""
    items: List[SkillbaseResponse]
    total: int


class ValidationErrorDetail(BaseModel):
    """Детали ошибки валидации."""
    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Ответ с ошибками валидации."""
    detail: str
    errors: List[ValidationErrorDetail]


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=SkillbaseListResponse)
async def list_skillbases(
    company_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    is_published: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
):
    """
    Получить список Skillbases.
    
    Фильтры:
    - company_id: фильтр по компании
    - is_active: фильтр по активности
    - is_published: фильтр по публикации
    - skip: пропустить N записей (пагинация)
    - limit: максимум записей (default: 50)
    """
    async with get_async_db() as db:
        query = select(Skillbase)
        
        if company_id:
            query = query.where(Skillbase.company_id == company_id)
        if is_active is not None:
            query = query.where(Skillbase.is_active == is_active)
        if is_published is not None:
            query = query.where(Skillbase.is_published == is_published)
        
        query = query.offset(skip).limit(limit).order_by(Skillbase.created_at.desc())
        
        result = await db.execute(query)
        skillbases = list(result.scalars().all())
        
        # Считаем общее количество
        count_query = select(Skillbase)
        if company_id:
            count_query = count_query.where(Skillbase.company_id == company_id)
        if is_active is not None:
            count_query = count_query.where(Skillbase.is_active == is_active)
        if is_published is not None:
            count_query = count_query.where(Skillbase.is_published == is_published)
        
        count_result = await db.execute(count_query)
        total = len(list(count_result.scalars().all()))
        
        return SkillbaseListResponse(
            items=[SkillbaseResponse.model_validate(sb) for sb in skillbases],
            total=total,
        )


@router.post("", response_model=SkillbaseResponse, status_code=201)
async def create_skillbase(data: SkillbaseCreate):
    """
    Создать новый Skillbase.
    
    Валидирует конфигурацию перед сохранением.
    Возвращает 400 с детальными ошибками при невалидной конфигурации.
    """
    async with get_async_db() as db:
        service = SkillbaseService(db)
        
        try:
            skillbase = await service.create(
                company_id=data.company_id,
                name=data.name,
                slug=data.slug,
                description=data.description,
                config=data.config,
                knowledge_base_id=data.knowledge_base_id,
                is_active=data.is_active,
                is_published=data.is_published,
            )
            
            return SkillbaseResponse.model_validate(skillbase)
        
        except SkillbaseValidationError as e:
            # Возвращаем детальные ошибки валидации
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(e),
                    "errors": e.errors if hasattr(e, "errors") else [],
                }
            )
        
        except ValueError as e:
            # Другие ошибки валидации (company not found, slug exists, etc.)
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/{skillbase_id}", response_model=SkillbaseResponse)
async def get_skillbase(skillbase_id: UUID):
    """
    Получить Skillbase по ID.
    """
    async with get_async_db() as db:
        skillbase = await db.get(Skillbase, skillbase_id)
        
        if not skillbase:
            raise HTTPException(status_code=404, detail="Skillbase not found")
        
        return SkillbaseResponse.model_validate(skillbase)


@router.put("/{skillbase_id}", response_model=SkillbaseResponse)
async def update_skillbase(skillbase_id: UUID, data: SkillbaseUpdate):
    """
    Обновить Skillbase.
    
    При обновлении config автоматически инкрементируется version.
    Валидирует новую конфигурацию перед сохранением.
    """
    async with get_async_db() as db:
        service = SkillbaseService(db)
        
        try:
            skillbase = await service.update(
                skillbase_id=skillbase_id,
                name=data.name,
                description=data.description,
                config=data.config,
                knowledge_base_id=data.knowledge_base_id,
                is_active=data.is_active,
                is_published=data.is_published,
            )
            
            return SkillbaseResponse.model_validate(skillbase)
        
        except SkillbaseValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(e),
                    "errors": e.errors if hasattr(e, "errors") else [],
                }
            )
        
        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{skillbase_id}", status_code=204)
async def delete_skillbase(skillbase_id: UUID):
    """
    Удалить Skillbase.
    
    ВНИМАНИЕ: Удаление Skillbase удалит все связанные Campaigns и CallTasks (CASCADE).
    """
    async with get_async_db() as db:
        skillbase = await db.get(Skillbase, skillbase_id)
        
        if not skillbase:
            raise HTTPException(status_code=404, detail="Skillbase not found")
        
        await db.delete(skillbase)
        await db.commit()


# =============================================================================
# Дополнительные эндпоинты для Skillbase Configurator
# =============================================================================

@router.get("/voices/list")
async def list_voices():
    """
    Получить список доступных голосов.
    
    Возвращает список голосов с информацией:
    - id: идентификатор голоса
    - name: название голоса
    - gender: пол (male/female)
    - style: стиль голоса
    """
    from src.schemas.skillbase_schemas import AVAILABLE_VOICES
    return {"voices": AVAILABLE_VOICES}


@router.post("/tts-preview")
async def tts_preview(text: str = Query(..., max_length=500), voice_id: str = Query(default="sasha_v1")):
    """
    Генерация TTS preview для фразы.
    
    Параметры:
    - text: текст для озвучки (до 500 символов)
    - voice_id: ID голоса
    
    Возвращает:
    - audio_url: URL аудиофайла (временный)
    
    TODO: Интеграция с Cartesia/ElevenLabs
    """
    # Заглушка пока нет интеграции с TTS
    return {
        "audio_url": f"https://example.com/tts/{voice_id}/{hash(text)}.mp3",
        "duration": len(text) * 0.1,  # примерная длительность
        "voice_id": voice_id,
        "text": text
    }


@router.post("/{skillbase_id}/test-call")
async def test_call(
    skillbase_id: UUID,
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
):
    """
    Тестовый звонок с использованием Skillbase.
    
    Параметры:
    - skillbase_id: ID Skillbase
    - phone_number: номер телефона в международном формате
    
    Возвращает:
    - call_id: ID созданного звонка
    - status: статус звонка
    
    TODO: Интеграция с LiveKit + телефонией
    """
    async with get_async_db() as db:
        skillbase = await db.get(Skillbase, skillbase_id)
        
        if not skillbase:
            raise HTTPException(status_code=404, detail="Skillbase not found")
        
        if not skillbase.is_active:
            raise HTTPException(status_code=400, detail="Skillbase is not active")
        
        # Заглушка пока нет интеграции с телефонией
        return {
            "call_id": "test-call-" + str(skillbase_id)[:8],
            "status": "initiated",
            "phone_number": phone_number,
            "skillbase_id": str(skillbase_id),
            "message": "Test call initiated (stub implementation)"
        }


@router.get("/{skillbase_id}/config")
async def get_skillbase_config(skillbase_id: UUID):
    """
    Получить только конфигурацию Skillbase.
    
    Удобно для загрузки конфигурации в UI конфигуратор.
    """
    async with get_async_db() as db:
        skillbase = await db.get(Skillbase, skillbase_id)
        
        if not skillbase:
            raise HTTPException(status_code=404, detail="Skillbase not found")
        
        return {
            "id": skillbase.id,
            "name": skillbase.name,
            "config": skillbase.config,
            "version": skillbase.version,
            "updated_at": skillbase.updated_at
        }


@router.put("/{skillbase_id}/config")
async def update_skillbase_config(
    skillbase_id: UUID,
    config: Dict[str, Any]
):
    """
    Обновить только конфигурацию Skillbase.
    
    Валидирует конфигурацию и инкрементирует version.
    """
    async with get_async_db() as db:
        service = SkillbaseService(db)
        
        try:
            skillbase = await service.update(
                skillbase_id=skillbase_id,
                config=config
            )
            
            return {
                "id": skillbase.id,
                "name": skillbase.name,
                "config": skillbase.config,
                "version": skillbase.version,
                "updated_at": skillbase.updated_at
            }
        
        except SkillbaseValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(e),
                    "errors": e.errors if hasattr(e, "errors") else [],
                }
            )
        
        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
