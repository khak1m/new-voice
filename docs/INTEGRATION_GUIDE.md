# 🔗 Integration Guide: Campaign Worker + Existing LiveKit Setup

## Дата: 2026-01-17
## Автор: Senior Backend Engineer

---

## 📋 Обзор

У нас есть **два типа звонков**, которые используют LiveKit:

### 1. **Входящие звонки (Inbound)** - УЖЕ РАБОТАЕТ ✅
- Пользователь звонит на наш номер
- LiveKit принимает звонок через SIP
- Запускается `VoiceAgent` через `entrypoint(ctx: JobContext)`
- Agent обрабатывает разговор
- Результат сохраняется в БД

### 2. **Исходящие звонки (Outbound)** - НОВАЯ ФУНКЦИОНАЛЬНОСТЬ ✅
- `CampaignWorker` берёт задачу из очереди
- Создаёт LiveKit room
- Набирает номер через SIP
- Запускает `VoiceAgent` для разговора
- Результат сохраняется в БД

---

## 🏗️ Архитектура интеграции

```
┌─────────────────────────────────────────────────────────────┐
│                    LiveKit Cloud                            │
│  wss://aiprosto-777-jxrcg2iv.livekit.cloud                 │
└─────────────────────────────────────────────────────────────┘
                    ▲                    ▲
                    │                    │
        ┌───────────┴──────────┐    ┌───┴──────────────┐
        │   Inbound Calls      │    │  Outbound Calls  │
        │   (Existing)         │    │  (New)           │
        └──────────────────────┘    └──────────────────┘
                    │                    │
                    │                    │
        ┌───────────▼──────────┐    ┌───▼──────────────┐
        │  LiveKit Agent       │    │ CampaignWorker   │
        │  (livekit-agents)    │    │ (Background)     │
        │                      │    │                  │
        │  - Слушает входящие  │    │ - Создаёт rooms  │
        │  - Запускает         │    │ - Набирает номер │
        │    entrypoint()      │    │ - Запускает      │
        │                      │    │   VoiceAgent     │
        └──────────────────────┘    └──────────────────┘
                    │                    │
                    └────────┬───────────┘
                             │
                    ┌────────▼─────────┐
                    │   VoiceAgent     │
                    │   (Shared)       │
                    │                  │
                    │ - STT (Deepgram) │
                    │ - LLM (Groq)     │
                    │ - TTS (Cartesia) │
                    │ - Scenario Logic │
                    └──────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   PostgreSQL     │
                    │   (Database)     │
                    │                  │
                    │ - Calls          │
                    │ - CallMetrics    │
                    │ - CallTasks      │
                    └──────────────────┘
```

---

## 🔧 Как это работает сейчас

### Входящие звонки (Inbound) - Существующий код

**1. Запуск LiveKit Agent:**
```bash
cd /root/new-voice
source venv/bin/activate
python -m livekit.agents dev src/voice_agent/skillbase_voice_agent.py
```

**2. Что происходит:**
- LiveKit Agent слушает входящие звонки
- Когда звонок приходит, вызывается `entrypoint(ctx: JobContext)`
- VoiceAgent обрабатывает разговор
- Результат сохраняется в `calls` таблицу

**3. Используемые credentials:**
```python
LIVEKIT_URL=wss://aiprosto-777-jxrcg2iv.livekit.cloud
LIVEKIT_API_KEY=API6o8JTjBWNFHX
LIVEKIT_API_SECRET=ItY8xWt7x8fPtIJ8lqfQ7PL8D8YdqUEwsXXyNzCjFov
```

---

## 🆕 Как работают исходящие звонки (Outbound)

### CampaignWorker - Новый код

**1. Запуск CampaignWorker:**
```bash
cd /root/new-voice
source venv/bin/activate
python -m src.workers.campaign_worker
```

