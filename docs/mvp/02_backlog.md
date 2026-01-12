# MVP Backlog

## Epic 1: Infrastructure Setup

### Stories

**1.1 Server Configuration**
- [x] Task: Update Ubuntu system
- [x] Task: Install Python 3.12
- [x] Task: Install Docker
- [x] Task: Install Git
- [ ] Task: Configure firewall (UFW)
- [ ] Task: Setup SSL certificates

**1.2 Database Setup**
- [ ] Task: Deploy PostgreSQL container
- [ ] Task: Create database schema
- [ ] Task: Setup Qdrant container
- [ ] Task: Configure Redis for queues

**1.3 Project Setup**
- [x] Task: Create GitHub repository
- [x] Task: Setup project structure
- [ ] Task: Configure environment variables
- [ ] Task: Setup Docker Compose for all services

---

## Epic 2: Provider Layer

### Stories

**2.1 LLM Provider**
- [x] Task: Create abstract LLM interface
- [x] Task: Implement Ollama provider (локальный)
- [x] Task: Implement Groq provider (заблокирован в РФ)
- [x] Task: Установить Ollama на сервер ✅
- [x] Task: Протестировать на сервере ✅
- [ ] Task: Add streaming support
- [ ] Task: Add error handling and retries

**2.2 STT Provider**
- [ ] Task: Create abstract STT interface
- [ ] Task: Implement Deepgram provider
- [ ] Task: Add real-time streaming
- [ ] Task: Handle connection drops

**2.3 TTS Provider**
- [ ] Task: Create abstract TTS interface
- [ ] Task: Implement Cartesia provider
- [ ] Task: Add streaming synthesis
- [ ] Task: Voice selection support


**2.4 Telephony Provider**
- [ ] Task: Create abstract telephony interface
- [ ] Task: Implement MTS Exolve provider
- [ ] Task: SIP to LiveKit bridge
- [ ] Task: Call status webhooks

---

## Epic 3: Knowledge System (RAG)

### Stories

**3.1 File Processing**
- [ ] Task: File upload endpoint
- [ ] Task: PDF parser
- [ ] Task: DOCX parser
- [ ] Task: TXT/CSV parser
- [ ] Task: File validation

**3.2 Chunking & Embeddings**
- [ ] Task: Text chunking logic
- [ ] Task: OpenAI embeddings integration
- [ ] Task: Batch processing for large files

**3.3 Vector Storage**
- [ ] Task: Qdrant collection management
- [ ] Task: Per-bot namespace isolation
- [ ] Task: Semantic search implementation
- [ ] Task: Delete document with vectors

---

## Epic 4: Realtime Voice Agent

### Stories

**4.1 LiveKit Integration**
- [ ] Task: LiveKit agent setup
- [ ] Task: Room connection handling
- [ ] Task: Audio stream processing

**4.2 Voice Pipeline**
- [ ] Task: STT → LLM → TTS orchestration
- [ ] Task: Interrupt handling
- [ ] Task: Silence detection
- [ ] Task: Latency optimization

**4.3 Conversation Logic**
- [ ] Task: Context management
- [ ] Task: RAG integration in prompts
- [ ] Task: Scenario state machine
- [ ] Task: Field collection flow

---

## Epic 5: Scenario Engine

### Stories

**5.1 Config Parser**
- [x] Task: YAML/JSON config schema
- [x] Task: Config validation
- [ ] Task: Hot reload support

**5.2 State Machine**
- [x] Task: Гибкие этапы (клиент задаёт сам)
- [x] Task: Переходы между этапами
- [x] Task: Условия переходов

**5.3 Data Collection**
- [x] Task: FieldExtractor — извлечение данных
- [x] Task: Валидация (телефон, дата, время, email)
- [x] Task: LanguageDetector — определение языка

**5.4 Outcome Classification**
- [x] Task: OutcomeClassifier — классификация результатов
- [x] Task: Правила (LEAD, CALLBACK, INFO_ONLY, etc.)
- [x] Task: Сбор evidence

**5.5 Main Engine**
- [x] Task: ScenarioEngine — основной движок
- [x] Task: start_call(), process_turn(), end_call()
- [x] Task: Интеграция всех компонентов
- [ ] Task: Подключить реальный LLM (Ollama)

---

## Epic 6: Post-Call Processing

### Stories

**6.1 Queue System**
- [ ] Task: Redis queue setup
- [ ] Task: Worker process
- [ ] Task: Retry logic

**6.2 Call Analysis**
- [ ] Task: Summary generation
- [ ] Task: Outcome classification
- [ ] Task: Data extraction

**6.3 Webhook Delivery**
- [ ] Task: Webhook sender
- [ ] Task: Retry with backoff
- [ ] Task: Delivery logging

---

## Epic 7: Admin API

### Stories

**7.1 Authentication**
- [ ] Task: API key generation
- [ ] Task: Key validation middleware
- [ ] Task: Rate limiting (basic)

**7.2 Company Endpoints**
- [ ] Task: CRUD operations
- [ ] Task: Webhook configuration

**7.3 Bot Endpoints**
- [ ] Task: CRUD operations
- [ ] Task: Config update
- [ ] Task: Phone number assignment

**7.4 Knowledge Endpoints**
- [ ] Task: File upload
- [ ] Task: List documents
- [ ] Task: Delete document

**7.5 Call Endpoints**
- [ ] Task: List calls with filters
- [ ] Task: Call details + transcript
- [ ] Task: Outcome retrieval

---

## Epic 8: Admin UI (Basic)

### Stories

**8.1 Dashboard**
- [ ] Task: Login page
- [ ] Task: Company selector
- [ ] Task: Basic stats

**8.2 Bot Management**
- [ ] Task: Bot list view
- [ ] Task: Bot create/edit form
- [ ] Task: Config editor

**8.3 Knowledge Management**
- [ ] Task: File upload UI
- [ ] Task: Document list
- [ ] Task: Delete confirmation

**8.4 Call Logs**
- [ ] Task: Call list with filters
- [ ] Task: Transcript viewer
- [ ] Task: Outcome display

---

## Priority Order

1. **Week 1-2:** Epic 1 (Infrastructure) + Epic 2 (Providers)
2. **Week 2-3:** Epic 3 (Knowledge) + Epic 4 (Voice Agent)
3. **Week 3-4:** Epic 5 (Scenarios) + Epic 6 (Post-Call)
4. **Week 4-5:** Epic 7 (API) + Epic 8 (UI)
5. **Week 5-6:** Integration testing + Bug fixes
