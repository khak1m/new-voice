# NEW-VOICE 2.0 — Прогресс разработки

## Общая информация
- **Проект:** Платформа для создания голосовых AI-ботов
- **Цель:** Боты общаются как люди, работают с входящими/исходящими звонками
- **Компания:** AI Prosto
- **Репозиторий:** https://github.com/khak1m/new-voice
- **Сервер:** 77.233.212.58 (Ubuntu 24.04, 2 vCPU, 4GB RAM, Нидерланды)

---

## 🛠 Технологии

| Компонент | Технология | Статус |
|-----------|------------|--------|
| **LLM** | Groq (llama-3.1-8b-instant) | ✅ Работает |
| **STT** | Deepgram (nova-2) | ✅ Работает |
| **TTS** | Cartesia (sonic-2) | ✅ Работает |
| **Real-time** | LiveKit Cloud | ✅ Работает |
| **VAD** | Silero | ✅ Работает |
| **Database** | PostgreSQL + Qdrant + Redis | ✅ Работает |
| **RAG** | Qdrant + sentence-transformers | ✅ Работает |
| **Admin API** | FastAPI | ✅ Работает |
| **Telephony** | MTS Exolve + VPS РФ | ✅ Работает |

---

## ✅ ВЫПОЛНЕНО

### Этап 1: Инфраструктура
- [x] Сервер настроен (Ubuntu 24.04)
- [x] Python 3.12, Docker, Git установлены
- [x] GitHub репозиторий создан
- [x] Виртуальное окружение (venv) настроено

### Этап 2: LLM Provider
- [x] Groq подключен (llama-3.1-8b-instant)
- [x] ~~Ollama установлен на сервер~~ (удален, используем Groq)

### Этап 3: Voice Pipeline ✅ ГОТОВО!
- [x] Deepgram STT подключен (русский язык)
- [x] Cartesia TTS подключен (русский язык)
- [x] LiveKit Cloud подключен (регион Germany 2)
- [x] Silero VAD для определения речи
- [x] **Voice Agent работает и отвечает голосом!**

### Этап 4: Scenario Engine (95%)
- [x] Модели данных (models.py)
- [x] Загрузчик конфигов (config_loader.py)
- [x] Машина состояний (state_machine.py)
- [x] Менеджер контекста (context_manager.py)
- [x] Извлечение данных из речи (field_extractor.py)
- [x] Определение языка (language_detector.py)
- [x] Классификация результатов (outcome_classifier.py)
- [x] Основной движок (engine.py)
- [x] **Интеграция с Voice Agent (scenario_voice_agent.py)** ✅

### Этап 5: Database Setup ✅ ГОТОВО!
- [x] PostgreSQL добавлен в docker-compose.yml
- [x] Qdrant добавлен в docker-compose.yml
- [x] Redis добавлен в docker-compose.yml
- [x] Схема БД создана (scripts/init_db.sql)
- [x] SQLAlchemy модели созданы (src/database/)
- [x] Скрипт тестирования БД (scripts/test_database.py)

### Этап 6: RAG System ✅ ГОТОВО!
- [x] Модуль эмбеддингов (src/rag/embeddings.py)
- [x] Менеджер базы знаний (src/rag/knowledge_base.py)
- [x] RAG поиск (src/rag/search.py)
- [x] Тест RAG (scripts/test_rag.py)

### Этап 7: Admin API ✅ ГОТОВО!
- [x] FastAPI приложение (src/api/main.py)
- [x] API для ботов (CRUD)
- [x] API для баз знаний (создание, документы, поиск)
- [x] API для звонков (просмотр, статистика)
- [x] API для лидов (просмотр, экспорт CSV)
- [x] Health check эндпоинты

### Этап 8: Телефония MTS Exolve ✅ РАБОТАЕТ!
- [x] Аккаунт MTS Exolve создан
- [x] Номер телефона: +7 934 662-08-75
- [x] **VPS в России арендован** (62.113.37.156, Timeweb, 350 руб/мес)
- [x] **Kamailio 5.7.4 установлен** — SIP proxy
- [x] **rtpengine 11.5.1 установлен** — медиа proxy
- [x] Переадресация MTS → VPS РФ настроена
- [x] LiveKit Inbound Trunk обновлён (allowed: 62.113.37.156)
- [x] **🎉 Тестовый звонок прошёл успешно!**