**2. Что происходит:**
- CampaignWorker берёт задачу из `call_tasks` таблицы
- Создаёт LiveKit room через API
- Набирает номер через SIP trunk
- Запускает VoiceAgent **программно** (не через entrypoint)
- Результат сохраняется в `calls` и `call_tasks` таблицы

**3. Используемые credentials:**
```python
# ТЕ ЖЕ самые credentials из .env!
LIVEKIT_URL=wss://aiprosto-777-jxrcg2iv.livekit.cloud
LIVEKIT_API_KEY=API6o8JTjBWNFHX
LIVEKIT_API_SECRET=ItY8xWt7x8fPtIJ8lqfQ7PL8D8YdqUEwsXXyNzCjFov
```

---

## 🔑 Ключевые отличия

| Аспект | Inbound (Existing) | Outbound (New) |
|--------|-------------------|----------------|
| **Инициатор** | Пользователь звонит | CampaignWorker звонит |
| **Запуск** | `livekit-agents dev` | `python -m src.workers.campaign_worker` |
| **Entry point** | `entrypoint(ctx)` | Программный запуск VoiceAgent |
| **Room creation** | LiveKit создаёт автоматически | CampaignWorker создаёт через API |
| **SIP direction** | Inbound (принимаем) | Outbound (набираем) |
| **Database** | `calls` | `calls` + `call_tasks` + `campaigns` |
| **Credentials** | Из .env | Из .env (те же самые!) |

---

## 🚀 Как запустить оба одновременно

### Вариант 1: Два терминала (для разработки)

**Терминал 1 - Inbound Agent:**
```bash
cd /root/new-voice
source venv/bin/activate
python -m livekit.agents dev src/voice_agent/skillbase_voice_agent.py
```

**Терминал 2 - Outbound Worker:**
```bash
cd /root/new-voice
source venv/bin/activate
python -m src.workers.campaign_worker
```

### Вариант 2: Systemd Services (для продакшена)

**Создать два сервиса:**

**1. `/etc/systemd/system/newvoice-inbound.service`**
```ini
[Unit]
Description=NEW-VOICE Inbound Agent
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/new-voice
Environment="PATH=/root/new-voice/venv/bin"
ExecStart=/root/new-voice/venv/bin/python -m livekit.agents dev src/voice_agent/skillbase_voice_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**2. `/etc/systemd/system/newvoice-outbound.service`**
```ini
[Unit]
Description=NEW-VOICE Outbound Worker
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/new-voice
Environment="PATH=/root/new-voice/venv/bin"
ExecStart=/root/new-voice/venv/bin/python -m src.workers.campaign_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Запуск:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable newvoice-inbound
sudo systemctl enable newvoice-outbound
sudo systemctl start newvoice-inbound
sudo systemctl start newvoice-outbound
```

**Проверка:**
```bash
sudo systemctl status newvoice-inbound
sudo systemctl status newvoice-outbound
```

### Вариант 3: Docker Compose (рекомендуется)

**Добавить в `docker-compose.yml`:**
```yaml
services:
  # ... existing services ...

  inbound-agent:
    build: .
    command: python -m livekit.agents dev src/voice_agent/skillbase_voice_agent.py
    env_file: .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  outbound-worker:
    build: .
    command: python -m src.workers.campaign_worker
    env_file: .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
```

---

## 🔐 SIP Trunk Configuration

Для исходящих звонков нужен **SIP Trunk ID** от LiveKit.

### Как получить SIP Trunk ID:

1. Зайти в LiveKit Cloud Dashboard
2. Перейти в раздел "SIP"
3. Создать SIP Trunk (если ещё нет)
4. Скопировать Trunk ID

### Добавить в .env:
```bash
LIVEKIT_SIP_TRUNK_ID=your-trunk-id-here
```

### Обновить CampaignWorker:
```python
worker = CampaignWorker(
    db_session=session,
    livekit_url=os.getenv("LIVEKIT_URL"),
    livekit_api_key=os.getenv("LIVEKIT_API_KEY"),
    livekit_api_secret=os.getenv("LIVEKIT_API_SECRET"),
    sip_trunk_id=os.getenv("LIVEKIT_SIP_TRUNK_ID"),  # ← Добавить это
    voice_agent_factory=create_voice_agent,
    poll_interval=1.0
)
```

---

## 🧪 Тестирование интеграции

### 1. Проверить LiveKit подключение:
```bash
cd /root/new-voice
source venv/bin/activate
python scripts/test_services.py
```

**Ожидаемый результат:**
```
✅ LiveKit подключен!
   URL: wss://aiprosto-777-jxrcg2iv.livekit.cloud
   Активных комнат: 0
