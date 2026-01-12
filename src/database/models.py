"""
SQLAlchemy models for NEW-VOICE 2.0.

Модели соответствуют схеме в scripts/init_db.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# =============================================================================
# КОМПАНИИ
# =============================================================================

class Company(Base):
    """Компания — клиент платформы."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    
    settings = Column(JSON, default=dict)
    limits = Column(JSON, default={"bots": 5, "calls_per_month": 1000})
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="company", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", back_populates="company", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="company")
    leads = relationship("Lead", back_populates="company")
    webhooks = relationship("Webhook", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company {self.slug}>"


# =============================================================================
# ПОЛЬЗОВАТЕЛИ
# =============================================================================

class User(Base):
    """Пользователь — админ компании."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    role = Column(String(50), default="admin")  # admin, manager, viewer
    
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.email}>"


# =============================================================================
# БОТЫ
# =============================================================================

class Bot(Base):
    """Бот — голосовой ассистент."""
    
    __tablename__ = "bots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Конфигурация
    scenario_config = Column(JSON, nullable=False, default=dict)
    voice_config = Column(JSON, default={
        "tts_provider": "cartesia",
        "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
        "stt_provider": "deepgram",
        "stt_language": "ru"
    })
    llm_config = Column(JSON, default={
        "provider": "ollama",
        "model": "qwen2:1.5b",
        "temperature": 0.7
    })
    
    phone_numbers = Column(JSON, default=list)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="SET NULL"))
    
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_bots_company_slug"),
    )
    
    # Relationships
    company = relationship("Company", back_populates="bots")
    knowledge_base = relationship("KnowledgeBase", back_populates="bots")
    calls = relationship("Call", back_populates="bot")
    leads = relationship("Lead", back_populates="bot")
    webhooks = relationship("Webhook", back_populates="bot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bot {self.name}>"


# =============================================================================
# БАЗЫ ЗНАНИЙ
# =============================================================================

class KnowledgeBase(Base):
    """База знаний для RAG."""
    
    __tablename__ = "knowledge_bases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    qdrant_collection = Column(String(255))
    
    settings = Column(JSON, default={
        "chunk_size": 500,
        "chunk_overlap": 50,
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    })
    
    document_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    last_indexed_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="knowledge_base")
    
    def __repr__(self):
        return f"<KnowledgeBase {self.name}>"


# =============================================================================
# ДОКУМЕНТЫ
# =============================================================================

class Document(Base):
    """Документ в базе знаний."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"))
    
    title = Column(String(500))
    source_type = Column(String(50), nullable=False)  # file, url, text
    source_url = Column(Text)
    
    content = Column(Text)
    content_hash = Column(String(64))
    metadata = Column(JSON, default=dict)
    
    is_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime(timezone=True))
    chunk_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    def __repr__(self):
        return f"<Document {self.title}>"


# =============================================================================
# ЗВОНКИ
# =============================================================================

class Call(Base):
    """Звонок."""
    
    __tablename__ = "calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    
    external_call_id = Column(String(255))
    livekit_room_id = Column(String(255))
    
    direction = Column(String(20), nullable=False)  # inbound, outbound
    caller_number = Column(String(50))
    callee_number = Column(String(50))
    
    outcome = Column(String(50))  # lead, callback, info_only, not_target, failed
    outcome_data = Column(JSON, default=dict)
    collected_data = Column(JSON, default=dict)
    
    duration_sec = Column(Integer, default=0)
    turn_count = Column(Integer, default=0)
    states_visited = Column(JSON, default=list)
    language = Column(String(10), default="ru")
    
    status = Column(String(50), default="active")  # active, completed, failed, transferred
    ended_reason = Column(String(100))
    
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    bot = relationship("Bot", back_populates="calls")
    company = relationship("Company", back_populates="calls")
    messages = relationship("Message", back_populates="call", cascade="all, delete-orphan")
    lead = relationship("Lead", back_populates="call", uselist=False)
    
    def __repr__(self):
        return f"<Call {self.id} ({self.direction})>"


# =============================================================================
# СООБЩЕНИЯ
# =============================================================================

class Message(Base):
    """Сообщение в диалоге."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"))
    
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    state_id = Column(String(100))
    metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.role}: {self.content[:50]}...>"


# =============================================================================
# ЛИДЫ
# =============================================================================

class Lead(Base):
    """Лид — собранный контакт."""
    
    __tablename__ = "leads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="SET NULL"))
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"))
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    
    name = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    data = Column(JSON, default=dict)
    
    status = Column(String(50), default="new")  # new, contacted, converted, rejected
    notes = Column(Text)
    
    webhook_sent = Column(Boolean, default=False)
    webhook_sent_at = Column(DateTime(timezone=True))
    webhook_response = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", back_populates="lead")
    bot = relationship("Bot", back_populates="leads")
    company = relationship("Company", back_populates="leads")
    
    def __repr__(self):
        return f"<Lead {self.name or self.phone}>"


# =============================================================================
# WEBHOOKS
# =============================================================================

class Webhook(Base):
    """Webhook для отправки данных."""
    
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"))
    
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    trigger_on = Column(JSON, default=["lead", "callback"])
    headers = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_triggered_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="webhooks")
    bot = relationship("Bot", back_populates="webhooks")
    
    def __repr__(self):
        return f"<Webhook {self.name}>"
