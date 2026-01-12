-- =============================================================================
-- NEW-VOICE 2.0 — Схема базы данных
-- =============================================================================
-- PostgreSQL 16
-- Создаётся автоматически при первом запуске docker-compose
-- =============================================================================

-- Расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- КОМПАНИИ (клиенты платформы)
-- =============================================================================
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,          -- URL-friendly имя
    email VARCHAR(255),
    phone VARCHAR(50),
    
    -- Настройки
    settings JSONB DEFAULT '{}',                -- Общие настройки компании
    limits JSONB DEFAULT '{"bots": 5, "calls_per_month": 1000}',
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ПОЛЬЗОВАТЕЛИ (админы компаний)
-- =============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',           -- admin, manager, viewer
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- БОТЫ
-- =============================================================================
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,                 -- Уникальный в рамках компании
    description TEXT,
    
    -- Конфигурация сценария (YAML/JSON)
    scenario_config JSONB NOT NULL DEFAULT '{}',
    
    -- Настройки голоса
    voice_config JSONB DEFAULT '{
        "tts_provider": "cartesia",
        "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
        "stt_provider": "deepgram",
        "stt_language": "ru"
    }',
    
    -- Настройки LLM
    llm_config JSONB DEFAULT '{
        "provider": "ollama",
        "model": "qwen2:1.5b",
        "temperature": 0.7
    }',
    
    -- Телефония
    phone_numbers JSONB DEFAULT '[]',           -- Привязанные номера
    
    -- RAG
    knowledge_base_id UUID,                     -- Ссылка на базу знаний
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    is_published BOOLEAN DEFAULT false,         -- Опубликован для звонков
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(company_id, slug)
);

-- =============================================================================
-- БАЗЫ ЗНАНИЙ (для RAG)
-- =============================================================================
CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Qdrant collection name
    qdrant_collection VARCHAR(255),
    
    -- Настройки
    settings JSONB DEFAULT '{
        "chunk_size": 500,
        "chunk_overlap": 50,
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    }',
    
    -- Статистика
    document_count INT DEFAULT 0,
    chunk_count INT DEFAULT 0,
    last_indexed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Связь бота с базой знаний
ALTER TABLE bots ADD CONSTRAINT fk_bots_knowledge_base 
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL;

-- =============================================================================
-- ДОКУМЕНТЫ (для RAG)
-- =============================================================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    
    title VARCHAR(500),
    source_type VARCHAR(50) NOT NULL,           -- file, url, text
    source_url TEXT,                            -- URL или путь к файлу
    
    -- Контент
    content TEXT,                               -- Оригинальный текст
    content_hash VARCHAR(64),                   -- SHA256 для дедупликации
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',
    
    -- Статус индексации
    is_indexed BOOLEAN DEFAULT false,
    indexed_at TIMESTAMP WITH TIME ZONE,
    chunk_count INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ЗВОНКИ
