# 🚀 API Quick Start Guide

## Запуск API сервера

### 1. Активировать виртуальное окружение

```bash
cd /root/new-voice
source venv/bin/activate
```

### 2. Запустить API сервер

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Опции:**
- `--host 0.0.0.0` — доступ с любого IP
- `--port 8000` — порт (можно изменить)
- `--reload` — автоперезагрузка при изменении кода (для разработки)

### 3. Открыть Swagger UI

**URL:** http://77.233.212.58:8000/docs

Swagger UI предоставляет:
- Интерактивную документацию API
- Возможность тестировать endpoints прямо в браузере
- Автоматическую генерацию примеров запросов

**Альтернатива (ReDoc):** http://77.233.212.58:8000/redoc

---

## 📚 Доступные API Endpoints

### Skillbases (5 endpoints)

**GET /api/skillbases**
- Список Skillbases с фильтрацией
- Параметры: company_id, is_active, is_published, skip, limit

**POST /api/skillbases**
- Создать новый Skillbase
- Body: name, slug, company_id, config, ...

**GET /api/skillbases/{id}**
- Получить Skillbase по ID

**PUT /api/skillbases/{id}**
- Обновить Skillbase (автоматический version increment)

**DELETE /api/skillbases/{id}**
- Удалить Skillbase (CASCADE)

---

### Campaigns (8 endpoints)

**GET /api/campaigns**
- Список Campaigns с фильтрацией
- Параметры: company_id, skillbase_id, status, skip, limit

**POST /api/campaigns**
- Создать новую Campaign
- Body: company_id, skillbase_id, name, scheduling, rate_limits, ...

**GET /api/campaigns/{id}**
- Получить Campaign по ID

**PUT /api/campaigns/{id}**
- Обновить Campaign

**DELETE /api/campaigns/{id}**
- Удалить Campaign (CASCADE)

**POST /api/campaigns/{id}/call-list**
- Загрузить список контактов (CSV/Excel)
- File upload: phone_number (обязательно), name, ...

**POST /api/campaigns/{id}/start**
- Запустить Campaign

**POST /api/campaigns/{id}/pause**
- Поставить Campaign на паузу

---

### Analytics (4 endpoints)

**GET /api/analytics/calls**
- История звонков с фильтрацией
- Параметры: skillbase_id, campaign_id, outcome, status, start_date, end_date, page, page_size

**GET /api/analytics/calls/{id}/metrics**
- Детальные метрики звонка
- Возвращает: latency, usage, cost, quality, outcome

**GET /api/analytics/metrics**
- Агрегированные метрики
- Параметры: skillbase_id, campaign_id, start_date, end_date
- Возвращает: total_calls, avg_metrics, total_cost, outcome_distribution

**WS /api/analytics/ws/calls/{id}**
- WebSocket для real-time мониторинга звонка
- Типы сообщений: init, turn, metrics, status

---

## 🧪 Примеры использования

### 1. Создать Skillbase

```bash
curl -X POST "http://77.233.212.58:8000/api/skillbases" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Салон красоты",
    "slug": "salon-bot",
    "company_id": "YOUR_COMPANY_ID",
    "config": {
      "context": {
        "role": "Администратор салона красоты",
        "style": "Дружелюбный и профессиональный",
        "safety_rules": ["Не обсуждать цены без прайс-листа"],
        "facts": ["Работаем с 9:00 до 21:00"]
      },
      "flow": {
        "type": "linear",
        "states": [
          {
            "id": "greeting",
            "prompt": "Поздоровайтесь и спросите чем помочь",
            "next": "booking"
          },
          {
            "id": "booking",
            "prompt": "Предложите записаться на услугу",
            "next": "end"
          }
        ]
      },
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
  }'
```

### 2. Создать Campaign

```bash
curl -X POST "http://77.233.212.58:8000/api/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "YOUR_COMPANY_ID",
    "skillbase_id": "YOUR_SKILLBASE_ID",
    "name": "Напоминание о записи",
    "description": "Обзвон клиентов с напоминанием",
    "daily_start_time": "09:00",
    "daily_end_time": "18:00",
    "max_concurrent_calls": 5,
    "calls_per_minute": 10,
    "max_retries": 3,
    "retry_delay_minutes": 30
  }'
```

### 3. Загрузить список контактов

```bash
curl -X POST "http://77.233.212.58:8000/api/campaigns/YOUR_CAMPAIGN_ID/call-list" \
  -F "file=@contacts.csv"
```

**Формат CSV:**
```csv
phone_number,name,appointment_time
+79991234567,Иван Иванов,2026-01-20 14:00
+79997654321,Мария Петрова,2026-01-20 15:30
```

### 4. Запустить Campaign

```bash
curl -X POST "http://77.233.212.58:8000/api/campaigns/YOUR_CAMPAIGN_ID/start"
```

### 5. Получить метрики

```bash
# Агрегированные метрики за последние 30 дней
curl "http://77.233.212.58:8000/api/analytics/metrics"

# Метрики конкретного звонка
curl "http://77.233.212.58:8000/api/analytics/calls/YOUR_CALL_ID/metrics"
```

---

## 🔧 Troubleshooting

### Ошибка: "Address already in use"

Порт 8000 уже занят. Используйте другой порт:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8001
```

### Ошибка: "Module not found"

Убедитесь что виртуальное окружение активировано:

```bash
source venv/bin/activate
```

### Ошибка: "Database connection failed"

Проверьте `.env` файл:

```bash
cat .env | grep DATABASE_URL
```

Должно быть:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/new_voice
```

---

## 📊 Мониторинг

### Логи API

```bash
# Логи в реальном времени
tail -f /var/log/new-voice/api.log

# Или если запущено в терминале - логи выводятся в stdout
```

### Проверка здоровья

```bash
curl http://77.233.212.58:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

---

## 🚀 Production Deployment

### 1. Использовать Gunicorn

```bash
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/new-voice/access.log \
  --error-logfile /var/log/new-voice/error.log
```

### 2. Создать systemd service

```bash
sudo nano /etc/systemd/system/new-voice-api.service
```

```ini
[Unit]
Description=NEW-VOICE 2.0 API
After=network.target postgresql.service

[Service]
Type=notify
User=root
WorkingDirectory=/root/new-voice
Environment="PATH=/root/new-voice/venv/bin"
ExecStart=/root/new-voice/venv/bin/gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable new-voice-api
sudo systemctl start new-voice-api
sudo systemctl status new-voice-api
```

### 3. Настроить Nginx reverse proxy

```bash
sudo nano /etc/nginx/sites-available/new-voice-api
```

```nginx
server {
    listen 80;
    server_name api.new-voice.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/new-voice-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📝 Дополнительная документация

- **Phase 5 Completion:** `PHASE5_COMPLETION.md`
- **Enterprise Platform Summary:** `ENTERPRISE_PLATFORM_SUMMARY.md`
- **API Specification:** `.kiro/specs/enterprise-platform/requirements.md`
- **Design Document:** `.kiro/specs/enterprise-platform/design.md`

---

**Дата:** 2026-01-17
**Версия API:** 2.0.0
**Статус:** ✅ Production Ready
