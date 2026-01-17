"""
API для управления Campaigns (Task 18).

Эндпоинты:
- GET /api/campaigns — список Campaigns
- POST /api/campaigns — создать Campaign
- GET /api/campaigns/{id} — получить Campaign
- PUT /api/campaigns/{id} — обновить Campaign
- DELETE /api/campaigns/{id} — удалить Campaign
- POST /api/campaigns/{id}/call-list — загрузить список контактов
- POST /api/campaigns/{id}/start — запустить Campaign
- POST /api/campaigns/{id}/pause — поставить Campaign на паузу
"""

from uuid import UUID
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_async_db
from src.database.models import Campaign
from src.services.campaign_service import CampaignService, CampaignValidationError, CampaignNotFoundError

router = APIRouter()


# =============================================================================
# Pydantic схемы
# =============================================================================

class CampaignCreate(BaseModel):
    """Схема создания Campaign."""
    company_id: UUID
    skillbase_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Scheduling
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    daily_start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    daily_end_time: str = Field(default="18:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = Field(default="UTC")
    
    # Rate limiting
    max_concurrent_calls: int = Field(default=5, ge=1, le=100)
    calls_per_minute: int = Field(default=10, ge=1, le=100)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_minutes: int = Field(default=30, ge=1, le=1440)


class CampaignUpdate(BaseModel):
    """Схема обновления Campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    daily_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    daily_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: Optional[str] = None
    max_concurrent_calls: Optional[int] = Field(None, ge=1, le=100)
    calls_per_minute: Optional[int] = Field(None, ge=1, le=100)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_minutes: Optional[int] = Field(None, ge=1, le=1440)


class CampaignResponse(BaseModel):
    """Схема ответа Campaign."""
    id: UUID
    company_id: UUID
    skillbase_id: UUID
    name: str
    description: Optional[str]
    status: str
    
    # Scheduling
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    daily_start_time: str
    daily_end_time: str
    timezone: str
    
    # Rate limiting
    max_concurrent_calls: int
    calls_per_minute: int
    max_retries: int
    retry_delay_minutes: int
    
    # Stats
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Список Campaigns."""
    items: List[CampaignResponse]
    total: int


class CallListUploadResponse(BaseModel):
    """Результат загрузки списка контактов."""
    total: int = Field(..., description="Всего строк в файле")
    created: int = Field(..., description="Успешно созданных задач")
    errors: List[str] = Field(default_factory=list, description="Список ошибок")


# =============================================================================
# Эндпоинты
# =============================================================================

@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    company_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """
    Получить список Campaigns.
    
    Фильтры:
    - company_id: фильтр по компании
    - skillbase_id: фильтр по Skillbase
    - status: фильтр по статусу (draft, running, paused, completed)
    - skip: пропустить N записей (пагинация)
    - limit: максимум записей (default: 50)
    """
    async with get_async_db() as db:
        query = select(Campaign)
        
        if company_id:
            query = query.where(Campaign.company_id == company_id)
        if skillbase_id:
            query = query.where(Campaign.skillbase_id == skillbase_id)
        if status:
            query = query.where(Campaign.status == status)
        
        query = query.offset(skip).limit(limit).order_by(Campaign.created_at.desc())
        
        result = await db.execute(query)
        campaigns = list(result.scalars().all())
        
        # Считаем общее количество
        count_query = select(Campaign)
        if company_id:
            count_query = count_query.where(Campaign.company_id == company_id)
        if skillbase_id:
            count_query = count_query.where(Campaign.skillbase_id == skillbase_id)
        if status:
            count_query = count_query.where(Campaign.status == status)
        
        count_result = await db.execute(count_query)
        total = len(list(count_result.scalars().all()))
        
        return CampaignListResponse(
            items=[CampaignResponse.model_validate(c) for c in campaigns],
            total=total,
        )


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(data: CampaignCreate):
    """
    Создать новую Campaign.
    
    Валидирует company_id, skillbase_id и временные окна.
    """
    async with get_async_db() as db:
        service = CampaignService(db)
        
        try:
            campaign = await service.create(
                company_id=data.company_id,
                skillbase_id=data.skillbase_id,
                name=data.name,
                description=data.description,
                start_time=data.start_time,
                end_time=data.end_time,
                daily_start_time=data.daily_start_time,
                daily_end_time=data.daily_end_time,
                timezone=data.timezone,
                max_concurrent_calls=data.max_concurrent_calls,
                calls_per_minute=data.calls_per_minute,
                max_retries=data.max_retries,
                retry_delay_minutes=data.retry_delay_minutes,
            )
            
            return CampaignResponse.model_validate(campaign)
        
        except CampaignValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID):
    """
    Получить Campaign по ID.
    """
    async with get_async_db() as db:
        service = CampaignService(db)
        
        try:
            campaign = await service.get_by_id(campaign_id)
            return CampaignResponse.model_validate(campaign)
        
        except CampaignNotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: UUID, data: CampaignUpdate):
    """
    Обновить Campaign.
    
    ВНИМАНИЕ: Нельзя изменить company_id или skillbase_id после создания.
    """
    async with get_async_db() as db:
        campaign = await db.get(Campaign, campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Обновляем поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)
        
        try:
            await db.commit()
            await db.refresh(campaign)
            
            return CampaignResponse.model_validate(campaign)
        
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: UUID):
    """
    Удалить Campaign.
    
    ВНИМАНИЕ: Удаление Campaign удалит все связанные CallTasks (CASCADE).
    """
    async with get_async_db() as db:
        campaign = await db.get(Campaign, campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        await db.delete(campaign)
        await db.commit()


@router.post("/{campaign_id}/call-list", response_model=CallListUploadResponse)
async def upload_call_list(
    campaign_id: UUID,
    file: UploadFile = File(..., description="CSV or Excel file with contacts"),
):
    """
    Загрузить список контактов для Campaign.
    
    Поддерживаемые форматы: CSV (.csv), Excel (.xlsx, .xls)
    
    Обязательные колонки:
    - phone_number: номер телефона
    
    Опциональные колонки:
    - name или contact_name: имя контакта
    - Любые дополнительные поля сохраняются в contact_data (JSONB)
    
    Возвращает:
    - total: всего строк в файле
    - created: успешно созданных задач
    - errors: список ошибок (не останавливает процесс)
    """
    async with get_async_db() as db:
        service = CampaignService(db)
        
        try:
            # Читаем файл
            content = await file.read()
            
            # Загружаем список
            result = await service.upload_call_list(
                campaign_id=campaign_id,
                file_content=content,
                filename=file.filename or "upload.csv",
            )
            
            return CallListUploadResponse(**result)
        
        except CampaignNotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(campaign_id: UUID):
    """
    Запустить Campaign.
    
    Валидация:
    - Campaign не должна быть уже запущена
    - Campaign должна иметь задачи (total_tasks > 0)
    """
    async with get_async_db() as db:
        service = CampaignService(db)
        
        try:
            campaign = await service.start(campaign_id)
            return CampaignResponse.model_validate(campaign)
        
        except CampaignNotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        except CampaignValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(campaign_id: UUID):
    """
    Поставить Campaign на паузу.
    
    Останавливает обработку новых задач немедленно.
    Текущие активные звонки завершатся.
    """
    async with get_async_db() as db:
        service = CampaignService(db)
        
        try:
            campaign = await service.pause(campaign_id)
            return CampaignResponse.model_validate(campaign)
        
        except CampaignNotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")