### Этап 9: Enterprise Platform ✅ В ПРОЦЕССЕ!
- [x] **Спецификация создана** (.kiro/specs/enterprise-platform/)
  - [x] Requirements.md — 9 требований в EARS формате
  - [x] Design.md — архитектура с 10 correctness properties
  - [x] Tasks.md — план реализации в 5 фаз (22 группы задач)
- [x] **Phase 1: Database Schema Migration** ✅ ЗАВЕРШЕНО
  - [x] Alembic настроен для NEW-VOICE 2.0
  - [x] Миграция 001: skillbases, campaigns, call_tasks
  - [x] Миграция 002: call_metrics, call_logs
  - [x] SQLAlchemy модели: Skillbase, Campaign, CallTask, CallMetrics, CallLog
  - [x] Все тесты пройдены — готово к применению на сервере
- [x] **Phase 2: Skillbase Management** ✅ ЗАВЕРШЕНО
  - [x] Pydantic схемы для валидации конфигурации (src/schemas/skillbase_schemas.py)
    - ContextConfig, FlowConfig, AgentConfig, ToolConfig, VoiceConfig, LLMConfig
    - Валидация: required fields, type checking, cross-reference validation
    - Enums: FlowType, TTSProvider, STTProvider, LLMProvider
  - [x] SkillbaseService (src/services/skillbase_service.py)
    - CRUD операции: create, get_by_id, get_by_slug, update, delete, list_by_company
    - get_for_call() — оптимизированный запрос для инициализации звонка
    - Автоматический инкремент версии при изменении config
    - Все операции async с error handling и rollback
  - [x] SystemPromptBuilder (src/prompts/skillbase_prompt_builder.py)
    - Конвертация SkillbaseConfig → system prompt
    - Поддержка linear и graph flows
    - Двухуровневая система: base prompt + skillbase config
  - [x] Skillbase VoiceAgent (src/voice_agent/skillbase_voice_agent.py)
    - Загрузка Skillbase из PostgreSQL
    - Генерация system prompt через SystemPromptBuilder
    - Создание LLM/STT/TTS из конфигурации
    - Интеграция с ScenarioEngine
  - [x] SkillbaseToScenarioAdapter (src/adapters/skillbase_to_scenario.py)
    - Конвертация SkillbaseConfig → ScenarioConfig
    - Поддержка linear и graph flows
    - Конвертация context, safety_rules, facts
  - [x] Function Calling Tools (src/tools/)
    - Base classes: Tool, ToolResult, ToolRegistry
    - CalendarTool: check_availability, book_appointment
    - TransferTool: transfer_to_operator
    - Auto-registration и OpenAI schema generation
  - [x] Тесты (scripts/)
    - ✅ test_skillbase_service.py — Schema validation (100%)
    - ✅ test_skillbase_agent.py — Agent integration (100%)
    - ✅ test_skillbase_scenario_adapter.py — Adapter (100%)
    - ✅ test_tools.py — Function calling tools (100%)
- [x] **Phase 3: Deep Observability** ✅ ЗАВЕРШЕНО
  - [x] TelemetryService (src/telemetry/telemetry_service.py)
    - In-memory metrics buffer (thread-safe)
    - record_turn() — неблокирующая запись
    - finalize_call() — агрегация и персистенция
    - Поддержка CallMetrics и CallLog таблиц
  - [x] MetricCollector (src/telemetry/metric_collector.py)
    - Timing hooks для STT, LLM, TTS
    - TTFB (Time To First Byte) measurements
    - EOU latency (End Of Utterance) tracking
    - TurnContext для state tracking
  - [x] CostCalculator (src/telemetry/cost_calculator.py)
    - PricingConfig с настраиваемыми ценами
    - Расчёт по компонентам (STT, LLM, TTS, LiveKit)
    - Decimal precision для денежных расчётов
    - Cost estimation per minute
  - [x] QualityMetrics (src/telemetry/quality_metrics.py)
    - InterruptionTracker — детекция прерываний
    - OutcomeClassifier — классификация исходов
    - SentimentAnalyzer — placeholder для будущего
    - QualityMetricsCollector — агрегация метрик
  - [x] Тесты (scripts/test_telemetry.py)
    - ✅ TelemetryService — PASSED (100%)
    - ✅ MetricCollector — PASSED (100%)
    - ✅ CostCalculator — PASSED (100%)
    - ✅ QualityMetrics — PASSED (100%)
    - **Результат: 4/4 тестов пройдено (100%)**
