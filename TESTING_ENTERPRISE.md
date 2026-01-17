# 🧪 Тестирование Enterprise Platform Phase 1

Комплексное руководство по тестированию новых компонентов Enterprise Platform.

---

## 📋 Что тестируем

### Phase 1: Database Schema Migration
- ✅ Миграции Alembic (001, 002)
- ✅ SQLAlchemy модели (Skillbase, Campaign, CallTask, CallMetrics, CallLog)
- ✅ JSONB конфигурации
- ✅ Связи между таблицами
- ✅ CRUD операции

---

## 🚀 Быстрый старт

### 1. Тест без базы данных (локально)

Проверяет импорт моделей, валидацию конфигураций, создание объектов в памяти:

```bash
cd /path/to/new-voice
python scripts/test_enterprise_platform.py
```

**Что проверяется:**
- ✅ Импорт всех моделей
- ✅ Валидация Skillbase JSONB конфигурации
- ✅ Создание экземпляров моделей
- ✅ Связи между моделями (relationships)
- ✅ Инкремент версии Skillbase
- ✅ Расчеты метрик CallMetrics

**Ожидаемый результат:**
```
🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!
✅ Enterprise Platform Phase 1 готова к использованию
Результат: 6/6 тестов пройдено (100.0%)
```

---

### 2. Тест с реальной базой данных (на сервере)

**ВНИМАНИЕ:** Требует подключения к PostgreSQL!

```bash
# На сервере
cd /root/new-voice
source venv/bin/activate

# Убедитесь, что миграции применены
python -m alembic upgrade head

# Запустите тесты
python scripts/test_enterprise_db.py
```

**Что проверяется:**
- ✅ Подключение к PostgreSQL
- ✅ Существование всех новых таблиц
- ✅ CRUD операции (Create, Read, Update, Delete)
- ✅ Транзакции и откаты
- ✅ Связи между таблицами в реальной БД

**Ожидаемый результат:**
```
🎉 ВСЕ ТЕСТЫ С БД ПРОЙДЕНЫ!
✅ Enterprise Platform Phase 1 полностью функциональна
Результат: 3/3 тестов пройдено (100.0%)
```

---

## 🗄️ Применение миграций на сервере

### Шаг 1: Подключитесь к серверу

```bash
ssh root@77.233.212.58
cd /root/new-voice
source venv/bin/activate
```

### Шаг 2: Проверьте текущую версию БД

```bash
python -m alembic current
```

Если миграции еще не применены, вы увидите пустой вывод или старую версию.

### Шаг 3: Примените миграции

```bash
# Применить все миграции
python -m alembic upgrade head

# Или применить конкретную миграцию
python -m alembic upgrade 001  # Только skillbases, campaigns, call_tasks
python -m alembic upgrade 002  # Добавить call_metrics, call_logs
```

### Шаг 4: Проверьте результат

```bash
# Проверить версию
python -m alembic current

# Должно показать: 002 (head)
```

### Шаг 5: Проверьте таблицы в PostgreSQL

```bash
# Подключитесь к PostgreSQL
psql -U newvoice -d newvoice

# Проверьте таблицы
\dt

# Должны появиться:
# - skillbases
# - campaigns
# - call_tasks
# - call_metrics
# - call_logs

# Посмотрите структуру таблицы
\d skillbases

# Выйдите
\q
```

---

## 🧪 Ручное тестирование в PostgreSQL

### Создание тестового Skillbase

```sql
-- Подключитесь к БД
psql -U newvoice -d newvoice

-- Создайте тестовую компанию (если еще нет)
INSERT INTO companies (id, name, slug, email)
VALUES (
  gen_random_uuid(),
  'Test Company',
  'test-company',
  'test@example.com'
) RETURNING id;

-- Сохраните ID компании и используйте его ниже

-- Создайте Skillbase
INSERT INTO skillbases (
  id,
  company_id,
  name,
  slug,
  config,
  version
) VALUES (
  gen_random_uuid(),
  '<company_id_from_above>',
  'Test Skillbase',
  'test-skillbase',
  '{
    "context": {
      "role": "Тестовый ассистент",
      "style": "Профессиональный",
      "safety_rules": ["Не давать медицинские советы"],
      "facts": ["Работаем с 9 до 21"]
    },
    "flow": {
      "type": "linear",
      "states": ["greeting", "inquiry", "booking"],
      "transitions": []
    },
    "agent": {
      "handoff_criteria": {},
      "crm_field_mapping": {}
    },
    "tools": [],
    "voice": {
      "tts_provider": "cartesia",
      "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
      "stt_provider": "deepgram",
      "stt_language": "ru"
    },
    "llm": {
      "provider": "groq",
      "model": "llama-3.1-8b-instant",
      "temperature": 0.7
    }
  }'::jsonb,
  1
) RETURNING id, name, version;

-- Проверьте созданный Skillbase
SELECT id, name, slug, version, 
       jsonb_pretty(config) as config
FROM skillbases
WHERE slug = 'test-skillbase';

-- Удалите тестовые данные
DELETE FROM skillbases WHERE slug = 'test-skillbase';
```

### Создание тестовой Campaign

