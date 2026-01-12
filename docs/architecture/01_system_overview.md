# System Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ADMIN PANEL (FastAPI + Web UI)                 │
│  • Company management                                                        │
│  • Bot configuration                                                         │
│  • Knowledge upload                                                          │
│  • Call logs & outcomes                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CORE API LAYER                                  │
│  • REST API endpoints                                                        │
│  • Webhook dispatcher                                                        │
│  • Authentication                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   REALTIME MODULE    │  │   KNOWLEDGE MODULE   │  │  POST-CALL MODULE    │
│   (Call Processing)  │  │   (RAG System)       │  │  (Async Processing)  │
│                      │  │                      │  │                      │
│  • LiveKit Agent     │  │  • File processor    │  │  • Call summary      │
│  • STT pipeline      │  │  • Chunking          │  │  • Lead extraction   │
│  • LLM orchestrator  │  │  • Embeddings        │  │  • Webhook sender    │
│  • TTS pipeline      │  │  • Qdrant storage    │  │  • Analytics         │
└──────────┬───────────┘  └──────────────────────┘  └──────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PROVIDER LAYER (Pluggable)                         │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   LLM Provider  │   STT Provider  │   TTS Provider  │  Telephony Provider   │
│   • Ollama ✅   │   • Deepgram    │   • Cartesia    │  • MTS Exolve         │
│   • Groq        │   • Whisper     │   • ElevenLabs  │  • Twilio             │
│   • OpenAI      │   • Local STT   │   • Local TTS   │  • SIP Generic        │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├─────────────────────────────────┬───────────────────────────────────────────┤
│         PostgreSQL              │              Qdrant                        │
│  • Companies                    │  • Knowledge embeddings                    │
│  • Bots                         │  • One collection per bot                  │
│  • Calls                        │                                            │
│  • Outcomes                     │                                            │
│  • Knowledge metadata           │                                            │
└─────────────────────────────────┴───────────────────────────────────────────┘
```

## Module Separation

### 1. Realtime Module (Hot Path)
- Handles live call audio
- Must be lightweight (<500ms latency)
- Runs in LiveKit agent process
- NO database writes during call (only in-memory)

### 2. Post-Call Module (Cold Path)
- Async processing after call ends
- Generates summaries, extracts leads
- Writes to database
- Sends webhooks
- Can be slower, more resource-intensive

### 3. Knowledge Module
- File upload and processing
- Chunking strategies
- Embedding generation
- Qdrant index management

## Data Flow: Inbound Call

```
1. Phone Call → MTS Exolve
2. Exolve → SIP → LiveKit Room
3. LiveKit → Voice Agent joins room
4. Audio Stream → Deepgram (STT) → Text
5. Text + RAG Context → OpenAI (LLM) → Response
6. Response → Cartesia (TTS) → Audio
7. Audio → LiveKit → Exolve → Caller
8. Call Ends → Post-Call Queue
9. Async: Summary + Lead Extraction + Webhook
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate realtime/async | Low-resource server, reliability |
| Provider abstraction | Future flexibility, vendor lock-in prevention |
| Config-based scenarios | MVP simplicity, no visual editor needed |
| One Qdrant collection per bot | Isolation, easy deletion |
| PostgreSQL over Supabase | Future on-prem compliance |
| No CRM integration | MVP scope reduction |