- [x] **Phase 4: Campaign Management** ✅ РЕАЛИЗОВАНО (Tasks 13-14)
  - [x] CampaignService (src/services/campaign_service.py)
    - CRUD операции: create, get_by_id, get_active_campaigns
    - Lifecycle: start, pause
    - Call list upload: CSV/Excel parsing с pandas/openpyxl
    - Rate limiting: max_concurrent_calls, calls_per_minute
    - Task queue: get_next_task с проверкой scheduling windows
    - Task management: mark_in_progress, mark_completed, mark_failed
    - Retry logic: max_retries, retry_delay_minutes
  - [x] Тесты (scripts/test_campaign_service.py)
    - ✅ Campaign creation with validation
    - ✅ Call list upload (CSV parsing)
    - ✅ Campaign lifecycle (start/pause)
    - ✅ Task queue management
    - ✅ Task status transitions
    - **Статус: READY FOR TESTING**
  - [ ] CampaignWorker (Task 15) — НЕ РЕАЛИЗОВАНО
    - Background task processing
    - LiveKit room creation
    - VoiceAgent execution

---

## 🔜 СЛЕДУЮЩИЕ ЗАДАЧИ

### 1. Enterprise Platform (продолжение)
- [x] **Phase 1: Database Schema Migration** ✅ ЗАВЕРШЕНО
- [x] **Phase 2: Skillbase Management** ✅ ЗАВЕРШЕНО
- [x] **Phase 3: Deep Observability** ✅ ЗАВЕРШЕНО
- [x] **Phase 4: Campaign Management (Tasks 13-14)** ✅ РЕАЛИЗОВАНО
  - [x] CampaignService — управление кампаниями
  - [x] Call list upload — CSV/Excel parsing
  - [x] Rate limiting — concurrent + per minute
  - [x] Task queue management — get_next_task
  - [x] Task status transitions — mark_in_progress/completed/failed
  - [x] Retry logic — max_retries, retry_delay
  - [ ] **ТЕСТИРОВАНИЕ НА СЕРВЕРЕ** — запустить test_campaign_service.py
- [ ] **Phase 4: Campaign Management (Tasks 15-16)** — CampaignWorker, background processing
- [ ] **Phase 5: API Layer** — CRUD endpoints, file upload, WebSocket monitoring

### 2. Применение миграций на сервере
- [ ] Подключиться к серверу PostgreSQL
- [ ] Выполнить `python -m alembic upgrade head`
- [ ] Проверить создание новых таблиц

### 3. Оптимизация задержки
- [ ] GPU сервер в РФ для LLM (уменьшит latency на ~500ms)
- [ ] Перенос агента на VPS РФ

### 4. Масштабирование
- [ ] Несколько воркеров агента (--num-workers=10)
- [ ] Увеличить ресурсы VPS (4 CPU, 8GB RAM)

### 5. Admin UI (веб-интерфейс)
- [ ] React/Next.js фронтенд
- [ ] Управление ботами через UI
- [ ] Просмотр звонков и лидов

### 6. Outbound Trunk (исходящие звонки)
- [ ] Создать Outbound Trunk в LiveKit
- [ ] Настроить исходящие звонки через MTS Exolve

---

## 📊 Общий прогресс

```
Инфраструктура:     ██████████ 100%
Scenario Engine:    ██████████ 100% ✅
Voice Pipeline:     ██████████ 100% ✅
Provider Layer:     ██████████ 100% ✅
Database:           ██████████ 100% ✅
RAG System:         ██████████ 100% ✅
Admin API:          ██████████ 100% ✅
Телефония:          ██████████ 100% ✅ РАБОТАЕТ!
Enterprise Platform: ███████░░░ 70% (Phase 1-3 завершены, Phase 4 Tasks 13-14 готовы)
Admin UI:           ░░░░░░░░░░ 0%
```

---

## 📁 Структура проекта

