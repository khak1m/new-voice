"""
SQLAlchemy models for NEW-VOICE 2.0.

Модели соответствуют схеме в scripts/init_db.sql.
"""

import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, JSON, UniqueConstraint, Numeric
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
    extra_data = Column(JSON, default=dict)  # renamed from metadata (reserved)
    
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
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"))  # Legacy, для обратной совместимости
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    
    # Enterprise Platform fields
    skillbase_id = Column(UUID(as_uuid=True), ForeignKey("skillbases.id", ondelete="SET NULL"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"))
    
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
    skillbase = relationship("Skillbase", backref="calls")
    campaign = relationship("Campaign", backref="calls")
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
    extra_data = Column(JSON, default=dict)  # renamed from metadata (reserved)
    
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
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id", ondelete="SET NULL"))  # Legacy
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"))
    
    # Enterprise Platform fields
    skillbase_id = Column(UUID(as_uuid=True), ForeignKey("skillbases.id", ondelete="SET NULL"))
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"))
    
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
    skillbase = relationship("Skillbase", backref="leads")
    campaign = relationship("Campaign", backref="leads")
    
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


# =============================================================================
# SKILLBASES (Enterprise Platform)
# =============================================================================

class Skillbase(Base):
    """
    Skillbase — комплексная конфигурация бота.
    
    Хранит в JSONB:
    - context: role, style, safety_rules, facts
    - flow: states, transitions (linear или graph)
    - agent: handoff_criteria, crm_field_mapping
    - tools: function calling definitions
    - voice: tts/stt настройки
    - llm: provider, model, temperature
    
    Это замена простого Bot.scenario_config на полноценный
    enterprise-grade конфиг с версионированием.
    """
    
    __tablename__ = "skillbases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    # Основные поля
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    version = Column(Integer, default=1, nullable=False)
    
    # JSONB конфигурация — гибкая схема
    config = Column(JSON, nullable=False, default=dict)
    # Структура config:
    # {
    #   "context": {"role": "", "style": "", "safety_rules": [], "facts": []},
    #   "flow": {"type": "linear|graph", "states": [], "transitions": []},
    #   "agent": {"handoff_criteria": {}, "crm_field_mapping": {}},
    #   "tools": [{"name": "calendar", "config": {}}],
    #   "voice": {"tts_provider": "", "tts_voice_id": "", "stt_provider": "", "stt_language": ""},
    #   "llm": {"provider": "", "model": "", "temperature": 0.7}
    # }
    
    # Связь с базой знаний
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="SET NULL"))
    
    # Статусы
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_skillbases_company_slug"),
    )
    
    # Relationships
    company = relationship("Company", backref="skillbases")
    knowledge_base = relationship("KnowledgeBase", backref="skillbases")
    campaigns = relationship("Campaign", back_populates="skillbase", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Skillbase {self.name} v{self.version}>"
    
    def increment_version(self):
        """Увеличить версию при обновлении конфига."""
        self.version += 1
        self.updated_at = datetime.utcnow()


# =============================================================================
# CAMPAIGNS (Enterprise Platform)
# =============================================================================

class Campaign(Base):
    """
    Campaign — кампания исходящих звонков.
    
    Управляет:
    - Списком контактов для обзвона
    - Расписанием (когда звонить)
    - Rate limiting (сколько звонков в минуту)
    - Статистикой выполнения
    """
    
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    skillbase_id = Column(UUID(as_uuid=True), ForeignKey("skillbases.id", ondelete="CASCADE"), nullable=False)
    
    # Основные поля
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Статус кампании
    status = Column(String(50), default="draft")  # draft, scheduled, running, paused, completed
    
    # Расписание
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    daily_start_time = Column(String(5))  # "09:00"
    daily_end_time = Column(String(5))    # "21:00"
    timezone = Column(String(50), default="Europe/Moscow")
    
    # Rate limiting
    max_concurrent_calls = Column(Integer, default=5)
    calls_per_minute = Column(Integer, default=10)
    max_retries = Column(Integer, default=3)
    retry_delay_minutes = Column(Integer, default=30)
    
    # Статистика (денормализовано для быстрого доступа)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", backref="campaigns")
    skillbase = relationship("Skillbase", back_populates="campaigns")
    call_tasks = relationship("CallTask", back_populates="campaign", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campaign {self.name} ({self.status})>"


# =============================================================================
# CALL TASKS (Enterprise Platform)
# =============================================================================

class CallTask(Base):
    """
    CallTask — задача на звонок в очереди кампании.
    
    Каждая строка = один контакт для обзвона.
    Отслеживает статус, попытки, результат.
    """
    
    __tablename__ = "call_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    
    # Контактные данные
    phone_number = Column(String(50), nullable=False)
    contact_name = Column(String(255))
    contact_data = Column(JSON, default=dict)  # Дополнительные поля из CSV
    
    # Статус
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed, retry
    
    # Попытки
    attempt_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone=True))
    next_attempt_at = Column(DateTime(timezone=True))
    
    # Результат
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="SET NULL"))
    outcome = Column(String(50))  # success, fail, voicemail, no_answer, busy
    error_message = Column(Text)
    
    # Приоритет (для сортировки очереди)
    priority = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="call_tasks")
    call = relationship("Call", backref="call_task")
    
    def __repr__(self):
        return f"<CallTask {self.phone_number} ({self.status})>"


