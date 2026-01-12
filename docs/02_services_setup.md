# Этап 2: Регистрация сервисов

## Список сервисов

| Сервис | Назначение | Ссылка |
|--------|------------|--------|
| OpenAI | LLM для диалогов | https://platform.openai.com |
| Deepgram | Распознавание речи | https://deepgram.com |
| Cartesia | Синтез речи | https://cartesia.ai |
| LiveKit | Голосовой стриминг | https://livekit.io |
| MTS Exolve | Телефония | https://exolve.ru |
| Qdrant | Векторная база | https://qdrant.tech |
| Supabase | База данных | https://supabase.com |

---

## 1. OpenAI

1. Зайди на https://platform.openai.com
2. Создай аккаунт / войди
3. Перейди в API Keys → Create new secret key
4. Сохрани ключ: `sk-...`

**Модель:** `gpt-4-turbo` или `gpt-4o`

---

## 2. Deepgram

1. Зайди на https://deepgram.com
2. Создай аккаунт (есть бесплатный tier)
3. Dashboard → API Keys → Create Key
4. Сохрани ключ

**Модель:** `nova-2` (лучшее качество)

---

## 3. Cartesia

1. Зайди на https://cartesia.ai
2. Создай аккаунт
3. Settings → API Keys → Create
4. Сохрани ключ

**Голоса:** выбери подходящий в библиотеке голосов

---

## 4. LiveKit

### Вариант A: LiveKit Cloud (проще)

1. Зайди на https://cloud.livekit.io
2. Создай проект
3. Получи: URL, API Key, API Secret

### Вариант B: Self-hosted (на своём сервере)

```bash
docker run -d \
  --name livekit \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  livekit/livekit-server \
  --dev
```

---

## 5. MTS Exolve

1. Зайди на https://exolve.ru
2. Зарегистрируйся как юрлицо/ИП
3. Получи тестовый номер
4. API Key в личном кабинете

---

## 6. Qdrant (self-hosted)

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant
```

---

## 7. Supabase

1. Зайди на https://supabase.com
2. Создай проект
3. Settings → API → Скопируй URL и anon key

---

## Сохранение ключей

После получения всех ключей, заполни файл `.env`:

```bash
cp .env.example .env
nano .env
```

## Следующий шаг

→ [Архитектура проекта](03_architecture.md)
