# Как продолжить работу в новом чате

## Шаг 1: Напиши мне

```
Продолжаем работу над проектом NEW-VOICE 2.0.
Это платформа для создания голосовых AI-ботов.
Покажи файл PROGRESS.md чтобы понять где остановились.
```

## Шаг 2: Покажи файлы

Используй #File или просто открой эти файлы:
1. `new-voice/PROGRESS.md`
2. `.kiro/specs/scenario-engine/tasks.md`

## Шаг 3: Скажи что делать

Например:
- "Создай Groq LLM провайдер"
- "Покажи что уже сделано"
- "Объясни текущий статус"

---

## Краткое описание проекта

**NEW-VOICE 2.0** — платформа для создания голосовых AI-ботов:
- Боты общаются естественно, как люди
- Входящие и исходящие звонки
- Клиент сам настраивает этапы диалога через конфиг
- LLM генерирует ответы (не шаблоны)

**Технологии:**
- Python 3.12
- Ollama (Llama/Qwen) — локальный LLM на сервере
- Deepgram (распознавание речи)
- Cartesia (синтез речи)
- LiveKit (голосовой стриминг)
- MTS Exolve (телефония)

**Сервер:** 77.233.212.58 (Ubuntu 24.04)
**GitHub:** https://github.com/khak1m/new-voice

---

## Текущий статус

**Scenario Engine готов на 95%!**
**Voice Pipeline почти готов — Deepgram и Cartesia работают!**

**Сделано:**
- Scenario Engine (все компоненты)
- Ollama LLM на сервере
- Deepgram STT ✅ подключен
- Cartesia TTS ✅ подключен (3 голоса)
- LiveKit — нужно доустановить `livekit-api`

**API ключи в .env на сервере:**
- DEEPGRAM_API_KEY ✅
- CARTESIA_API_KEY ✅
- LIVEKIT_URL, API_KEY, API_SECRET ✅

**Следующее:**
1. На сервере: `pip install livekit-api`
2. Запустить: `python scripts/test_services.py`
3. Если всё ок — запустить Voice Agent
