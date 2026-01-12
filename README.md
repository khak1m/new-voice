# NEW-VOICE 2.0

Voice AI Platform by AI Prosto

## О проекте

Платформа для создания голосовых AI-ботов, которые общаются с людьми естественно. Настройка под любую бизнес-нишу: салоны красоты, клиники, рестораны, недвижимость и др.

## Технологии

- **Python 3.11+** — основной язык
- **OpenAI GPT-4 / Claude** — LLM для диалогов
- **Deepgram** — распознавание речи (STT)
- **Cartesia** — синтез речи (TTS)
- **LiveKit** — real-time голосовой стриминг
- **MTS Exolve** — телефония
- **Qdrant** — векторная база для RAG
- **Supabase** — CRM и логи
- **FastAPI** — API и админ-панель
- **Docker** — контейнеризация

## Быстрый старт

### 1. Настройка сервера

```bash
chmod +x scripts/setup_server.sh
./scripts/setup_server.sh
```

### 2. Настройка проекта

```bash
cp .env.example .env
# Заполни API ключи в .env

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Запуск

```bash
docker-compose up -d
python src/main.py
```

## Структура проекта

```
new-voice/
├── src/                    # Исходный код
│   ├── agent/              # Голосовой агент
│   ├── api/                # FastAPI endpoints
│   ├── rag/                # RAG система
│   ├── telephony/          # Интеграция с телефонией
│   └── main.py
├── scripts/                # Скрипты установки
├── docs/                   # Документация
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Документация

- [Настройка сервера](docs/01_server_setup.md)
- [Регистрация сервисов](docs/02_services_setup.md)
- [Архитектура](docs/03_architecture.md)

## Лицензия

Proprietary — AI Prosto
