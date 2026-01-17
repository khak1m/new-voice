# 🧪 Phase 4 Testing Guide

## Дата: 2026-01-17
## Компонент: Campaign Management (Tasks 13-14)

---

## 📋 Что тестируем

**CampaignService** — система управления кампаниями исходящих звонков:
- ✅ Создание кампаний с валидацией
- ✅ Загрузка call lists (CSV/Excel)
- ✅ Управление жизненным циклом (start/pause)
- ✅ Rate limiting (concurrent + per minute)
- ✅ Task queue management
- ✅ Task status transitions
- ✅ Retry logic

---

## 🚀 Подготовка к тестированию

### 1. Установить зависимости

```bash
cd /root/new-voice
source venv/bin/activate
pip install pandas==2.2.0 openpyxl==3.1.2
```

### 2. Проверить подключение к БД

```bash
# Убедиться, что .env содержит DATABASE_URL
cat .env | grep DATABASE_URL

# Должно быть что-то вроде:
# DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### 3. Проверить миграции

```bash
# Убедиться, что все миграции применены
python -m alembic current

# Должно показать: 002 (head)
```

---

## 🧪 Запуск тестов

### Запустить все тесты

```bash
cd /root/new-voice
source venv/bin/activate
python scripts/test_campaign_service.py
```

### Ожидаемый результат

```
======================================================================
🚀 ТЕСТИРОВАНИЕ CAMPAIGN SERVICE (PHASE 4)
======================================================================

======================================================================
🧪 ТЕСТ 1: Campaign Creation
======================================================================
✅ Test data created
✅ CampaignService created
✅ Campaign created: <uuid>
   Name: Test Campaign 1
   Status: draft
   Max concurrent: 5
   Calls per minute: 10
✅ Validation error caught: Company <uuid> not found
✅ Validation error caught: Skillbase <uuid> not found or doesn't belong to company
✅ Validation error caught: Invalid time format: ...
✅ All validation tests passed

======================================================================
🧪 ТЕСТ 2: Call List Upload
======================================================================
✅ Using campaign: <uuid>
✅ Call list uploaded
   Total rows: 5
   Created tasks: 4
   Errors: 1
   Error details:
      - Row 6: Empty phone number
✅ Tasks in database: 4
   First task:
      Phone: +79991234567
      Name: Иван Иванов
      Status: pending
      Data: {'company': 'ООО Рога и Копыта', 'notes': 'VIP клиент'}
✅ Campaign total_tasks updated: 4
✅ Validation error caught: Unsupported file format...
✅ Validation error caught: Missing required columns: phone_number

======================================================================
🧪 ТЕСТ 3: Campaign Lifecycle
======================================================================
✅ Using campaign: <uuid>
   Initial status: draft
✅ Campaign started: running
✅ Validation error caught: Campaign is already running
✅ Campaign paused: paused
✅ Campaign restarted: running
✅ Active campaigns: 1

======================================================================
🧪 ТЕСТ 4: Task Queue Management
======================================================================
✅ Using campaign: <uuid>
✅ Got next task: <uuid>
   Phone: +79991234567
   Status: pending
   Priority: 0
✅ Got 5 tasks (max concurrent: 5)
✅ Rate limiting working correctly

======================================================================
🧪 ТЕСТ 5: Task Status Transitions
======================================================================
✅ Using task: <uuid>
   Initial status: pending
   Attempt count: 0
✅ Task marked in progress
   Status: in_progress
   Attempt count: 1
✅ Task marked completed
   Status: completed
   Outcome: success
✅ Task marked for retry
   Status: retry
   Next attempt: 2026-01-17 15:30:00

======================================================================
📊 ИТОГОВЫЙ ОТЧЕТ
======================================================================
✅ PASSED - Campaign Creation
✅ PASSED - Call List Upload
✅ PASSED - Campaign Lifecycle
✅ PASSED - Task Queue Management
✅ PASSED - Task Status Transitions
======================================================================
Результат: 5/5 тестов пройдено (100%)
======================================================================
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
```

---

## 🐛 Возможные проблемы

### Проблема 1: ModuleNotFoundError: No module named 'pandas'

**Решение:**
```bash
pip install pandas==2.2.0 openpyxl==3.1.2
```

### Проблема 2: Database connection error

**Решение:**
```bash
# Проверить DATABASE_URL в .env
cat .env | grep DATABASE_URL

