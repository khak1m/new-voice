# Testing Phase 2: Skillbase Management

## ✅ Что сделано

**Phase 2: Skillbase Management** завершена:
- ✅ Pydantic схемы для валидации конфигурации Skillbase
- ✅ SkillbaseService с полным CRUD
- ✅ Тесты (локальная валидация схем прошла успешно)

## 🧪 Тестирование на сервере

### 1. Обновить код на сервере

```bash
ssh root@77.233.212.58
cd /root/new-voice
git pull origin main
source venv/bin/activate
```

### 2. Применить миграции (если еще не применены)

```bash
# Проверить текущую версию БД
python -m alembic current

# Применить все миграции
python -m alembic upgrade head

# Проверить, что таблицы созданы
psql -U postgres -d new_voice -c "\dt"
```

Должны быть таблицы:
- `skillbases`
- `campaigns`
- `call_tasks`
- `call_metrics`
- `call_logs`

### 3. Запустить тесты

```bash
# Тест 1: Валидация схем (работает без БД)
python scripts/test_skillbase_service.py

# Тест 2: Тест с реальной БД
python scripts/test_enterprise_db.py
```

**Ожидаемый результат:**
```
✅ PASSED - Schema Validation (100%)
✅ PASSED - Service Operations (100%)
```

### 4. Ручное тестирование через Python

```python
import asyncio
from uuid import uuid4
from database.connection import get_async_db
from database.models import Company
from services.skillbase_service import SkillbaseService

async def test_skillbase():
    async with get_async_db() as db:
        # Создать тестовую компанию
        company = Company(
            id=uuid4(),
            name="Test Company",
            slug="test-company",
            email="test@example.com"
        )
        db.add(company)
        await db.flush()
        
        # Создать Skillbase
        service = SkillbaseService(db)
        
        config = {
            "context": {
                "role": "Ассистент салона красоты",
                "style": "Дружелюбный и профессиональный",
                "safety_rules": ["Не давать медицинские советы"],
                "facts": ["Работаем с 9 до 21"]
            },
            "flow": {
                "type": "linear",
                "states": [
                    {"id": "greeting", "name": "Приветствие"},
                    {"id": "inquiry", "name": "Запрос услуги"}
                ],
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
        }
        
        skillbase = await service.create(
            company_id=company.id,
            name="Салон красоты",
            slug="salon-test",
            config=config
        )
        
        print(f"✅ Skillbase создан: {skillbase.id}")
        print(f"   Версия: {skillbase.version}")
        print(f"   Конфиг валиден: {skillbase.config is not None}")
        
        # Получить Skillbase для звонка
        loaded = await service.get_for_call(skillbase.id)
        print(f"✅ Skillbase загружен для звонка")
        print(f"   Role: {loaded.config['context']['role']}")
        print(f"   LLM: {loaded.config['llm']['provider']}/{loaded.config['llm']['model']}")
        
        # Обновить конфиг (должна увеличиться версия)
        updated_config = config.copy()
        updated_config["context"]["role"] = "Обновленный ассистент"
        
        updated = await service.update(
            skillbase_id=skillbase.id,
            config=updated_config
        )
        
        print(f"✅ Skillbase обновлен")
        print(f"   Новая версия: {updated.version} (было {skillbase.version})")
        
        # Откатить транзакцию (не сохранять тестовые данные)
        await db.rollback()
        print("✅ Тест завершен (данные не сохранены)")

# Запустить тест
asyncio.run(test_skillbase())
```

Сохранить в файл `test_manual.py` и запустить:
```bash
python test_manual.py
```

## 📋 Следующие шаги (Phase 2.1)

После успешного тестирования Phase 2, переходим к интеграции с VoiceAgent:

1. **Создать SystemPromptBuilder** (`src/prompts/prompt_builder.py`)
   - Генерация динамического system prompt из Skillbase.config
   - Включить: context.role, context.style, context.safety_rules, context.facts

2. **Рефакторинг VoiceAgent** (`src/voice_agent/scenario_voice_agent.py`)
   - Принимать `skillbase_id` вместо `scenario_path`
   - Загружать Skillbase через `SkillbaseService.get_for_call()`
   - Использовать SystemPromptBuilder для генерации промпта
   - Применять настройки LLM/Voice из Skillbase.config

3. **Интеграция ScenarioEngine**
   - Конвертировать Skillbase.config.flow в ScenarioConfig
   - Передать в существующий ScenarioEngine

4. **Тестирование**
   - Создать Skillbase через сервис
   - Запустить VoiceAgent с `skillbase_id`
   - Проверить, что бот использует конфигурацию из БД

## 🎯 Критерии успеха Phase 2

- [x] Pydantic схемы валидируют конфигурацию
- [x] SkillbaseService создает/читает/обновляет/удаляет Skillbase
- [x] Версия автоматически инкрементируется при изменении config
- [ ] Тесты проходят на сервере с реальной БД
- [ ] VoiceAgent может загрузить Skillbase и использовать его конфигурацию

## 📝 Примечания

- Локальные тесты (schema validation) прошли успешно ✅
- Тесты с БД требуют подключения к PostgreSQL на сервере
- Все операции async с автоматическим rollback при ошибках
- Structured logging с контекстом (skillbase_id, company_id)
