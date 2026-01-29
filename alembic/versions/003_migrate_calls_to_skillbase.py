"""Migrate calls from bot_id to skillbase_id and add campaign_id

Revision ID: 003
Revises: 002
Create Date: 2026-01-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Миграция Call и Lead моделей:
    1. Добавить skillbase_id и campaign_id в calls
    2. Добавить skillbase_id и campaign_id в leads
    3. Мигрировать данные из bot_id в skillbase_id (если есть связь)
    4. Сделать bot_id опциональным (для обратной совместимости)
    """
    
    # =========================================================================
    # CALLS TABLE
    # =========================================================================
    
    # Добавляем новые колонки в calls
    op.add_column('calls', sa.Column('skillbase_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('calls', sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Создаём foreign keys для calls
    op.create_foreign_key(
        'fk_calls_skillbase_id',
        'calls', 'skillbases',
        ['skillbase_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_calls_campaign_id',
        'calls', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Создаём индексы для производительности calls
    op.create_index('ix_calls_skillbase_id', 'calls', ['skillbase_id'])
    op.create_index('ix_calls_campaign_id', 'calls', ['campaign_id'])
    
    # =========================================================================
    # LEADS TABLE
    # =========================================================================
    
    # Добавляем новые колонки в leads
    op.add_column('leads', sa.Column('skillbase_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('leads', sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Создаём foreign keys для leads
    op.create_foreign_key(
        'fk_leads_skillbase_id',
        'leads', 'skillbases',
        ['skillbase_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.create_foreign_key(
        'fk_leads_campaign_id',
        'leads', 'campaigns',
        ['campaign_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Создаём индексы для производительности leads
    op.create_index('ix_leads_skillbase_id', 'leads', ['skillbase_id'])
    op.create_index('ix_leads_campaign_id', 'leads', ['campaign_id'])
    
    # =========================================================================
    # DATA MIGRATION (опционально)
    # =========================================================================
    
    # Мигрируем данные: если у бота есть соответствующий skillbase, копируем
    # Это опционально - можно запустить отдельным скриптом
    # op.execute("""
    #     UPDATE calls c
    #     SET skillbase_id = s.id
    #     FROM bots b
    #     JOIN skillbases s ON s.company_id = b.company_id AND s.name = b.name
    #     WHERE c.bot_id = b.id
    # """)
    #
    # op.execute("""
    #     UPDATE leads l
    #     SET skillbase_id = s.id
    #     FROM bots b
    #     JOIN skillbases s ON s.company_id = b.company_id AND s.name = b.name
    #     WHERE l.bot_id = b.id
    # """)


def downgrade() -> None:
    """Откат миграции"""
    
    # =========================================================================
    # LEADS TABLE
    # =========================================================================
    
    # Удаляем индексы leads
    op.drop_index('ix_leads_campaign_id', table_name='leads')
    op.drop_index('ix_leads_skillbase_id', table_name='leads')
    
    # Удаляем foreign keys leads
    op.drop_constraint('fk_leads_campaign_id', 'leads', type_='foreignkey')
    op.drop_constraint('fk_leads_skillbase_id', 'leads', type_='foreignkey')
    
    # Удаляем колонки leads
    op.drop_column('leads', 'campaign_id')
    op.drop_column('leads', 'skillbase_id')
    
    # =========================================================================
    # CALLS TABLE
    # =========================================================================
    
    # Удаляем индексы calls
    op.drop_index('ix_calls_campaign_id', table_name='calls')
    op.drop_index('ix_calls_skillbase_id', table_name='calls')
    
    # Удаляем foreign keys calls
    op.drop_constraint('fk_calls_campaign_id', 'calls', type_='foreignkey')
    op.drop_constraint('fk_calls_skillbase_id', 'calls', type_='foreignkey')
    
    # Удаляем колонки calls
    op.drop_column('calls', 'campaign_id')
    op.drop_column('calls', 'skillbase_id')
