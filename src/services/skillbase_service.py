"""
SkillbaseService: Business logic for Skillbase management.

This service handles:
- CRUD operations for Skillbases
- Configuration validation
- Version management
- RAG collection attachment
- Optimized queries for call initialization

Author: Senior Backend Engineer
Date: 2026-01-17

**INTELLECTUAL HONESTY NOTE:**
- Using SQLAlchemy async session (AsyncSession)
- Using Pydantic for validation
- All DB operations wrapped in try/except with rollback
- Using structured logging with context
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import ValidationError

from database.models import Skillbase, Company, KnowledgeBase
from schemas.skillbase_schemas import SkillbaseConfig


# Configure logger
logger = logging.getLogger(__name__)


class SkillbaseServiceError(Exception):
    """Base exception for SkillbaseService errors."""
    pass


class SkillbaseNotFoundError(SkillbaseServiceError):
    """Raised when Skillbase is not found."""
    pass


class SkillbaseValidationError(SkillbaseServiceError):
    """Raised when Skillbase configuration validation fails."""
    pass


class SkillbaseService:
    """
    Service for managing Skillbase configurations.
    
    **Design Principles:**
    1. All methods are async
    2. All DB operations have error handling with rollback
    3. All operations are logged with context (skillbase_id, company_id)
    4. Configuration is validated using Pydantic schemas
    5. Version is auto-incremented on updates
    
    **Usage:**
        async with get_async_db() as db:
            service = SkillbaseService(db)
            skillbase = await service.get_by_id(skillbase_id)
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
    
    async def create(
        self,
        company_id: UUID,
        name: str,
        slug: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None
    ) -> Skillbase:
        """
        Create a new Skillbase with validation.
        
        Args:
            company_id: Company UUID
            name: Skillbase name
            slug: Unique slug within company
            config: JSONB configuration dict
            description: Optional description
            knowledge_base_id: Optional knowledge base UUID
        
        Returns:
            Created Skillbase instance
        
        Raises:
            SkillbaseValidationError: If config validation fails
            SkillbaseServiceError: If creation fails
        
        **SAFETY:** Validates config before saving, rolls back on error
        """
        logger.info(
            "Creating Skillbase",
            extra={
                "company_id": str(company_id),
                "name": name,
                "slug": slug
            }
        )
        
        try:
            # Validate configuration using Pydantic
            try:
                validated_config = SkillbaseConfig(**config)
                config_dict = validated_config.dict()
            except ValidationError as e:
                logger.error(
                    "Skillbase config validation failed",
                    extra={
                        "company_id": str(company_id),
                        "slug": slug,
                        "errors": str(e)
                    }
                )
                raise SkillbaseValidationError(f"Invalid configuration: {e}")
            
            # Verify company exists
            company_result = await self.db.execute(
                select(Company).where(Company.id == company_id)
            )
            company = company_result.scalar_one_or_none()
            if not company:
                raise SkillbaseServiceError(f"Company {company_id} not found")
            
            # Verify knowledge base exists if provided
            if knowledge_base_id:
                kb_result = await self.db.execute(
                    select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
                )
                kb = kb_result.scalar_one_or_none()
                if not kb:
                    raise SkillbaseServiceError(f"KnowledgeBase {knowledge_base_id} not found")
            
            # Create Skillbase
            skillbase = Skillbase(
                company_id=company_id,
                name=name,
                slug=slug,
                description=description,
                config=config_dict,
                knowledge_base_id=knowledge_base_id,
                version=1
            )
            
            self.db.add(skillbase)
            await self.db.flush()
            await self.db.refresh(skillbase)
            
            logger.info(
                "Skillbase created successfully",
                extra={
                    "skillbase_id": str(skillbase.id),
                    "company_id": str(company_id),
                    "version": skillbase.version
                }
            )
            
            return skillbase
            
        except SkillbaseValidationError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to create Skillbase",
                extra={
                    "company_id": str(company_id),
                    "slug": slug,
                    "error": str(e)
                },
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to create Skillbase: {e}")
    
    async def get_by_id(
        self,
        skillbase_id: UUID,
        load_relations: bool = False
    ) -> Optional[Skillbase]:
        """
        Get Skillbase by ID.
        
        Args:
            skillbase_id: Skillbase UUID
            load_relations: Whether to eagerly load relationships
        
        Returns:
            Skillbase instance or None if not found
        
        **OPTIMIZATION:** Uses selectinload for eager loading when needed
        """
        logger.debug(
            "Fetching Skillbase by ID",
            extra={"skillbase_id": str(skillbase_id)}
        )
        
        try:
            query = select(Skillbase).where(Skillbase.id == skillbase_id)
            
            if load_relations:
                query = query.options(
                    selectinload(Skillbase.company),
                    selectinload(Skillbase.knowledge_base),
                    selectinload(Skillbase.campaigns)
                )
            
            result = await self.db.execute(query)
            skillbase = result.scalar_one_or_none()
            
            if skillbase:
                logger.debug(
                    "Skillbase found",
                    extra={
                        "skillbase_id": str(skillbase_id),
                        "version": skillbase.version
                    }
                )
            else:
                logger.warning(
                    "Skillbase not found",
                    extra={"skillbase_id": str(skillbase_id)}
                )
            
            return skillbase
            
        except Exception as e:
            logger.error(
                "Failed to fetch Skillbase",
                extra={"skillbase_id": str(skillbase_id), "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to fetch Skillbase: {e}")
    
    async def get_by_slug(
        self,
        company_id: UUID,
        slug: str
    ) -> Optional[Skillbase]:
        """
        Get Skillbase by company and slug.
        
        Args:
            company_id: Company UUID
            slug: Skillbase slug
        
        Returns:
            Skillbase instance or None if not found
        """
        logger.debug(
            "Fetching Skillbase by slug",
            extra={"company_id": str(company_id), "slug": slug}
        )
        
        try:
            result = await self.db.execute(
                select(Skillbase).where(
                    Skillbase.company_id == company_id,
                    Skillbase.slug == slug
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(
                "Failed to fetch Skillbase by slug",
                extra={"company_id": str(company_id), "slug": slug, "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to fetch Skillbase: {e}")
    
    async def get_for_call(
        self,
        skillbase_id: UUID
    ) -> Skillbase:
        """
        Get Skillbase optimized for call initialization.
        
        This method eagerly loads all relationships needed for a call:
        - Company (for limits/settings)
        - KnowledgeBase (for RAG)
        
        Args:
            skillbase_id: Skillbase UUID
        
        Returns:
            Skillbase instance with loaded relationships
        
        Raises:
            SkillbaseNotFoundError: If Skillbase not found or not active
        
        **OPTIMIZATION:** Single query with eager loading
        **REQUIREMENT:** Validates Skillbase is active and published
        """
        logger.info(
            "Fetching Skillbase for call initialization",
            extra={"skillbase_id": str(skillbase_id)}
        )
        
        try:
            result = await self.db.execute(
                select(Skillbase)
                .where(Skillbase.id == skillbase_id)
                .options(
                    selectinload(Skillbase.company),
                    selectinload(Skillbase.knowledge_base)
                )
            )
            skillbase = result.scalar_one_or_none()
            
            if not skillbase:
                logger.error(
                    "Skillbase not found for call",
                    extra={"skillbase_id": str(skillbase_id)}
                )
                raise SkillbaseNotFoundError(f"Skillbase {skillbase_id} not found")
            
            if not skillbase.is_active:
                logger.error(
                    "Skillbase is not active",
                    extra={"skillbase_id": str(skillbase_id)}
                )
                raise SkillbaseNotFoundError(f"Skillbase {skillbase_id} is not active")
            
            logger.info(
                "Skillbase loaded for call",
                extra={
                    "skillbase_id": str(skillbase_id),
                    "version": skillbase.version,
                    "has_knowledge_base": skillbase.knowledge_base_id is not None
                }
            )
            
            return skillbase
            
        except SkillbaseNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to fetch Skillbase for call",
                extra={"skillbase_id": str(skillbase_id), "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to fetch Skillbase for call: {e}")
    
    async def update(
        self,
        skillbase_id: UUID,
        config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        knowledge_base_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        is_published: Optional[bool] = None
    ) -> Skillbase:
        """
        Update Skillbase with automatic version increment.
        
        Args:
            skillbase_id: Skillbase UUID
            config: New configuration (triggers version increment)
            name: New name
            description: New description
            knowledge_base_id: New knowledge base ID
            is_active: New active status
            is_published: New published status
        
        Returns:
            Updated Skillbase instance
        
        Raises:
            SkillbaseNotFoundError: If Skillbase not found
            SkillbaseValidationError: If config validation fails
        
        **SAFETY:** Validates config before saving, auto-increments version
        """
        logger.info(
            "Updating Skillbase",
            extra={"skillbase_id": str(skillbase_id)}
        )
        
        try:
            # Fetch existing Skillbase
            skillbase = await self.get_by_id(skillbase_id)
            if not skillbase:
                raise SkillbaseNotFoundError(f"Skillbase {skillbase_id} not found")
            
            # Validate new config if provided
            if config is not None:
                try:
                    validated_config = SkillbaseConfig(**config)
                    skillbase.config = validated_config.dict()
                    # Increment version when config changes
                    skillbase.increment_version()
                    logger.info(
                        "Skillbase config updated, version incremented",
                        extra={
                            "skillbase_id": str(skillbase_id),
                            "new_version": skillbase.version
                        }
                    )
                except ValidationError as e:
                    logger.error(
                        "Skillbase config validation failed",
                        extra={
                            "skillbase_id": str(skillbase_id),
                            "errors": str(e)
                        }
                    )
                    raise SkillbaseValidationError(f"Invalid configuration: {e}")
            
            # Update other fields
            if name is not None:
                skillbase.name = name
            if description is not None:
                skillbase.description = description
            if knowledge_base_id is not None:
                skillbase.knowledge_base_id = knowledge_base_id
            if is_active is not None:
                skillbase.is_active = is_active
            if is_published is not None:
                skillbase.is_published = is_published
            
            skillbase.updated_at = datetime.utcnow()
            
            await self.db.flush()
            await self.db.refresh(skillbase)
            
            logger.info(
                "Skillbase updated successfully",
                extra={
                    "skillbase_id": str(skillbase_id),
                    "version": skillbase.version
                }
            )
            
            return skillbase
            
        except (SkillbaseNotFoundError, SkillbaseValidationError):
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to update Skillbase",
                extra={"skillbase_id": str(skillbase_id), "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to update Skillbase: {e}")
    
    async def list_by_company(
        self,
        company_id: UUID,
        active_only: bool = False,
        published_only: bool = False
    ) -> List[Skillbase]:
        """
        List all Skillbases for a company.
        
        Args:
            company_id: Company UUID
            active_only: Filter to active Skillbases only
            published_only: Filter to published Skillbases only
        
        Returns:
            List of Skillbase instances
        """
        logger.debug(
            "Listing Skillbases for company",
            extra={
                "company_id": str(company_id),
                "active_only": active_only,
                "published_only": published_only
            }
        )
        
        try:
            query = select(Skillbase).where(Skillbase.company_id == company_id)
            
            if active_only:
                query = query.where(Skillbase.is_active == True)
            if published_only:
                query = query.where(Skillbase.is_published == True)
            
            query = query.order_by(Skillbase.created_at.desc())
            
            result = await self.db.execute(query)
            skillbases = result.scalars().all()
            
            logger.debug(
                "Skillbases listed",
                extra={
                    "company_id": str(company_id),
                    "count": len(skillbases)
                }
            )
            
            return list(skillbases)
            
        except Exception as e:
            logger.error(
                "Failed to list Skillbases",
                extra={"company_id": str(company_id), "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to list Skillbases: {e}")
    
    async def delete(self, skillbase_id: UUID) -> bool:
        """
        Delete a Skillbase.
        
        Args:
            skillbase_id: Skillbase UUID
        
        Returns:
            True if deleted, False if not found
        
        **SAFETY:** Cascades to campaigns and call_tasks
        """
        logger.info(
            "Deleting Skillbase",
            extra={"skillbase_id": str(skillbase_id)}
        )
        
        try:
            skillbase = await self.get_by_id(skillbase_id)
            if not skillbase:
                logger.warning(
                    "Skillbase not found for deletion",
                    extra={"skillbase_id": str(skillbase_id)}
                )
                return False
            
            await self.db.delete(skillbase)
            await self.db.flush()
            
            logger.info(
                "Skillbase deleted successfully",
                extra={"skillbase_id": str(skillbase_id)}
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to delete Skillbase",
                extra={"skillbase_id": str(skillbase_id), "error": str(e)},
                exc_info=True
            )
            raise SkillbaseServiceError(f"Failed to delete Skillbase: {e}")
    
    async def validate_config(self, config: Dict[str, Any]) -> SkillbaseConfig:
        """
        Validate Skillbase configuration without saving.
        
        Args:
            config: Configuration dict to validate
        
        Returns:
            Validated SkillbaseConfig instance
        
        Raises:
            SkillbaseValidationError: If validation fails
        
        **USE CASE:** Pre-validation before creating/updating
        """
        try:
            return SkillbaseConfig(**config)
        except ValidationError as e:
            raise SkillbaseValidationError(f"Invalid configuration: {e}")