# Проверить подключение к PostgreSQL
python scripts/test_database.py
```

### Проблема 3: Table does not exist

**Решение:**
```bash
# Применить миграции
python -m alembic upgrade head

# Проверить текущую версию
python -m alembic current
```

### Проблема 4: Import error (cannot import CampaignService)

**Решение:**
```bash
# Убедиться, что файлы на месте
ls -la src/services/campaign_service.py
ls -la src/services/__init__.py

# Проверить, что __init__.py экспортирует CampaignService
cat src/services/__init__.py
```

---

## 📊 Что проверяют тесты

### Тест 1: Campaign Creation
- ✅ Создание кампании с валидными данными
- ✅ Валидация company_id (должен существовать)
- ✅ Валидация skillbase_id (должен существовать и принадлежать company)
- ✅ Валидация time format (HH:MM)
- ✅ Установка default значений

### Тест 2: Call List Upload
- ✅ Парсинг CSV файла
- ✅ Создание CallTask записей
- ✅ Обработка ошибок по строкам (не останавливает процесс)
- ✅ Обновление campaign.total_tasks
- ✅ Валидация формата файла (только CSV/Excel)
- ✅ Валидация обязательных колонок (phone_number)
- ✅ Сохранение дополнительных полей в contact_data

### Тест 3: Campaign Lifecycle
- ✅ start() — запуск кампании (draft → running)
- ✅ Валидация: нельзя запустить running кампанию
- ✅ pause() — пауза кампании (running → paused)
- ✅ Повторный запуск после паузы (paused → running)
- ✅ get_active_campaigns() — получение активных кампаний

### Тест 4: Task Queue Management
- ✅ get_next_task() — получение следующей задачи
- ✅ Rate limiting: concurrent calls (max_concurrent_calls)
- ✅ Rate limiting: calls per minute (calls_per_minute)
- ✅ Scheduling window check (daily_start_time, daily_end_time)

### Тест 5: Task Status Transitions
- ✅ mark_in_progress() — pending → in_progress
- ✅ Увеличение attempt_count
- ✅ Установка last_attempt_at
- ✅ mark_completed() — in_progress → completed
- ✅ Сохранение call_id и outcome
- ✅ Обновление campaign.completed_tasks
- ✅ mark_failed() → retry (если attempt_count < max_retries)
- ✅ Установка next_attempt_at
- ✅ mark_failed() → failed (если max_retries достигнут)

---

## ✅ Критерии успешного тестирования

- [ ] Все 5 тестов пройдены (100%)
- [ ] Нет ошибок подключения к БД
- [ ] Нет import errors
- [ ] Campaign создаётся корректно
- [ ] Call list загружается из CSV
- [ ] Rate limiting работает
- [ ] Task transitions корректны
- [ ] Retry logic работает

---

## 📝 После тестирования

### Если все тесты пройдены ✅

1. Обновить PHASE4_COMPLETION.md:
   - Отметить "Тесты пройдены на сервере"
   - Добавить результаты тестирования

2. Закоммитить изменения:
   ```bash
   git add .
   git commit -m "Phase 4 (Tasks 13-14): Campaign Management - Tests passed"
   git push origin main
   ```

3. Переходить к Task 15: Campaign Worker

### Если есть проблемы ❌

1. Записать ошибки в отдельный файл
2. Исправить проблемы
3. Повторить тестирование

---

## 🔗 Связанные файлы

- **Реализация:** `src/services/campaign_service.py`
- **Тесты:** `scripts/test_campaign_service.py`
- **Документация:** `PHASE4_COMPLETION.md`
- **Спецификация:** `.kiro/specs/enterprise-platform/tasks.md`

---

**Дата создания:** 2026-01-17
**Статус:** READY FOR TESTING
