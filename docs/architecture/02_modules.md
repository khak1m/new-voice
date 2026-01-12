# Module Specifications

## Module 1: Realtime Call Processing

### Purpose
Handle live voice calls with minimal latency.

### Components

```
src/realtime/
├── agent.py           # LiveKit agent entry point
├── pipeline.py        # STT → LLM → TTS orchestration
├── context.py         # Call context manager (in-memory)
├── prompts.py         # System prompts builder
└── handlers/
    ├── greeting.py    # Initial greeting logic
    ├── qualification.py  # Lead qualification
    └── booking.py     # Appointment booking
```

### Interfaces

```python
class RealtimeAgent:
    async def on_call_start(self, call_info: CallInfo) -> None
    async def on_speech(self, text: str) -> str
    async def on_call_end(self) -> CallResult
```

### Constraints
- Max 500ms response latency
- No database writes during call
- Memory limit: 512MB per call
- Graceful degradation on provider failure

---

## Module 2: Knowledge (RAG)

### Purpose
Store and retrieve company knowledge for bot responses.

### Components

```
src/knowledge/
├── processor.py       # File upload handler
├── chunker.py         # Text chunking strategies
├── embedder.py        # Embedding generation
├── retriever.py       # Qdrant search
└── formats/
    ├── pdf.py
    ├── docx.py
    ├── txt.py
    └── csv.py
```

### Interfaces

```python
class KnowledgeService:
    async def upload(self, bot_id: str, file: UploadFile) -> KnowledgeDoc
    async def search(self, bot_id: str, query: str, top_k: int = 5) -> List[Chunk]
    async def delete(self, bot_id: str, doc_id: str) -> None
    async def clear_bot(self, bot_id: str) -> None
```

### Chunking Strategy
- Chunk size: 500 tokens
- Overlap: 50 tokens
- Metadata: source file, page number, section

---

## Module 3: Post-Call Processing

### Purpose
Async processing after call completion.

### Components

```
src/postcall/
├── queue.py           # Task queue (Redis-based)
├── summarizer.py      # Call summary generation
├── extractor.py       # Lead/booking extraction
├── webhook.py         # External webhook sender
└── analytics.py       # Call metrics
```

### Interfaces

```python
class PostCallProcessor:
    async def process(self, call_id: str) -> None
    async def generate_summary(self, transcript: str) -> str
    async def extract_outcome(self, transcript: str, bot_config: BotConfig) -> Outcome
    async def send_webhook(self, outcome: Outcome, webhook_url: str) -> bool
```

### Queue Flow
```
Call Ends → Redis Queue → Worker picks up → Process → Save to DB → Webhook
```

---

## Module 4: Provider Layer

### Purpose
Abstract external services for easy swapping.

### Components

```
src/providers/
├── __init__.py        # Экспорт провайдеров
├── ollama_llm.py      # ✅ Ollama (локальный LLM)
├── groq_llm.py        # ✅ Groq (заблокирован в РФ)
├── stt/
│   ├── deepgram.py    # TODO
│   └── whisper.py     # TODO
├── tts/
│   ├── cartesia.py    # TODO
│   └── elevenlabs.py  # TODO
└── telephony/
    ├── exolve.py      # TODO
    └── twilio.py      # TODO
```

### LLM Providers

**Ollama (основной для MVP):**
- Работает локально на сервере
- Без блокировок и лимитов
- Модели: Llama 3.1, Qwen2, Mistral

**Groq (заблокирован в РФ):**
- Быстрый облачный API
- 403 Forbidden из России

### Interfaces

```python
class LLMProvider(Protocol):
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 150
    ) -> str: ...

class STTProvider(ABC):
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[str]

class TTSProvider(ABC):
    async def synthesize(self, text: str, voice_id: str) -> bytes
    async def synthesize_stream(self, text: str, voice_id: str) -> AsyncIterator[bytes]

class TelephonyProvider(ABC):
    async def connect_to_livekit(self, call_id: str, room: str) -> None
    async def hangup(self, call_id: str) -> None
```

---

## Module 5: Admin API

### Purpose
REST API for platform management.

### Components

```
src/api/
├── main.py            # FastAPI app
├── routes/
│   ├── companies.py
│   ├── bots.py
│   ├── knowledge.py
│   ├── calls.py
│   └── webhooks.py
├── schemas/           # Pydantic models
├── deps.py            # Dependencies
└── auth.py            # API key auth
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /companies | Create company |
| GET | /companies/{id}/bots | List bots |
| POST | /bots | Create bot |
| PUT | /bots/{id}/config | Update bot config |
| POST | /bots/{id}/knowledge | Upload knowledge file |
| GET | /calls | List calls with filters |
| GET | /calls/{id} | Call details + transcript |

---

## Module 6: Scenario Engine

### Purpose
Config-based conversation flow control.

### Config Structure

```yaml
# bot_config.yaml
bot_id: "salon-bot-1"
language: "ru"
voice_id: "russian-female-1"

greeting: "Здравствуйте! Салон красоты Элегант. Чем могу помочь?"

scenarios:
  - name: "booking"
    trigger_keywords: ["записаться", "запись", "свободно"]
    collect_fields:
      - name: "service"
        prompt: "На какую услугу хотите записаться?"
      - name: "date"
        prompt: "На какой день?"
      - name: "time"
        prompt: "В какое время?"
      - name: "phone"
        prompt: "Оставьте номер для подтверждения"
    on_complete: "booking_created"

  - name: "support"
    trigger_keywords: ["вопрос", "узнать", "сколько стоит"]
    use_knowledge_base: true

fallback: "Извините, не совсем поняла. Вы хотите записаться или у вас вопрос?"

max_turns: 20
silence_timeout_sec: 10
```

### Engine Logic
1. Match user intent to scenario
2. If scenario active → follow collect_fields
3. If no match → use knowledge base
4. If still no match → fallback response