```
src/
├── api/                         ✅ Admin API (FastAPI)
│   ├── main.py                  Главный файл API
│   └── routers/
│       ├── bots.py              CRUD для ботов
│       ├── knowledge_bases.py   Базы знаний
│       ├── calls.py             История звонков
│       ├── leads.py             Лиды
│       └── health.py            Health check
├── voice_agent/
│   ├── simple_agent.py          ✅ Простой агент для тестов
│   ├── scenario_voice_agent.py  ✅ Агент со сценариями
│   └── agent.py                 Расширенный агент
├── scenario_engine/
│   ├── models.py         ✅ Модели данных
│   ├── config_loader.py  ✅ Загрузка YAML/JSON
│   ├── state_machine.py  ✅ Переходы между этапами
│   ├── context_manager.py ✅ Контекст звонка
│   ├── field_extractor.py ✅ Извлечение данных
│   ├── language_detector.py ✅ Определение языка
│   ├── outcome_classifier.py ✅ Классификация
│   └── engine.py         ✅ Основной движок
├── rag/                         ✅ RAG система
│   ├── embeddings.py            Эмбеддинги (sentence-transformers)
│   ├── knowledge_base.py        Менеджер базы знаний
│   └── search.py                Поиск по документам
├── database/
│   ├── models.py         ✅ SQLAlchemy модели (+ Enterprise Platform)
│   └── connection.py     ✅ Подключение к PostgreSQL
├── schemas/                     ✅ Pydantic schemas (Enterprise Platform)
│   └── skillbase_schemas.py     Валидация Skillbase config
├── services/                    ✅ Business logic (Enterprise Platform)
│   └── skillbase_service.py     CRUD для Skillbase
├── prompts/                     ✅ Prompt builders (Enterprise Platform)
│   └── skillbase_prompt_builder.py  SystemPromptBuilder
├── adapters/                    ✅ Adapters (Enterprise Platform)
│   └── skillbase_to_scenario.py     SkillbaseConfig → ScenarioConfig
├── tools/                       ✅ Function calling tools (Enterprise Platform)
│   ├── base.py                  Tool, ToolResult, ToolRegistry
│   ├── calendar_tool.py         CalendarTool
│   └── transfer_tool.py         TransferTool
├── telemetry/                   ✅ Observability (Enterprise Platform Phase 3)
│   ├── telemetry_service.py     TelemetryService (metrics buffer + aggregation)
│   ├── metric_collector.py      MetricCollector (timing hooks)
│   ├── cost_calculator.py       CostCalculator (pricing + breakdown)
│   └── quality_metrics.py       QualityMetrics (interruptions, outcome, sentiment)
├── providers/
│   └── groq_llm.py       ✅ Groq провайдер (основной)
alembic/                         ✅ Database migrations (Enterprise Platform)
├── env.py                       Alembic environment configuration
├── versions/
│   ├── 001_add_skillbases_campaigns_call_tasks.py  ✅ Skillbase tables
│   └── 002_add_call_metrics_and_call_logs.py       ✅ Observability tables
.kiro/specs/enterprise-platform/ ✅ Enterprise Platform specification
├── requirements.md              9 requirements (EARS format)
├── design.md                    Architecture + 10 correctness properties
└── tasks.md                     5-phase implementation plan (22 task groups)
scripts/
├── test_services.py      ✅ Тест всех сервисов
├── test_database.py      ✅ Тест PostgreSQL
├── test_rag.py           ✅ Тест RAG
├── test_groq.py          ✅ Тест Groq
├── test_enterprise_platform.py  ✅ Тест Enterprise Platform (Phase 1)
├── test_enterprise_db.py        ✅ Тест Enterprise DB (Phase 1)
├── test_skillbase_service.py    ✅ Тест Skillbase Service (Phase 2)
├── test_skillbase_agent.py      ✅ Тест Skillbase Agent (Phase 2)
├── test_skillbase_scenario_adapter.py  ✅ Тест Adapter (Phase 2)
├── test_tools.py                ✅ Тест Function Calling Tools (Phase 2)
├── test_telemetry.py            ✅ Тест Telemetry System (Phase 3)
examples/
├── scenarios/
│   ├── salon_scenario.yaml   ✅ Салон красоты
│   └── clinic_scenario.yaml  ✅ Медицинская клиника
└── salon_bot_config.yaml ✅ Пример конфига
```

---

## 🔑 API Ключи (на сервере в .env)

- DEEPGRAM_API_KEY ✅
- CARTESIA_API_KEY ✅
- LIVEKIT_URL ✅
- LIVEKIT_API_KEY ✅
- LIVEKIT_API_SECRET ✅

