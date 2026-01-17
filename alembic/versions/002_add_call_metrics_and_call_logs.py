"""
Add call_metrics and call_logs tables.

Revision ID: 002
Revises: 001
Create Date: 2026-01-16

Enterprise Platform Phase 1 - Observability Tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Создаём таблицы для observability:
    - call_metrics: агрегированные метрики звонка (1:1 с calls)
    - call_logs: per-turn логи с детальными метриками
    """
    
    # ==========================================================================
    # CALL_METRICS - агрегированные метрики звонка
    # ==========================================================================
    op.create_table(
        'call_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('call_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False, unique=True),
        
        # ======================================================================
        # Latency Metrics (в миллисекундах)
        # ======================================================================
        # STT metrics
        sa.Column('ttfb_stt_avg', sa.Float),      # Time to First Byte STT (avg)
        sa.Column('ttfb_stt_min', sa.Float),
        sa.Column('ttfb_stt_max', sa.Float),
        
        # LLM metrics
        sa.Column('latency_llm_avg', sa.Float),   # LLM processing time (avg)
        sa.Column('latency_llm_min', sa.Float),
        sa.Column('latency_llm_max', sa.Float),
        
        # TTS metrics
        sa.Column('ttfb_tts_avg', sa.Float),      # Time to First Byte TTS (avg)
        sa.Column('ttfb_tts_min', sa.Float),
        sa.Column('ttfb_tts_max', sa.Float),
        
        # End-to-End metrics
        sa.Column('eou_latency_avg', sa.Float),   # End of Utterance to Audio Start (avg)
        sa.Column('eou_latency_min', sa.Float),
        sa.Column('eou_latency_max', sa.Float),
        
        # ======================================================================
        # Token & Duration Counts
        # ======================================================================
        sa.Column('stt_duration_sec', sa.Float, server_default='0'),    # Total STT audio duration
        sa.Column('llm_input_tokens', sa.Integer, server_default='0'),  # Total LLM input tokens
        sa.Column('llm_output_tokens', sa.Integer, server_default='0'), # Total LLM output tokens
        sa.Column('tts_characters', sa.Integer, server_default='0'),    # Total TTS characters
        sa.Column('livekit_duration_sec', sa.Float, server_default='0'),# LiveKit room duration
        
        # ======================================================================
        # Cost Breakdown (в USD или рублях - настраивается)
        # ======================================================================
        sa.Column('cost_stt', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_llm', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_tts', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_livekit', sa.Numeric(10, 6), server_default='0'),
        sa.Column('cost_total', sa.Numeric(10, 6), server_default='0'),
        
        # ======================================================================
        # Quality Metrics
        # ======================================================================
        sa.Column('interruption_count', sa.Integer, server_default='0'),
        sa.Column('interruption_rate', sa.Float),  # interruptions / turns
        sa.Column('sentiment_score', sa.Float),    # -1.0 to 1.0
        sa.Column('outcome', sa.String(50)),       # success, fail, voicemail, no_answer, busy
        sa.Column('outcome_confidence', sa.Float), # 0.0 to 1.0
        sa.Column('outcome_reason', sa.Text),
        
        # ======================================================================
        # Turn Statistics
        # ======================================================================
        sa.Column('turn_count', sa.Integer, server_default='0'),
        sa.Column('user_turn_count', sa.Integer, server_default='0'),
        sa.Column('bot_turn_count', sa.Integer, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Индексы для call_metrics
    op.create_index('idx_call_metrics_call', 'call_metrics', ['call_id'], unique=True)
    op.create_index('idx_call_metrics_outcome', 'call_metrics', ['outcome'])
    op.create_index('idx_call_metrics_created', 'call_metrics', ['created_at'])

    
    # ==========================================================================
    # CALL_LOGS - per-turn логи с детальными метриками
    # ==========================================================================
    op.create_table(
        'call_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('call_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('calls.id', ondelete='CASCADE'), nullable=False),
        
        # Turn identification
        sa.Column('turn_index', sa.Integer, nullable=False),  # 0, 1, 2, ...
        sa.Column('role', sa.String(20), nullable=False),     # user, assistant
        
        # Content
        sa.Column('content', sa.Text),
        sa.Column('state_id', sa.String(100)),  # Scenario state at this turn
        
        # ======================================================================
        # Per-Turn Latency Metrics (в миллисекундах)
        # ======================================================================
        sa.Column('ttfb_stt', sa.Float),      # Time to First Byte STT
        sa.Column('latency_stt', sa.Float),   # Full STT processing time
        sa.Column('latency_llm', sa.Float),   # LLM processing time
        sa.Column('ttfb_tts', sa.Float),      # Time to First Byte TTS
        sa.Column('latency_tts', sa.Float),   # Full TTS processing time
        sa.Column('eou_latency', sa.Float),   # End of Utterance to Audio Start
        
        # ======================================================================
        # Per-Turn Token Counts
        # ======================================================================
        sa.Column('stt_duration_sec', sa.Float),
        sa.Column('llm_input_tokens', sa.Integer),
        sa.Column('llm_output_tokens', sa.Integer),
        sa.Column('tts_characters', sa.Integer),
        
        # ======================================================================
        # Per-Turn Quality
        # ======================================================================
        sa.Column('was_interrupted', sa.Boolean, server_default='false'),
        sa.Column('sentiment', sa.Float),  # Per-turn sentiment
        
        # Metadata
        sa.Column('extra_data', postgresql.JSONB, server_default='{}'),
        
        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Индексы для call_logs
    op.create_index('idx_call_logs_call', 'call_logs', ['call_id'])
    op.create_index('idx_call_logs_call_turn', 'call_logs', ['call_id', 'turn_index'])
    op.create_index('idx_call_logs_created', 'call_logs', ['created_at'])
    
    # Комментарии
    op.execute("COMMENT ON TABLE call_metrics IS 'Aggregated call metrics for analytics (1:1 with calls)'")
    op.execute("COMMENT ON TABLE call_logs IS 'Per-turn call logs with detailed metrics'")


def downgrade() -> None:
    """Откат миграции."""
    op.drop_table('call_logs')
    op.drop_table('call_metrics')