-- =============================================================================
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bot_id UUID REFERENCES bots(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    
    -- Идентификаторы
    external_call_id VARCHAR(255),              -- ID от телефонии
    livekit_room_id VARCHAR(255),               -- ID комнаты LiveKit
    
    -- Направление и номера
    direction VARCHAR(20) NOT NULL,             -- inbound, outbound
    caller_number VARCHAR(50),
    callee_number VARCHAR(50),
    
    -- Результат
    outcome VARCHAR(50),                        -- lead, callback, info_only, not_target, failed
    outcome_data JSONB DEFAULT '{}',
    
    -- Собранные данные
    collected_data JSONB DEFAULT '{}',
    
    -- Метрики
    duration_sec INT DEFAULT 0,
    turn_count INT DEFAULT 0,
    states_visited JSONB DEFAULT '[]',
    language VARCHAR(10) DEFAULT 'ru',
    
    -- Статус
    status VARCHAR(50) DEFAULT 'active',        -- active, completed, failed, transferred
    ended_reason VARCHAR(100),
    
    -- Время
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- СООБЩЕНИЯ (история диалогов)
-- =============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    
    role VARCHAR(20) NOT NULL,                  -- user, assistant, system
    content TEXT NOT NULL,
    
    -- Контекст
    state_id VARCHAR(100),                      -- ID этапа сценария
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',                -- Доп. данные (confidence, etc.)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ЛИДЫ (собранные контакты)
-- =============================================================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    bot_id UUID REFERENCES bots(id) ON DELETE SET NULL,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    
    -- Контактные данные
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    
    -- Все собранные данные
    data JSONB DEFAULT '{}',
    
    -- Статус обработки
    status VARCHAR(50) DEFAULT 'new',           -- new, contacted, converted, rejected
    notes TEXT,
    
    -- Webhook
    webhook_sent BOOLEAN DEFAULT false,
    webhook_sent_at TIMESTAMP WITH TIME ZONE,
    webhook_response JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- WEBHOOKS (настройки отправки данных)
-- =============================================================================
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    
    -- Когда отправлять
    trigger_on JSONB DEFAULT '["lead", "callback"]',  -- Какие outcomes
    
    -- Настройки
    headers JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    
    -- Статистика
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ИНДЕКСЫ
-- =============================================================================

-- Компании
CREATE INDEX idx_companies_slug ON companies(slug);
CREATE INDEX idx_companies_is_active ON companies(is_active);

-- Пользователи
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_email ON users(email);

-- Боты
CREATE INDEX idx_bots_company_id ON bots(company_id);
CREATE INDEX idx_bots_slug ON bots(company_id, slug);
CREATE INDEX idx_bots_is_active ON bots(is_active);

-- Базы знаний
CREATE INDEX idx_knowledge_bases_company_id ON knowledge_bases(company_id);

-- Документы
CREATE INDEX idx_documents_knowledge_base_id ON documents(knowledge_base_id);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Звонки
CREATE INDEX idx_calls_bot_id ON calls(bot_id);
CREATE INDEX idx_calls_company_id ON calls(company_id);
CREATE INDEX idx_calls_started_at ON calls(started_at);
CREATE INDEX idx_calls_outcome ON calls(outcome);
CREATE INDEX idx_calls_status ON calls(status);

-- Сообщения
CREATE INDEX idx_messages_call_id ON messages(call_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Лиды
CREATE INDEX idx_leads_company_id ON leads(company_id);
CREATE INDEX idx_leads_bot_id ON leads(bot_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at);

-- Webhooks
CREATE INDEX idx_webhooks_company_id ON webhooks(company_id);
CREATE INDEX idx_webhooks_bot_id ON webhooks(bot_id);

-- =============================================================================
-- ТРИГГЕРЫ для updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON bots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_bases_updated_at BEFORE UPDATE ON knowledge_bases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- ТЕСТОВЫЕ ДАННЫЕ (опционально)
-- =============================================================================

-- Тестовая компания
INSERT INTO companies (id, name, slug, email) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'AI Prosto', 'aiprosto', 'admin@aiprosto.ru');

-- Тестовый пользователь (пароль: admin123)
INSERT INTO users (company_id, email, password_hash, name, role) VALUES 
    ('00000000-0000-0000-0000-000000000001', 'admin@aiprosto.ru', 
     crypt('admin123', gen_salt('bf')), 'Администратор', 'admin');

COMMENT ON TABLE companies IS 'Компании — клиенты платформы';
COMMENT ON TABLE users IS 'Пользователи — админы компаний';
COMMENT ON TABLE bots IS 'Боты — голосовые ассистенты';
COMMENT ON TABLE knowledge_bases IS 'Базы знаний для RAG';
COMMENT ON TABLE documents IS 'Документы в базах знаний';
COMMENT ON TABLE calls IS 'История звонков';
COMMENT ON TABLE messages IS 'Сообщения в диалогах';
COMMENT ON TABLE leads IS 'Собранные лиды';
COMMENT ON TABLE webhooks IS 'Настройки webhook-ов';
