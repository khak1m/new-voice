"""Utilities for resolving company identifiers.

Frontend currently sends a string company id (e.g. "default-company")
instead of a UUID. To keep frontend working without a full auth system,
we support:

1) UUID string -> lookup by id
2) slug string -> lookup by slug (auto-create if missing)
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Company


async def resolve_company(
    db: AsyncSession,
    company_id_or_slug: str,
    *,
    create_if_missing: bool = True,
    default_name: Optional[str] = None,
) -> Company:
    """Resolve a company from UUID or slug.

    Raises ValueError if company cannot be resolved.
    """

    if not company_id_or_slug or not str(company_id_or_slug).strip():
        raise ValueError("company_id is required")

    value = str(company_id_or_slug).strip()

    # Try UUID
    try:
        company_uuid = UUID(value)
        company = await db.get(Company, company_uuid)
        if company:
            return company
    except Exception:
        pass

    # Treat as slug
    result = await db.execute(select(Company).where(Company.slug == value))
    company = result.scalar_one_or_none()
    if company:
        return company

    if not create_if_missing:
        raise ValueError(f"Company '{value}' not found")

    company = Company(
        name=default_name or value,
        slug=value,
        is_active=True,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company
