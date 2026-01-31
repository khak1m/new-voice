"""API для управления лидами.

Эндпоинты (backend):
- GET /api/leads — список лидов
- POST /api/leads — создать лид (нужно фронту)
- GET /api/leads/{id} — получить лид
- PUT /api/leads/{id} — обновить лид (status/notes)
- DELETE /api/leads/{id} — удалить лид (нужно фронту)
- POST /api/leads/import — импорт лидов из файла (нужно фронту)
- GET /api/leads/export — экспорт лидов (нужно фронту)

Legacy/compat:
- GET /api/leads/export/csv — экспорт лидов в CSV
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

import io
from typing import List
from uuid import uuid4

import pandas as pd

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
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
    skillbase_id: Optional[UUID]
    campaign_id: Optional[UUID]
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


class LeadCreate(BaseModel):
    """Схема создания лида (минимально для фронта)."""

    company_id: Optional[UUID] = None
    call_id: Optional[UUID] = None
    skillbase_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    data: dict = Field(default_factory=dict)
    status: str = Field(default="new")
    notes: Optional[str] = None


# =============================================================================
# Эндпоинты
# =============================================================================


@router.get("", response_model=LeadListResponse)
async def list_leads(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
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
        if skillbase_id:
            query = query.where(Lead.skillbase_id == skillbase_id)
        if campaign_id:
            query = query.where(Lead.campaign_id == campaign_id)
        if status:
            query = query.where(Lead.status == status)

        # Считаем общее количество
        count_query = select(Lead)
        if company_id:
            count_query = count_query.where(Lead.company_id == company_id)
        if bot_id:
            count_query = count_query.where(Lead.bot_id == bot_id)
        if skillbase_id:
            count_query = count_query.where(Lead.skillbase_id == skillbase_id)
        if campaign_id:
            count_query = count_query.where(Lead.campaign_id == campaign_id)
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


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(data: LeadCreate):
    """Создать лид (используется фронтом для ручного добавления)."""
    async with get_async_db() as db:
        lead = Lead(
            id=uuid4(),
            company_id=data.company_id,
            call_id=data.call_id,
            skillbase_id=data.skillbase_id,
            campaign_id=data.campaign_id,
            name=data.name,
            phone=data.phone,
            email=data.email,
            data=data.data or {},
            status=data.status or "new",
            notes=data.notes,
        )

        db.add(lead)
        await db.commit()
        await db.refresh(lead)

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


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: UUID):
    """Удалить лид (нужно фронту)."""
    async with get_async_db() as db:
        lead = await db.get(Lead, lead_id)

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        await db.delete(lead)
        await db.commit()


@router.get("/stats/summary")
async def get_leads_stats(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
):
    """Получить статистику по лидам."""
    async with get_async_db() as db:
        query = select(Lead)

        if company_id:
            query = query.where(Lead.company_id == company_id)
        if bot_id:
            query = query.where(Lead.bot_id == bot_id)
        if skillbase_id:
            query = query.where(Lead.skillbase_id == skillbase_id)
        if campaign_id:
            query = query.where(Lead.campaign_id == campaign_id)

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


def _build_leads_csv(leads: List[Lead]) -> str:
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Имя", "Телефон", "Email", "Статус", "Дата создания", "Данные"]
    )
    for lead in leads:
        writer.writerow(
            [
                str(lead.id),
                lead.name or "",
                lead.phone or "",
                lead.email or "",
                lead.status or "",
                lead.created_at.isoformat() if lead.created_at else "",
                str(lead.data) if lead.data else "",
            ]
        )
    output.seek(0)
    return output.getvalue()


@router.get("/export")
async def export_leads(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    status: Optional[str] = None,
):
    """Экспорт лидов в CSV (нужно фронту: /leads/export)."""
    async with get_async_db() as db:
        query = select(Lead).order_by(desc(Lead.created_at))

        if company_id:
            query = query.where(Lead.company_id == company_id)
        if bot_id:
            query = query.where(Lead.bot_id == bot_id)
        if skillbase_id:
            query = query.where(Lead.skillbase_id == skillbase_id)
        if campaign_id:
            query = query.where(Lead.campaign_id == campaign_id)
        if status:
            query = query.where(Lead.status == status)

        result = await db.execute(query)
        leads = result.scalars().all()

        csv_text = _build_leads_csv(leads)

        return StreamingResponse(
            iter([csv_text]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads.csv"},
        )


@router.get("/export/csv")
async def export_leads_csv(
    company_id: Optional[UUID] = None,
    bot_id: Optional[UUID] = None,
    skillbase_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    status: Optional[str] = None,
):
    """Alias для совместимости: /leads/export/csv."""
    return await export_leads(
        company_id=company_id,
        bot_id=bot_id,
        skillbase_id=skillbase_id,
        campaign_id=campaign_id,
        status=status,
    )


@router.post("/import")
async def import_leads(file: UploadFile = File(...)):
    """Импорт лидов из CSV/Excel (нужно фронту: /leads/import).

    Ожидаемые колонки:
    - phone OR phone_number
    - name (optional)
    - email (optional)
    Любые остальные колонки попадут в Lead.data
    """
    async with get_async_db() as db:
        content = await file.read()
        filename = (file.filename or "").lower()

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(content))
            else:
                raise HTTPException(
                    status_code=400, detail="Unsupported file format. Use CSV or Excel"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

        # Normalize columns
        cols = {c.lower().strip(): c for c in df.columns}
        phone_col = cols.get("phone") or cols.get("phone_number")
        if not phone_col:
            raise HTTPException(
                status_code=400, detail="Missing required column: phone or phone_number"
            )

        name_col = cols.get("name")
        email_col = cols.get("email")

        created = 0
        errors: List[str] = []

        for idx, row in df.iterrows():
            try:
                phone = str(row[phone_col]).strip()
                if not phone or phone == "nan":
                    errors.append(f"Row {idx + 2}: Empty phone")
                    continue

                name = None
                if name_col is not None:
                    v = row.get(name_col)
                    if v is not None and str(v) != "nan":
                        name = str(v).strip()

                email = None
                if email_col is not None:
                    v = row.get(email_col)
                    if v is not None and str(v) != "nan":
                        email = str(v).strip()

                # Extra data
                extra = {}
                for c in df.columns:
                    if c in (phone_col, name_col, email_col):
                        continue
                    val = row.get(c)
                    if val is None or str(val) == "nan":
                        continue
                    extra[str(c)] = val

                lead = Lead(
                    id=uuid4(),
                    phone=phone,
                    name=name,
                    email=email,
                    data=extra,
                    status="new",
                )
                db.add(lead)
                created += 1
            except Exception as e:
                errors.append(f"Row {idx + 2}: {e}")

        await db.commit()

        return {
            "total": int(len(df)),
            "created": int(created),
            "errors": errors,
        }