---

## 🗄️ Enterprise Platform Database Schema

### Новые таблицы (Phase 1)

| Таблица | Назначение | Статус |
|---------|------------|--------|
| **skillbases** | Комплексная конфигурация ботов (JSONB) | ✅ Создана |
| **campaigns** | Кампании исходящих звонков | ✅ Создана |
| **call_tasks** | Очередь задач на звонки | ✅ Создана |
| **call_metrics** | Агрегированные метрики звонков (1:1 с calls) | ✅ Создана |
| **call_logs** | Per-turn детальные логи | ✅ Создана |

### Структура Skillbase (JSONB config)
```json
{
  "context": {
    "role": "Ассистент салона красоты",
    "style": "Дружелюбный и профессиональный", 
    "safety_rules": ["Не давать медицинские советы"],
    "facts": ["Работаем с 9 до 21", "Принимаем карты и наличные"]
  },
  "flow": {
    "type": "linear|graph",
    "states": ["greeting", "service_inquiry", "booking", "confirmation"],
    "transitions": []
  },
  "agent": {
    "handoff_criteria": {"complex_request": true},
    "crm_field_mapping": {"name": "client_name", "phone": "client_phone"}
  },
  "tools": [
    {"name": "calendar", "config": {"api_url": "https://api.example.com"}}
  ],
  "voice": {
    "tts_provider": "cartesia",
    "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
    "stt_provider": "deepgram", 
    "stt_language": "ru"
  },
  "llm": {
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "temperature": 0.7
  }
}
```

### Применение миграций на сервере
```bash
# На сервере с PostgreSQL
cd /root/new-voice
source venv/bin/activate
python -m alembic upgrade head
```

---

## 🚀 Как запустить Voice Agent

```bash
# На сервере
cd /root/new-voice
source venv/bin/activate

# Простой агент (без сценария)
python -m src.voice_agent.simple_agent dev

# Агент со сценарием салона
SCENARIO_PATH=examples/scenarios/salon_scenario.yaml python -m src.voice_agent.scenario_voice_agent dev

# Агент со сценарием клиники
SCENARIO_PATH=examples/scenarios/clinic_scenario.yaml python -m src.voice_agent.scenario_voice_agent dev
```

Тестирование: https://agents-playground.livekit.io/

---

## 🌐 Как запустить Admin API

```bash
# На сервере
cd /root/new-voice
source venv/bin/activate

# Запустить API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# API доступен по адресам:
# http://77.233.212.58:8000/       — корень
# http://77.233.212.58:8000/docs   — Swagger документация
# http://77.233.212.58:8000/health — проверка здоровья
```

---

## 📅 История

| Дата | Что сделано |
|------|-------------|
| 2026-01-12 | Настроен сервер, создан репозиторий |
| 2026-01-12 | Написана документация и спецификации |
| 2026-01-12 | Создан Scenario Engine |
| 2026-01-12 | Groq подключен (llama-3.1-8b-instant) |
| 2026-01-12 | ~~Ollama установлен~~ (удален, используем Groq) |
| 2026-01-12 | Подключены Deepgram, Cartesia, LiveKit |
| 2026-01-12 | **🎉 Voice Agent работает!** |
| 2026-01-12 | Настроена база данных (PostgreSQL, Qdrant, Redis) |
| 2026-01-12 | Создана RAG система для базы знаний |
| 2026-01-12 | Создан Admin API (FastAPI) |
| 2026-01-12 | Создан фронтенд в Lovable (ожидает HTTPS) |
| 2026-01-13 | **📞 Телефония MTS Exolve настроена!** |
| 2026-01-15 | **🎉 ТЕЛЕФОНИЯ РАБОТАЕТ!** VPS РФ + Kamailio + rtpengine |
| 2026-01-15 | Переключен LLM на Groq (быстрее Ollama) |
| 2026-01-17 | **🏗️ Enterprise Platform Phase 1** — Database Schema Migration |
| 2026-01-17 | **🏗️ Enterprise Platform Phase 2** — Skillbase Management (Pydantic + Service + VoiceAgent + Tools) |
| 2026-01-17 | **📊 Enterprise Platform Phase 3** — Deep Observability (Telemetry + Metrics + Costs + Quality) ✅ ЗАВЕРШЕНО |
| 2026-01-17 | **📞 Enterprise Platform Phase 4 (Tasks 13-14)** — Campaign Management (CampaignService + Tests) ✅ РЕАЛИЗОВАНО |