# =============================================================================
# CALL METRICS (Enterprise Platform - Observability)
# =============================================================================

class CallMetrics(Base):
    """
    CallMetrics — агрегированные метрики звонка для аналитики.
    
    1:1 связь с Call. Хранит:
    - Latency metrics: STT, LLM, TTS, End-to-End
    - Token counts: input/output tokens, characters, duration
    - Cost breakdown: по каждому провайдеру + total
    - Quality metrics: interruptions, sentiment, outcome
    """
    
    __tablename__ = "call_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # ==========================================================================
    # Latency Metrics (в миллисекундах)
    # ==========================================================================
    # STT metrics
    ttfb_stt_avg = Column(Float)      # Time to First Byte STT (avg)
    ttfb_stt_min = Column(Float)
    ttfb_stt_max = Column(Float)
    
    # LLM metrics
    latency_llm_avg = Column(Float)   # LLM processing time (avg)
    latency_llm_min = Column(Float)
    latency_llm_max = Column(Float)
    
    # TTS metrics
    ttfb_tts_avg = Column(Float)      # Time to First Byte TTS (avg)
    ttfb_tts_min = Column(Float)
    ttfb_tts_max = Column(Float)
    
    # End-to-End metrics
    eou_latency_avg = Column(Float)   # End of Utterance to Audio Start (avg)
    eou_latency_min = Column(Float)
    eou_latency_max = Column(Float)
    
    # ==========================================================================
    # Token & Duration Counts
    # ==========================================================================
    stt_duration_sec = Column(Float, default=0.0)    # Total STT audio duration
    llm_input_tokens = Column(Integer, default=0)    # Total LLM input tokens
    llm_output_tokens = Column(Integer, default=0)   # Total LLM output tokens
    tts_characters = Column(Integer, default=0)      # Total TTS characters
    livekit_duration_sec = Column(Float, default=0.0) # LiveKit room duration
    
    # ==========================================================================
    # Cost Breakdown (в USD или рублях - настраивается)
    # ==========================================================================
    cost_stt = Column(Numeric(10, 6), default=0)
    cost_llm = Column(Numeric(10, 6), default=0)
    cost_tts = Column(Numeric(10, 6), default=0)
    cost_livekit = Column(Numeric(10, 6), default=0)
    cost_total = Column(Numeric(10, 6), default=0)
    
    # ==========================================================================
    # Quality Metrics
    # ==========================================================================
    interruption_count = Column(Integer, default=0)
    interruption_rate = Column(Float)  # interruptions / turns
    sentiment_score = Column(Float)    # -1.0 to 1.0
    outcome = Column(String(50))       # success, fail, voicemail, no_answer, busy
    outcome_confidence = Column(Float) # 0.0 to 1.0
    outcome_reason = Column(Text)
    
    # ==========================================================================
    # Turn Statistics
    # ==========================================================================
    turn_count = Column(Integer, default=0)
    user_turn_count = Column(Integer, default=0)
    bot_turn_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", backref="metrics", uselist=False)
    
    def __repr__(self):
        return f"<CallMetrics call_id={self.call_id} cost_total={self.cost_total}>"


# =============================================================================
# CALL LOGS (Enterprise Platform - Per-Turn Metrics)
# =============================================================================

class CallLog(Base):
    """
    CallLog — per-turn логи с детальными метриками.
    
    Каждая запись = один turn в диалоге.
    Хранит детальные метрики для каждого хода:
    - Latency по каждому компоненту
    - Token counts для этого turn
    - Quality metrics (interruptions, sentiment)
    """
    
    __tablename__ = "call_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    
    # Turn identification
    turn_index = Column(Integer, nullable=False)  # 0, 1, 2, ...
    role = Column(String(20), nullable=False)     # user, assistant
    
    # Content
    content = Column(Text)
    state_id = Column(String(100))  # Scenario state at this turn
    
    # ==========================================================================
    # Per-Turn Latency Metrics (в миллисекундах)
    # ==========================================================================
    ttfb_stt = Column(Float)      # Time to First Byte STT
    latency_stt = Column(Float)   # Full STT processing time
    latency_llm = Column(Float)   # LLM processing time
    ttfb_tts = Column(Float)      # Time to First Byte TTS
    latency_tts = Column(Float)   # Full TTS processing time
    eou_latency = Column(Float)   # End of Utterance to Audio Start
    
    # ==========================================================================
    # Per-Turn Token Counts
    # ==========================================================================
    stt_duration_sec = Column(Float)
    llm_input_tokens = Column(Integer)
    llm_output_tokens = Column(Integer)
    tts_characters = Column(Integer)
    
    # ==========================================================================
    # Per-Turn Quality
    # ==========================================================================
    was_interrupted = Column(Boolean, default=False)
    sentiment = Column(Float)  # Per-turn sentiment
    
    # Metadata
    extra_data = Column(JSON, default=dict)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    call = relationship("Call", backref="logs")
    
    def __repr__(self):
        return f"<CallLog call_id={self.call_id} turn={self.turn_index} role={self.role}>"