# MVP Backlog

## ✅ ВЫПОЛНЕНО (2026-01-12)

### Voice Pipeline — 100% ГОТОВО! 🎉
- [x] Deepgram STT — распознавание речи (русский)
- [x] Cartesia TTS — синтез речи (русский)
- [x] LiveKit Cloud — real-time стриминг
- [x] Silero VAD — определение голосовой активности
- [x] Ollama LLM — генерация ответов (qwen2:1.5b)
- [x] **Voice Agent работает и отвечает голосом!**

### Scenario Engine — 95% готово
- [x] Модели данных (models.py)
- [x] Загрузчик конфигов (config_loader.py)
- [x] Машина состояний (state_machine.py)
- [x] Контекст звонка (context_manager.py)
- [x] Извлечение данных (field_extractor.py)
- [x] Определение языка (language_detector.py)
- [x] Классификация результатов (outcome_classifier.py)
- [x] Основной движок (engine.py)

---

## Epic 1: Infrastructure Setup

### Stories

**1.1 Server Configuration**
- [x] Task: Update Ubuntu system
- [x] Task: Install Python 3.12
- [x] Task: Install Docker
- [x] Task: Install Git
- [x] Task: Setup virtual environment (venv)
- [x] Task: Install Ollama
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
- [x] Task: Configure environment variables (.env)
- [ ] Task: Setup Docker Compose for all services

---

## Epic 2: Provider Layer ✅ ГОТОВО

### Stories

**2.1 LLM Provider** ✅
- [x] Task: Create abstract LLM interface
- [x] Task: Implement Ollama provider
- [x] Task: Groq provider (заблокирован в РФ)
- [x] Task: Установить Ollama на сервер
- [x] Task: Протестировать qwen2:1.5b
- [x] Task: Интеграция с livekit-plugins-openai

**2.2 STT Provider** ✅
- [x] Task: Deepgram STT подключен
- [x] Task: Русский язык (nova-2)
- [x] Task: Real-time streaming через LiveKit

**2.3 TTS Provider** ✅
- [x] Task: Cartesia TTS подключен
- [x] Task: Русский язык (sonic-2)
- [x] Task: Streaming synthesis

**2.4 Telephony Provider** ⏳
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
- [ ] Task: Embeddings integration
- [ ] Task: Batch processing for large files

**3.3 Vector Storage**
- [ ] Task: Qdrant collection management
- [ ] Task: Per-bot namespace isolation
- [ ] Task: Semantic search implementation
- [ ] Task: Delete document with vectors

---

## Epic 4: Realtime Voice Agent ✅ ГОТОВО

### Stories

**4.1 LiveKit Integration** ✅
- [x] Task: LiveKit agent setup
- [x] Task: Room connection handling
- [x] Task: Audio stream processing

**4.2 Voice Pipeline** ✅
- [x] Task: STT → LLM → TTS orchestration
- [x] Task: VAD (Silero) для определения речи
- [x] Task: Работает на русском языке

**4.3 Conversation Logic** ⏳
- [ ] Task: Интеграция Scenario Engine
- [ ] Task: RAG integration in prompts
- [ ] Task: Field collection flow

---

## Epic 5: Scenario Engine ✅ 95% ГОТОВО

### Stories

**5.1 Config Parser** ✅
- [x] Task: YAML/JSON config schema
- [x] Task: Config validation
- [ ] Task: Hot reload support

**5.2 State Machine** ✅
- [x] Task: Гибкие этапы (клиент задаёт сам)
- [x] Task: Переходы между этапами
- [x] Task: Условия переходов

**5.3 Data Collection** ✅
- [x] Task: FieldExtractor — извлечение данных
- [x] Task: Валидация (телефон, дата, время, email)
- [x] Task: LanguageDetector — определение языка

**5.4 Outcome Classification** ✅
- [x] Task: OutcomeClassifier — классификация результатов
- [x] Task: Правила (LEAD, CALLBACK, INFO_ONLY, etc.)
- [x] Task: Сбор evidence

**5.5 Main Engine** ✅
- [x] Task: ScenarioEngine — основной движок
- [x] Task: start_call(), process_turn(), end_call()
- [x] Task: Интеграция всех компонентов
- [ ] Task: Подключить к Voice Agent

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

## Приоритет задач

### Ближайшие (эта неделя):
1. **Интеграция Scenario Engine + Voice Agent**
2. Телефония MTS Exolve

### Следующие:
3. RAG System (Qdrant)
4. Admin API
5. Admin UI
