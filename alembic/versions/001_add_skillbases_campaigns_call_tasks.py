"""
Add skillbases, campaigns, call_tasks tables.

Revision ID: 001
Revises: 
Create Date: 2026-01-16

Enterprise Platform Phase 1 - Foundation & Data Model
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Создаём 3 новые таблицы для Enterprise Platform:
    - skillbases: комплексная конфигурация ботов с JSONB
    - campaigns: кампании исходящих звонков
    - call_tasks: очередь задач на звонки
    """
    
    # ==========================================================================
    # SKILLBASES - конфигурация ботов
    # ==========================================================================
    op.create_table(
        'skillbases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        
        # Основные поля
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        
        # JSONB конфигурация - гибкая схема
        sa.Column('config', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Связь с базой знаний
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('knowledge_bases.id', ondelete='SET NULL')),
        
        # Статусы
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_published', sa.Boolean, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        
        # Уникальность slug в рамках компании
        sa.UniqueConstraint('company_id', 'slug', name='uq_skillbases_company_slug'),
    )
    
    # Индексы для skillbases
    op.create_index('idx_skillbases_company', 'skillbases', ['company_id'])
    op.create_index('idx_skillbases_active', 'skillbases', ['is_active', 'is_published'])
    
    # ==========================================================================
    # CAMPAIGNS - кампании исходящих звонков
    # ==========================================================================
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skillbase_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('skillbases.id', ondelete='CASCADE'), nullable=False),
        
        # Основные поля
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        
        # Статус
        sa.Column('status', sa.String(50), server_default='draft'),
        
        # Расписание
        sa.Column('start_time', sa.DateTime(timezone=True)),
        sa.Column('end_time', sa.DateTime(timezone=True)),
        sa.Column('daily_start_time', sa.String(5)),  # "09:00"
        sa.Column('daily_end_time', sa.String(5)),    # "21:00"
        sa.Column('timezone', sa.String(50), server_default="'Europe/Moscow'"),
        
        # Rate limiting
        sa.Column('max_concurrent_calls', sa.Integer, server_default='5'),
        sa.Column('calls_per_minute', sa.Integer, server_default='10'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('retry_delay_minutes', sa.Integer, server_default='30'),
        
        # Статистика (денормализовано)
        sa.Column('total_tasks', sa.Integer, server_default='0'),
        sa.Column('completed_tasks', sa.Integer, server_default='0'),
        sa.Column('failed_tasks', sa.Integer, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Индексы для campaigns
    op.create_index('idx_campaigns_company', 'campaigns', ['company_id'])
    op.create_index('idx_campaigns_skillbase', 'campaigns', ['skillbase_id'])
    op.create_index('idx_campaigns_status', 'campaigns', ['status'])
    
    # ==========================================================================
    # CALL_TASKS - очередь задач на звонки
    # ==========================================================================
    op.create_table(
        'call_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False),
        
        # Контактные данные
        sa.Column('phone_number', sa.String(50), nullable=False),
        sa.Column('contact_name', sa.String(255)),
        sa.Column('contact_data', postgresql.JSONB, server_default='{}'),
        
        # Статус
        sa.Column('status', sa.String(50), server_default='pending'),
        
        # Попытки
        sa.Column('attempt_count', sa.Integer, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True)),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True)),
        
        # Результат
        sa.Column('call_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('calls.id', ondelete='SET NULL')),
        sa.Column('outcome', sa.String(50)),
        sa.Column('error_message', sa.Text),
        
        # Приоритет
        sa.Column('priority', sa.Integer, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Индексы для call_tasks
    op.create_index('idx_call_tasks_campaign', 'call_tasks', ['campaign_id'])
    op.create_index('idx_call_tasks_status', 'call_tasks', ['status'])
    # Составной индекс для выборки pending задач
    op.create_index(
        'idx_call_tasks_pending',
        'call_tasks',
        ['campaign_id', 'status', 'next_attempt_at'],
        postgresql_where=sa.text("status IN ('pending', 'retry')")
    )
    
    # Комментарии к таблицам
    op.execute("COMMENT ON TABLE skillbases IS 'Enterprise bot configurations with JSONB config'")
    op.execute("COMMENT ON TABLE campaigns IS 'Outbound calling campaigns'")
    op.execute("COMMENT ON TABLE call_tasks IS 'Individual call tasks in campaign queue'")


def downgrade() -> None:
    """Откат миграции - удаляем таблицы в обратном порядке."""
    op.drop_table('call_tasks')
    op.drop_table('campaigns')
    op.drop_table('skillbases')