```sql
-- Создайте Campaign (используйте ID skillbase из предыдущего шага)
INSERT INTO campaigns (
  id,
  company_id,
  skillbase_id,
  name,
  status,
  max_concurrent_calls,
  calls_per_minute
) VALUES (
  gen_random_uuid(),
  '<company_id>',
  '<skillbase_id>',
  'Test Campaign',
  'draft',
  5,
  10
) RETURNING id, name, status;

-- Проверьте Campaign
SELECT c.id, c.name, c.status, 
       s.name as skillbase_name
FROM campaigns c
JOIN skillbases s ON c.skillbase_id = s.id
WHERE c.name = 'Test Campaign';
```

---

## 📊 Проверка метрик

### Создание тестовых CallMetrics

```sql
-- Создайте тестовый звонок (если еще нет)
INSERT INTO calls (
  id,
  company_id,
  direction,
  caller_number,
  status
) VALUES (
  gen_random_uuid(),
  '<company_id>',
  'outbound',
  '+79991234567',
  'completed'
) RETURNING id;

-- Создайте метрики для звонка
INSERT INTO call_metrics (
  id,
  call_id,
  ttfb_stt_avg,
  latency_llm_avg,
  ttfb_tts_avg,
  eou_latency_avg,
  stt_duration_sec,
  llm_input_tokens,
  llm_output_tokens,
  tts_characters,
  cost_stt,
  cost_llm,
  cost_tts,
  cost_total,
  turn_count
) VALUES (
  gen_random_uuid(),
  '<call_id_from_above>',
  150.5,
  800.2,
  200.1,
  1200.5,
  45.3,
  150,
  200,
  350,
  0.012,
  0.008,
  0.015,
  0.035,
  10
) RETURNING id;

-- Проверьте метрики
SELECT 
  cm.ttfb_stt_avg,
  cm.latency_llm_avg,
  cm.cost_total,
  cm.turn_count,
  c.caller_number
FROM call_metrics cm
JOIN calls c ON cm.call_id = c.id
WHERE c.caller_number = '+79991234567';
```

---

## 🔄 Откат миграций (если нужно)

```bash
# Откатить последнюю миграцию
python -m alembic downgrade -1

# Откатить до конкретной версии
python -m alembic downgrade 001

# Откатить все миграции
python -m alembic downgrade base
```

**ВНИМАНИЕ:** Откат удалит все данные из новых таблиц!

---

## ✅ Чеклист тестирования

### Перед применением на production:

- [ ] Локальные тесты пройдены (`test_enterprise_platform.py`)
- [ ] Миграции применены на dev/staging сервере
- [ ] Тесты с БД пройдены (`test_enterprise_db.py`)
- [ ] Ручное тестирование в PostgreSQL выполнено
- [ ] Проверены все связи между таблицами
- [ ] Создан backup базы данных
- [ ] Протестирована производительность запросов
- [ ] Документация обновлена

### После применения на production:

- [ ] Миграции применены успешно
- [ ] Все таблицы созданы
- [ ] Индексы работают
- [ ] Связи между таблицами функционируют
- [ ] CRUD операции работают
- [ ] Мониторинг настроен

---

## 🐛 Troubleshooting

### Проблема: "No module named 'database'"

**Решение:**
```bash
# Убедитесь, что вы в правильной директории
cd /root/new-voice

# Активируйте venv
source venv/bin/activate

# Проверьте PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Проблема: "Connection refused" при подключении к БД

**Решение:**
```bash
# Проверьте, что PostgreSQL запущен
sudo systemctl status postgresql

# Проверьте настройки в .env
cat .env | grep DB_

# Проверьте подключение вручную
psql -U newvoice -d newvoice -h localhost
```

### Проблема: "Table already exists"

**Решение:**
```bash
# Проверьте текущую версию миграций
python -m alembic current

# Если таблицы уже есть, но alembic не знает об этом:
python -m alembic stamp head
```

### Проблема: Миграция не применяется

**Решение:**
```bash
# Проверьте логи
python -m alembic upgrade head --sql > migration.sql
cat migration.sql

# Примените вручную
psql -U newvoice -d newvoice < migration.sql
```

---

## 📚 Дополнительные ресурсы

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
- [Enterprise Platform Design](.kiro/specs/enterprise-platform/design.md)
- [Enterprise Platform Tasks](.kiro/specs/enterprise-platform/tasks.md)

---

## 🎯 Следующие шаги

После успешного тестирования Phase 1:

1. **Phase 2: Skillbase Management**
   - Pydantic схемы для валидации конфигураций
   - SkillbaseService для бизнес-логики
   - Интеграция с VoiceAgent

2. **Phase 3: Deep Observability**
   - TelemetryService для сбора метрик
   - MetricCollector для инструментации
   - CostCalculator для расчета стоимости

3. **Phase 4: Campaign Manager**
   - CampaignService для управления кампаниями
   - Background workers для обработки очереди
   - Retry logic и rate limiting

4. **Phase 5: API Layer**
   - REST API endpoints для всех сущностей
   - WebSocket для real-time мониторинга
   - File upload для call lists

---

**Удачи в тестировании! 🚀**