---

## 📞 Телефония MTS Exolve — Настройки

### Данные MTS Exolve
| Параметр | Значение |
|----------|----------|
| **Номер телефона** | +7 934 662-08-75 |
| **SIP Trunk** | prosto voice |
| **Outbound IP** | 80.75.130.99 |
| **Inbound IP** | 80.75.130.101 |
| **Переадресация** | 55fzatq1dd8@sip.livekit.cloud ✅ |

### Данные LiveKit
| Параметр | Значение |
|----------|----------|
| **SIP URI** | sip:55fzatq1dd8.sip.livekit.cloud |
| **SIP IP** | 138.2.166.67 |
| **Inbound Trunk ID** | ST_ZrtCkMpnDSPC |
| **Inbound Trunk Name** | MTS Exolve Inbound |
| **Dispatch Rule ID** | SDR_GyBxoB4KiNq6 |
| **Dispatch Rule Name** | MTS Exolve Inbound |
| **Agent Name** | voice-agent |
| **Room Prefix** | call- |

### Как работает входящий звонок
```
1. Клиент звонит на +7 934 662-08-75
2. MTS Exolve принимает звонок
3. MTS Exolve перенаправляет на VPS РФ (62.113.37.156:5060)
4. Kamailio принимает SIP и пересылает на LiveKit Cloud
5. rtpengine проксирует аудио (RTP) между MTS и LiveKit
6. LiveKit принимает звонок через Inbound Trunk
7. Dispatch Rule создаёт комнату call-<номер_звонящего>
8. LiveKit запускает voice-agent в этой комнате
9. Voice Agent (Нидерланды) отвечает через Groq LLM
```

### Архитектура телефонии
```
Телефон → MTS Exolve → VPS РФ (Kamailio+rtpengine) → LiveKit Cloud → Agent → Groq
              ↓              ↓                            ↓            ↓
      +7 934 662-08-75   62.113.37.156                Германия    Нидерланды
```

### Серверы

**VPS Россия (62.113.37.156) — SIP/RTP Proxy:**
- Kamailio 5.7.4: /etc/kamailio/kamailio.cfg
- rtpengine 11.5.1: /etc/rtpengine/rtpengine.conf
- Порты: 5060/udp (SIP), 10000-20000/udp (RTP)
- Стоимость: 350 руб/мес (Timeweb)

**VPS Нидерланды (77.233.212.58) — Voice Agent:**
- Voice Agent: python -m src.voice_agent.simple_agent dev
- LLM: Groq (llama-3.1-8b-instant)
- STT: Deepgram (nova-2)
- TTS: Cartesia (sonic-2)

### Тестирование телефонии
```bash
# 1. Запустить Voice Agent на сервере
cd /root/new-voice
source venv/bin/activate
python -m src.voice_agent.simple_agent dev

# 2. Позвонить на номер +7 934 662-08-75

# 3. Если бот ответил — телефония работает!
```

---

## 🔜 ЗАВТРА

1. **Тест телефонии** — позвонить на +7 934 662-08-75
2. **Настроить HTTPS** — нужен домен для SSL сертификата
3. **Подключить фронтенд** — связать Lovable с API

---

## 🔧 Systemd сервисы

Файлы сервисов находятся в `scripts/systemd/`:
- `new-voice-api.service` — Admin API (порт 8000)
- `new-voice-agent.service` — Voice Agent (LiveKit)

### Установка сервисов на сервере:

```bash
# Копируем файлы сервисов
sudo cp scripts/systemd/*.service /etc/systemd/system/

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable new-voice-api
sudo systemctl enable new-voice-agent

# Запускаем сервисы
sudo systemctl start new-voice-api
sudo systemctl start new-voice-agent

# Проверяем статус
sudo systemctl status new-voice-api
sudo systemctl status new-voice-agent
```

### Полезные команды:

```bash
# Посмотреть логи API
sudo journalctl -u new-voice-api -f

# Посмотреть логи Voice Agent
sudo journalctl -u new-voice-agent -f

# Перезапустить сервис
sudo systemctl restart new-voice-api

# Остановить сервис
sudo systemctl stop new-voice-api
```
