# Data Model

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Company   │──1:N──│     Bot     │──1:N──│    Call     │
└─────────────┘       └──────┬──────┘       └──────┬──────┘
                             │                     │
                            1:N                   1:1
                             │                     │
                      ┌──────▼──────┐       ┌──────▼──────┐
                      │  Knowledge  │       │   Outcome   │
                      └─────────────┘       └─────────────┘
```

## Tables

### Company

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    webhook_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR | Company name |
| api_key | VARCHAR | API authentication key |
| webhook_url | TEXT | Optional webhook for outcomes |
| is_active | BOOLEAN | Account status |

---

### Bot

```sql
CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    language VARCHAR(5) DEFAULT 'ru',
    
    -- Provider settings
    llm_provider VARCHAR(50) DEFAULT 'openai',
    llm_model VARCHAR(100) DEFAULT 'gpt-4-turbo',
    stt_provider VARCHAR(50) DEFAULT 'deepgram',
    tts_provider VARCHAR(50) DEFAULT 'cartesia',
    tts_voice_id VARCHAR(100),
    
    -- Scenario config (JSON)
    config JSONB NOT NULL DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bots_company ON bots(company_id);
CREATE INDEX idx_bots_phone ON bots(phone_number);
```

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| company_id | UUID | Owner company |
| name | VARCHAR | Bot display name |
| phone_number | VARCHAR | Assigned phone number |
| language | VARCHAR | ru / en |
| llm_provider | VARCHAR | openai / anthropic |
| llm_model | VARCHAR | Model name |
| stt_provider | VARCHAR | deepgram / whisper |
| tts_provider | VARCHAR | cartesia / elevenlabs |
| tts_voice_id | VARCHAR | Voice identifier |
| config | JSONB | Scenario configuration |

---

### Knowledge

```sql
CREATE TABLE knowledge_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    chunk_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'processing',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_bot ON knowledge_docs(bot_id);
```

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| bot_id | UUID | Owner bot |
| filename | VARCHAR | Original filename |
| file_type | VARCHAR | pdf / docx / txt / csv |
| file_size | INTEGER | Size in bytes |
| chunk_count | INTEGER | Number of chunks created |
| status | VARCHAR | processing / ready / error |

**Note:** Actual chunks stored in Qdrant with collection name = `bot_{bot_id}`

---

### Call

```sql
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID REFERENCES bots(id) ON DELETE SET NULL,
    
    -- Call info
    direction VARCHAR(10) NOT NULL, -- inbound / outbound
    caller_number VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    
    -- Timing
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_sec INTEGER,
    
    -- Content
    transcript JSONB DEFAULT '[]',
    audio_url TEXT,
    
    -- Processing
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP
);

CREATE INDEX idx_calls_bot ON calls(bot_id);
CREATE INDEX idx_calls_started ON calls(started_at DESC);
CREATE INDEX idx_calls_status ON calls(status);
```

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| bot_id | UUID | Bot that handled call |
| direction | VARCHAR | inbound / outbound |
| caller_number | VARCHAR | Caller phone |
| status | VARCHAR | active / completed / failed |
| duration_sec | INTEGER | Call duration |
| transcript | JSONB | Array of {role, text, timestamp} |
| audio_url | TEXT | Recording URL (optional) |
| processed | BOOLEAN | Post-call processing done |

---

### Outcome

```sql
CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID UNIQUE REFERENCES calls(id) ON DELETE CASCADE,
    
    -- Classification
    outcome_type VARCHAR(50) NOT NULL,
    confidence FLOAT,
    
    -- Extracted data
    summary TEXT,
    extracted_data JSONB DEFAULT '{}',
    
    -- Webhook
    webhook_sent BOOLEAN DEFAULT false,
    webhook_sent_at TIMESTAMP,
    webhook_response_code INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outcomes_call ON outcomes(call_id);
CREATE INDEX idx_outcomes_type ON outcomes(outcome_type);
```

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| call_id | UUID | Related call |
| outcome_type | VARCHAR | booking / lead / support / hangup |
| confidence | FLOAT | Classification confidence 0-1 |
| summary | TEXT | AI-generated summary |
| extracted_data | JSONB | Structured data (name, phone, etc) |
| webhook_sent | BOOLEAN | Webhook delivery status |

---

## Qdrant Collections

Each bot has its own collection:

```
Collection: bot_{bot_id}

Vector: 1536 dimensions (OpenAI embeddings)

Payload:
{
    "doc_id": "uuid",
    "text": "chunk text content",
    "source": "filename.pdf",
    "page": 1,
    "section": "Услуги",
    "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Sample Data

### Transcript Format (JSONB)

```json
[
    {"role": "bot", "text": "Здравствуйте! Салон красоты. Чем могу помочь?", "ts": 0.0},
    {"role": "user", "text": "Хочу записаться на маникюр", "ts": 2.5},
    {"role": "bot", "text": "Отлично! На какой день хотите записаться?", "ts": 4.0},
    {"role": "user", "text": "На завтра", "ts": 6.2}
]
```

### Extracted Data Format (JSONB)

```json
{
    "intent": "booking",
    "service": "маникюр",
    "date": "2024-01-15",
    "time": "14:00",
    "client_name": "Анна",
    "client_phone": "+79001234567"
}
```
