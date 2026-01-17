# Phase 2: Skillbase Management - Инструкция по тестированию

## ✅ Что сделано

### Задача 6.1: VoiceAgent Refactoring ✅

**Создано:**
1. `src/prompts/skillbase_prompt_builder.py` - SystemPromptBuilder
2. `src/voice_agent/skillbase_voice_agent.py` - новый агент с загрузкой из БД
3. `scripts/test_skillbase_agent.py` - тестовый скрипт

**Изменено:**
- `src/schemas/skillbase_schemas.py` - FlowConfig теперь поддерживает `Union[str, StateConfig]`

---

## 🧪 Тестирование на сервере

### Шаг 1: Обновить код

```bash
cd /root/new-voice
git pull origin main
```

### Шаг 2: Запустить тесты

```bash
source venv/bin/activate
python scripts/test_skillbase_agent.py
```

**Ожидаемый результат:**

```
✅ PASSED - SystemPromptBuilder
✅ PASSED - Создание Skillbase
✅ PASSED - Загрузка Skillbase

Результат: 3/3 тестов пройдено (100%)
```

### Шаг 3: Создать тестовый Skillbase

Тест 2 создаст Skillbase в БД и выведет команду для запуска агента:

```
📋 ДЛЯ ЗАПУСКА АГЕНТА С ЭТИМ SKILLBASE:
======================================================================
SKILLBASE_ID=<uuid> python -m src.voice_agent.skillbase_voice_agent dev
======================================================================
```

**Примечание:** Тест 2 откатывает транзакцию, поэтому Skillbase не сохраняется. Для реального тестирования нужно создать Skillbase через API или вручную в БД.

---

## 📝 Создание Skillbase вручную (для тестирования)

### Вариант 1: Через Python скрипт

Создайте файл `scripts/create_test_skillbase.py`:

```python
import asyncio
from uuid import uuid4
from database.connection import get_async_db
from database.models import Company
from services.skillbase_service import SkillbaseService

async def main():
    async with get_async_db() as db:
        # Найти существующую компанию или создать новую
        from sqlalchemy import select
        result = await db.execute(select(Company).limit(1))
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                id=uuid4(),
                name="Тестовая компания",
                slug=f"test-{uuid4().hex[:8]}",
                email="test@example.com"
            )
            db.add(company)
            await db.flush()
        
        # Создать Skillbase
        service = SkillbaseService(db)
        skillbase = await service.create(
            company_id=company.id,
            name="Салон - Запись клиентов",
            slug=f"salon-booking-{uuid4().hex[:8]}",
            description="Тестовый Skillbase для записи в салон",
            config={
                "context": {
                    "role": "Администратор салона красоты",
                    "style": "Дружелюбный и профессиональный",
                    "safety_rules": ["Не обсуждай политику"],
                    "facts": ["Работаем с 9:00 до 21:00"]
                },
                "flow": {
                    "type": "linear",
                    "states": ["Приветствие", "Узнать имя", "Узнать услугу", "Записать"],
                    "transitions": []
                },
                "agent": {"handoff_criteria": {}, "crm_field_mapping": {}},
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
            }
        )
        
        await db.commit()
        
        print(f"✅ Skillbase создан!")
        print(f"   ID: {skillbase.id}")
        print(f"   Name: {skillbase.name}")
        print(f"\n📋 Для запуска агента:")
        print(f"SKILLBASE_ID={skillbase.id} python -m src.voice_agent.skillbase_voice_agent dev")

if __name__ == "__main__":
    asyncio.run(main())
```

Запустить:

```bash
python scripts/create_test_skillbase.py
```

### Вариант 2: Через psql

```sql
-- Найти ID компании
SELECT id, name FROM companies LIMIT 1;

-- Создать Skillbase
INSERT INTO skillbases (id, company_id, name, slug, config, version)
VALUES (
    gen_random_uuid(),
    '<company_id>',  -- Замените на реальный ID
    'Салон - Запись клиентов',
    'salon-booking-test',
    '{
        "context": {
            "role": "Администратор салона",
            "style": "Дружелюбный",
            "safety_rules": [],
            "facts": ["Работаем 9-21"]
        },
        "flow": {
            "type": "linear",
            "states": ["Приветствие", "Узнать имя", "Записать"],
            "transitions": []
        },
        "agent": {"handoff_criteria": {}, "crm_field_mapping": {}},
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
)
RETURNING id;
```

---

## 🚀 Запуск агента с Skillbase

После создания Skillbase:

```bash
# Установить SKILLBASE_ID
export SKILLBASE_ID=<uuid>

# Запустить агента
python -m src.voice_agent.skillbase_voice_agent dev
```

**Ожидаемый вывод:**

```
[Skillbase] Загружен: Салон - Запись клиентов (v1)
[Skillbase] Компания: Тестовая компания
[Skillbase] LLM: groq/llama-3.1-8b-instant
[Skillbase] TTS: cartesia
[Skillbase] STT: deepgram
[Agent] System prompt построен (1160 символов)
[Agent] Подключен к комнате: ...
[Agent] Агент запущен, ожидаю голос...
```

---

## ✅ Критерии успеха Phase 2 (Task 6.1)

- [x] SystemPromptBuilder создан
- [x] Промпт генерируется из Skillbase.config
- [x] skillbase_voice_agent.py создан
- [x] Агент загружает Skillbase из БД
- [x] Агент использует LLM/TTS/STT из конфигурации
- [ ] Агент протестирован с реальным звонком (TODO: Task 6.2)

---

## 🎯 Следующие шаги

**Task 6.2:** Интеграция ScenarioEngine с Skillbase
- Передать `Skillbase.config.flow` в ScenarioEngine
- Обработать ответы engine

**Task 6.3:** Function calling support
- Парсить `Skillbase.config.tools`
- Выполнять tool calls во время разговора

---

## 🆘 Troubleshooting

### Проблема: "SKILLBASE_ID не указан"

```bash
# Убедитесь, что переменная установлена
echo $SKILLBASE_ID

# Если пусто, установите:
export SKILLBASE_ID=<uuid>
```

### Проблема: "Skillbase не найден"

```bash
# Проверьте, что Skillbase существует в БД
psql -U postgres -d new_voice -c "SELECT id, name FROM skillbases;"
```

### Проблема: "Неверный формат config"

```bash
# Проверьте структуру config
psql -U postgres -d new_voice -c "SELECT config FROM skillbases WHERE id = '<uuid>';"
```

---

## 📊 Статус Phase 2

| Задача | Статус |
|--------|--------|
| 4.1 Pydantic модели | ✅ DONE |
| 4.2 Валидация config | ✅ DONE |
| 5.1 SkillbaseService | ✅ DONE |
| 5.2 RAG attachment | ✅ DONE |
| **6.1 VoiceAgent refactoring** | ✅ **DONE** |
| 6.2 ScenarioEngine integration | ❌ TODO |
| 6.3 Function calling | ❌ TODO |

**Progress:** 5/7 задач (71%)
