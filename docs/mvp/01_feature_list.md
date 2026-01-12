# MVP Feature List

## ✅ In Scope (MVP)

### Core Platform

| Feature | Description | Priority |
|---------|-------------|----------|
| Company management | Create, edit, deactivate companies | P0 |
| Bot management | Create, configure, delete bots | P0 |
| API key auth | Simple API key authentication | P0 |
| Basic admin UI | Web interface for management | P1 |

### Voice Bot

| Feature | Description | Priority |
|---------|-------------|----------|
| Inbound calls | Receive and handle incoming calls | P0 |
| Speech recognition | Real-time STT (Deepgram) | P0 |
| AI responses | LLM-powered conversation (OpenAI) | P0 |
| Voice synthesis | Real-time TTS (Cartesia) | P0 |
| Multilingual | Russian and English support | P0 |
| Greeting | Configurable greeting message | P0 |
| Fallback | Handle unrecognized intents | P0 |

### Knowledge Base (RAG)

| Feature | Description | Priority |
|---------|-------------|----------|
| File upload | PDF, DOCX, TXT, CSV support | P0 |
| Chunking | Automatic text splitting | P0 |
| Embeddings | Vector generation | P0 |
| Semantic search | Query knowledge base | P0 |
| Per-bot isolation | Separate knowledge per bot | P0 |

### Scenarios

| Feature | Description | Priority |
|---------|-------------|----------|
| Config-based scenarios | YAML/JSON scenario definition | P0 |
| Lead qualification | Collect required fields | P0 |
| Booking capture | Appointment data collection | P0 |
| Support mode | Answer from knowledge base | P0 |

### Call Processing

| Feature | Description | Priority |
|---------|-------------|----------|
| Call logging | Store all calls | P0 |
| Transcript | Save conversation text | P0 |
| Post-call summary | AI-generated summary | P1 |
| Outcome extraction | Extract structured data | P1 |
| Webhook delivery | Send outcomes to external URL | P1 |

### Providers

| Feature | Description | Priority |
|---------|-------------|----------|
| OpenAI LLM | GPT-4 integration | P0 |
| Deepgram STT | Speech recognition | P0 |
| Cartesia TTS | Voice synthesis | P0 |
| MTS Exolve | Telephony | P0 |
| Provider abstraction | Pluggable architecture | P1 |

---

## ❌ Out of Scope (MVP)

### Explicitly Excluded

| Feature | Reason | Future Phase |
|---------|--------|--------------|
| Outbound calls | Complexity, MVP focus on inbound | Phase 2 |
| CRM integration | Scope reduction, use webhooks | Phase 2 |
| Visual scenario editor | Complexity, config is enough | Phase 3 |
| Call recording storage | Storage costs, compliance | Phase 2 |
| Real-time dashboard | Nice-to-have, not critical | Phase 2 |
| Multi-tenant billing | No monetization in MVP | Phase 3 |
| SSO / OAuth | Simple API keys sufficient | Phase 2 |
| Mobile app | Web-only for MVP | Phase 3 |
| Call transfer to human | Complexity | Phase 2 |
| SMS integration | Voice-only MVP | Phase 2 |
| Voicemail | Not needed for MVP | Phase 2 |
| A/B testing scenarios | Optimization feature | Phase 3 |
| Analytics dashboard | Basic logs sufficient | Phase 2 |
| 152-FZ compliance | Test mode only | Production |
| On-premise deployment | Cloud MVP first | Production |
| GPU inference | Cloud APIs for MVP | Production |

### Technical Debt Accepted

| Item | Reason |
|------|--------|
| No horizontal scaling | Single server MVP |
| Basic error handling | Will improve in Phase 2 |
| Minimal monitoring | Logs only for MVP |
| No rate limiting | Trusted users only |
| No backup automation | Manual backups |

---

## MVP Success Criteria

1. **Functional**
   - [ ] Bot answers inbound call within 3 seconds
   - [ ] Bot understands and responds in RU/EN
   - [ ] Bot uses knowledge base for answers
   - [ ] Bot collects lead/booking data
   - [ ] Outcomes saved and webhook sent

2. **Performance**
   - [ ] Response latency < 500ms (STT+LLM+TTS)
   - [ ] Handles 5 concurrent calls
   - [ ] 99% uptime during business hours

3. **Usability**
   - [ ] Create bot in < 5 minutes
   - [ ] Upload knowledge in < 2 minutes
   - [ ] View call logs with transcripts
