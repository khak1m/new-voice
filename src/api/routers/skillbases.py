"""
API для управления Skillbases (Task 17).

Эндпоинты:
- GET /api/skillbases — список Skillbases
- POST /api/skillbases — создать Skillbase
- GET /api/skillbases/{id} — получить Skillbase
- PUT /api/skillbases/{id} — обновить Skillbase
- DELETE /api/skillbases/{id} — удалить Skillbase
"""

import re
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

import base64
import io
import math
import wave

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Skillbase
from src.services.skillbase_service import SkillbaseService, SkillbaseValidationError
from src.services.company_utils import resolve_company

router = APIRouter()


def _generate_fallback_wav(text: str, sample_rate: int = 22050) -> bytes:
    """Generate a short WAV tone as a safe fallback."""
    duration_sec = max(0.6, min(6.0, len(text) * 0.03))
    freq_hz = 440.0
    frames = int(sample_rate * duration_sec)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        fade_frames = max(1, int(sample_rate * 0.02))
        for i in range(frames):
            t = i / sample_rate
            sample = math.sin(2 * math.pi * freq_hz * t)
            if i < fade_frames:
                sample *= i / fade_frames
            elif i > frames - fade_frames:
                sample *= max(0.0, (frames - i) / fade_frames)
            v = int(sample * 32767)
            wf.writeframesraw(v.to_bytes(2, byteorder="little", signed=True))

    return buf.getvalue()


# =============================================================================
# Pydantic схемы
# =============================================================================


class SkillbaseCreate(BaseModel):
    """Схема создания Skillbase (как делает фронт).

    Фронт присылает только name/description/company_id (строка).
    Остальное (slug + базовый config) создаём на бэке.
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    company_id: str


class SkillbaseUpdate(BaseModel):
    """Схема обновления Skillbase."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    knowledge_base_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None


class TestCallRequest(BaseModel):
    """Схема запроса тестового звонка."""

    phone_number: str = Field(
        ...,
        pattern=r"^\+?[1-9]\d{1,14}$",
        description="Номер телефона в международном формате",
    )


class TTSPreviewRequest(BaseModel):
    """Схема запроса TTS preview (как ожидает frontend)."""

    text: str = Field(..., min_length=1, max_length=500)
    voice_id: str = Field(default="sasha_v1", min_length=1)


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

        # Resolve company (UUID or slug). For demo/frontend default we auto-create.
        try:
            company = await resolve_company(
                db, data.company_id, default_name="Default Company"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        def slugify(value: str) -> str:
            value = value.strip().lower()
            value = re.sub(r"[^a-z0-9\s-]", "", value)
            value = re.sub(r"\s+", "-", value)
            value = re.sub(r"-+", "-", value)
            return value[:100] or "skillbase"

        base_slug = slugify(data.name)
        slug = base_slug
        # Ensure slug uniqueness within company
        for i in range(1, 100):
            existing = await db.execute(
                select(Skillbase).where(
                    Skillbase.company_id == company.id,
                    Skillbase.slug == slug,
                )
            )
            if existing.scalar_one_or_none() is None:
                break
            slug = f"{base_slug}-{i + 1}"[:100]

        default_config: Dict[str, Any] = {
            "context": {
                "role": "Вы - голосовой ассистент компании.",
                "style": "Говори коротко и по делу.",
                "rules": [],
                "facts": [],
                "lead_criteria": [],
                "language": "ru",
                "voice_id": "sasha_v1",
                "max_call_duration": 600,
            },
            "flow": {
                "greeting_phrases": ["Здравствуйте!"],
                "conversation_plan": ["Уточнить, как можно обращаться."],
            },
        }

        try:
            skillbase = await service.create(
                company_id=company.id,
                name=data.name,
                slug=slug,
                description=data.description,
                config=default_config,
                knowledge_base_id=None,
            )

            return SkillbaseResponse.model_validate(skillbase)

        except SkillbaseValidationError as e:
            # Возвращаем детальные ошибки валидации
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(e),
                    "errors": e.errors if hasattr(e, "errors") else [],
                },
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
                },
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
async def tts_preview(data: TTSPreviewRequest):
    """
    Генерация TTS preview для фразы.

    Параметры:
    - text: текст для озвучки (до 500 символов)
    - voice_id: ID голоса

    Возвращает:
    - audio_url: URL аудиофайла (временный)

    TODO: Интеграция с Cartesia/ElevenLabs
    """
    # Реальный audio bytes эндпоинт живет в /api/tts/preview.
    # Здесь возвращаем data URL, чтобы фронт мог проиграть без отдельного хранилища.
    try:
        from src.services import get_tts_service

        tts_service = get_tts_service()
        audio_bytes = await tts_service.generate_audio(
            text=data.text,
            voice_id=data.voice_id,
            language="ru",
            output_format="wav",
        )
        mime = "audio/wav"

    except Exception:
        # Fallback tone (если провайдер недоступен/voice_id невалидный)
        audio_bytes = _generate_fallback_wav(data.text)
        mime = "audio/wav"

    b64 = base64.b64encode(audio_bytes).decode("ascii")
    audio_url = f"data:{mime};base64,{b64}"

    return {
        "audio_url": audio_url,
        "duration": max(0.5, min(10.0, len(data.text) * 0.06)),
        "voice_id": data.voice_id,
        "text": data.text,
    }


@router.post("/{skillbase_id}/test-call")
async def test_call(skillbase_id: UUID, request: TestCallRequest):
    """
    Тестовый звонок с использованием Skillbase.

    Параметры:
    - skillbase_id: ID Skillbase
    - request.phone_number: номер телефона в международном формате

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
            "phone_number": request.phone_number,
            "skillbase_id": str(skillbase_id),
            "message": "Test call initiated (stub implementation)",
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
            "updated_at": skillbase.updated_at,
        }


@router.put("/{skillbase_id}/config")
async def update_skillbase_config(skillbase_id: UUID, config: Dict[str, Any]):
    """
    Обновить только конфигурацию Skillbase.

    Валидирует конфигурацию и инкрементирует version.
    """
    async with get_async_db() as db:
        service = SkillbaseService(db)

        try:
            skillbase = await service.update(skillbase_id=skillbase_id, config=config)

            return {
                "id": skillbase.id,
                "name": skillbase.name,
                "config": skillbase.config,
                "version": skillbase.version,
                "updated_at": skillbase.updated_at,
            }

        except SkillbaseValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": str(e),
                    "errors": e.errors if hasattr(e, "errors") else [],
                },
            )

        except ValueError as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=400, detail=str(e))
