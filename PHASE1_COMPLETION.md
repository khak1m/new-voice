# Phase 1: Foundation & Data Model - Инструкция по закрытию

## ✅ Что уже сделано (локально)

- ✅ Миграция 001: skillbases, campaigns, call_tasks
- ✅ Миграция 002: call_metrics, call_logs
- ✅ SQLAlchemy модели: Skillbase, Campaign, CallTask, CallMetrics, CallLog
- ✅ Тесты написаны и проверены локально
- ✅ Ollama удален (используем Groq)

## ❌ Что нужно сделать на сервере

### Шаг 1: Подключиться к серверу

```bash
ssh root@77.233.212.58
```

### Шаг 2: Обновить код

```bash
cd /root/new-voice
git pull origin main
```

Должны появиться:
- ✅ Миграции в `alembic/versions/`
- ✅ Новые модели в `src/database/models.py`
- ✅ Pydantic схемы в `src/schemas/`
- ✅ SkillbaseService в `src/services/`
- ❌ Удален `src/providers/ollama_llm.py`

### Шаг 3: Активировать виртуальное окружение

```bash
source venv/bin/activate
```

### Шаг 4: Применить миграции

```bash
python -m alembic upgrade head
```

**Ожидаемый вывод:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Add skillbases, campaigns, call_tasks tables
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Add call_metrics and call_logs tables
```

### Шаг 5: Проверить создание таблиц

```bash
psql -U postgres -d new_voice -c "\dt"
```

**Должны быть таблицы:**
```
 public | bots            | table | postgres
 public | call_logs       | table | postgres  ← НОВАЯ
 public | call_metrics    | table | postgres  ← НОВАЯ
 public | call_tasks      | table | postgres  ← НОВАЯ
 public | calls           | table | postgres
 public | campaigns       | table | postgres  ← НОВАЯ
 public | companies       | table | postgres
 public | knowledge_bases | table | postgres
 public | leads           | table | postgres
 public | skillbases      | table | postgres  ← НОВАЯ
```

### Шаг 6: Проверить структуру skillbases

```bash
psql -U postgres -d new_voice -c "\d skillbases"
```

**Должны быть колонки:**
- id (uuid)
- company_id (uuid)
- name (varchar)
- slug (varchar)
- description (text)
- config (jsonb) ← ВАЖНО
- version (integer)
- knowledge_base_id (uuid)
- is_active (boolean)
- is_published (boolean)
- created_at (timestamp)
- updated_at (timestamp)

### Шаг 7: Запустить тесты

```bash
# Тест 1: Локальные тесты (без БД)
python scripts/test_enterprise_platform.py
```

**Ожидаемый результат:**
```
✅ Test 1: Import all models - PASSED
✅ Test 2: Validate Skillbase JSONB config - PASSED
✅ Test 3: Create model instances - PASSED
✅ Test 4: Check relationships - PASSED
✅ Test 5: Test version increment - PASSED
✅ Test 6: Test CallMetrics calculations - PASSED

Result: 6/6 tests passed (100%)
```

```bash
# Тест 2: Тесты с БД
python scripts/test_enterprise_db.py
```

**Ожидаемый результат:**
```
✅ Test 1: Database connection - PASSED
✅ Test 2: Table existence - PASSED
✅ Test 3: CRUD operations - PASSED

Result: 3/3 tests passed (100%)
```

```bash
# Тест 3: Skillbase Service
python scripts/test_skillbase_service.py
```

**Ожидаемый результат:**
```
✅ Test 1: Schema Validation - PASSED
✅ Test 2: Service Operations - PASSED

Result: 2/2 tests passed (100%)
```

### Шаг 8: Удалить Ollama с сервера (опционально)

Если Ollama установлена на сервере и больше не нужна:

```bash
# Остановить Ollama
sudo systemctl stop ollama

# Отключить автозапуск
sudo systemctl disable ollama

# Удалить Ollama (если установлена)
sudo rm -rf /usr/local/bin/ollama
sudo rm -rf ~/.ollama

# Проверить, что Ollama удалена
which ollama  # Должно вернуть пустоту
```

---

## ✅ Критерии успеха Phase 1

После выполнения всех шагов:

- [x] Код обновлен на сервере
- [ ] Миграции применены (`alembic upgrade head`)
- [ ] 5 новых таблиц созданы в PostgreSQL
- [ ] Все тесты проходят (11/11 = 100%)
- [ ] Ollama удалена (опционально)

---

## 🎯 После закрытия Phase 1

Переходим к **Phase 2: Skillbase Management** (интеграция с VoiceAgent):

1. Создать SystemPromptBuilder
2. Рефакторинг VoiceAgent для загрузки Skillbase из БД
3. Интеграция ScenarioEngine с Skillbase.config.flow
4. Тестирование end-to-end

---

## 🆘 Troubleshooting

### Проблема: Миграции не применяются

```bash
# Проверить текущую версию БД
python -m alembic current

# Проверить историю миграций
python -m alembic history

# Откатить миграции (если нужно)
python -m alembic downgrade -1
```

### Проблема: Таблицы не создаются

```bash
# Проверить подключение к БД
psql -U postgres -d new_voice -c "SELECT version();"

# Проверить права пользователя
psql -U postgres -d new_voice -c "\du"
```

### Проблема: Тесты падают

```bash
# Проверить .env файл
cat .env | grep DATABASE_URL

# Проверить, что БД доступна
psql -U postgres -d new_voice -c "SELECT 1;"
```

---

## 📝 Отчет после выполнения

После выполнения всех шагов, напишите мне:

```
Phase 1 завершен:
- Миграции применены: ✅/❌
- Таблицы созданы: ✅/❌
- Тесты пройдены: X/11
- Ollama удалена: ✅/❌
```

И мы перейдем к Phase 2!