```

### 2. Запустить тест CampaignWorker:
```bash
python scripts/test_campaign_worker.py
```

**Ожидаемый результат:**
```
✅ CampaignWorker инициализирован
✅ Задачи обработаны
✅ Retry logic работает
```

### 3. Проверить входящие звонки:
```bash
python -m livekit.agents dev src/voice_agent/skillbase_voice_agent.py
```

Позвонить на номер и проверить, что бот отвечает.

---

## 📊 Мониторинг

### Проверить активные rooms:
```python
from livekit import api
import os

lk_api = api.LiveKitAPI(
    url=os.getenv("LIVEKIT_URL").replace("wss://", "https://"),
    api_key=os.getenv("LIVEKIT_API_KEY"),
    api_secret=os.getenv("LIVEKIT_API_SECRET")
)

rooms = await lk_api.room.list_rooms(api.ListRoomsRequest())
print(f"Active rooms: {len(rooms.rooms)}")
for room in rooms.rooms:
    print(f"  - {room.name} ({room.num_participants} participants)")
```

### Проверить задачи в очереди:
```sql
SELECT 
    status, 
    COUNT(*) as count 
FROM call_tasks 
GROUP BY status;
```

### Проверить метрики звонков:
```sql
SELECT 
    direction,
    status,
    COUNT(*) as count,
    AVG(duration_sec) as avg_duration
FROM calls
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY direction, status;
```

---

## ⚠️ Важные замечания

### 1. Shared LiveKit Connection
- Inbound и Outbound используют **одно и то же** LiveKit подключение
- Credentials из `.env` используются обоими
- Нет конфликтов, потому что rooms разные

### 2. VoiceAgent Factory
- Для Outbound нужна **factory function**, которая создаёт VoiceAgent
- Для Inbound используется `entrypoint(ctx)` (LiveKit вызывает автоматически)

### 3. Database Sessions
- Каждый worker должен иметь **свою** async session
- Не шарить session между workers!

### 4. Rate Limiting
- CampaignWorker имеет встроенный rate limiting
- Inbound calls не имеют rate limiting (принимаем все)

### 5. Error Handling
- Оба worker должны gracefully обрабатывать ошибки
- Retry logic только для Outbound (Inbound не retry)

---

## 🎯 Следующие шаги

### 1. Получить SIP Trunk ID
- Зайти в LiveKit Dashboard
- Создать SIP Trunk
- Добавить в `.env`

### 2. Создать VoiceAgent Factory
- Функция, которая создаёт VoiceAgent для Outbound
- Использует Skillbase из БД

### 3. Запустить оба worker
- Inbound Agent для входящих
- CampaignWorker для исходящих

### 4. Мониторинг
- Логи обоих workers
- Метрики в БД
- LiveKit Dashboard

---

## 📝 Резюме

**Ключевая идея:** Inbound и Outbound используют **одну и ту же** LiveKit инфраструктуру, но **разные** entry points:

- **Inbound:** LiveKit вызывает `entrypoint(ctx)` автоматически
- **Outbound:** CampaignWorker создаёт room и запускает VoiceAgent программно

**Credentials:** Одни и те же из `.env` для обоих!

**Конфликтов нет:** Разные rooms, разные sessions, разные workers.

---

**Дата:** 2026-01-17
**Статус:** ✅ Ready for Integration
**Автор:** Senior Backend Engineer
