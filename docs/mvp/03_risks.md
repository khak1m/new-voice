# Risks and Mitigations

## Risk Matrix

| Risk | Probability | Impact | Score | Mitigation |
|------|-------------|--------|-------|------------|
| LLM latency spikes | High | High | 🔴 | Streaming, timeouts, fallbacks |
| Provider API failures | Medium | High | 🟠 | Retries, circuit breaker, fallback providers |
| Server resource limits | High | Medium | 🟠 | Optimize memory, queue overflow protection |
| STT accuracy issues | Medium | Medium | 🟡 | Prompt engineering, confirmation flows |
| TTS quality/naturalness | Low | Medium | 🟡 | Voice selection, SSML tuning |
| Telephony connection drops | Medium | High | 🟠 | Reconnection logic, graceful hangup |
| Knowledge retrieval misses | Medium | Medium | 🟡 | Chunking tuning, fallback responses |

---

## Detailed Risk Analysis

### 1. LLM Instability

**Risk:** OpenAI/Anthropic API latency spikes or outages

**Impact:** 
- Call response delays >2 seconds
- Poor user experience
- Dropped calls

**Mitigations:**
```
1. Streaming responses (don't wait for full completion)
2. Aggressive timeouts (3 sec max for first token)
3. Fallback to simpler prompts on timeout
4. Pre-generated responses for common intents
5. Circuit breaker pattern (stop calling if >3 failures)
```

**Fallback Chain:**
```
GPT-4 → GPT-3.5-turbo → Pre-generated response → "Please hold"
```

---

### 2. Response Latency

**Risk:** Total pipeline latency exceeds acceptable threshold

**Target:** <500ms from user speech end to bot speech start

**Breakdown:**
| Component | Target | Max |
|-----------|--------|-----|
| STT | 100ms | 200ms |
| LLM (first token) | 200ms | 500ms |
| TTS (first chunk) | 100ms | 200ms |
| Network overhead | 50ms | 100ms |

**Mitigations:**
```
1. Use streaming for all components
2. Start TTS before LLM completes (sentence-by-sentence)
3. Pre-warm connections (keep-alive)
4. Edge deployment for telephony
5. Optimize prompt length (shorter = faster)
```

---

### 3. Provider Failures

**Risk:** External API becomes unavailable

**Mitigations:**
```
1. Provider abstraction layer (easy swap)
2. Health checks every 30 seconds
3. Automatic failover to backup provider
4. Graceful degradation (limited functionality)
5. Alert on provider errors
```

**Failover Matrix:**
| Primary | Backup | Degraded Mode |
|---------|--------|---------------|
| OpenAI | Anthropic | Simpler prompts |
| Deepgram | Whisper API | Higher latency |
| Cartesia | ElevenLabs | Different voice |
| Exolve | - | No calls |

---

### 4. Server Resource Limits

**Risk:** 2 vCPU / 4GB RAM insufficient for concurrent calls

**Constraints:**
- Max 5 concurrent calls target
- ~500MB per call (agent + buffers)
- CPU spikes during audio processing

**Mitigations:**
```
1. Separate realtime from async processing
2. Memory limits per call (kill if exceeded)
3. Queue overflow protection (reject new calls)
4. Offload heavy processing to post-call
5. Monitor and alert on resource usage
```

**Resource Budget:**
| Component | Memory | CPU |
|-----------|--------|-----|
| System | 500MB | - |
| PostgreSQL | 256MB | 0.1 |
| Qdrant | 512MB | 0.1 |
| Redis | 128MB | 0.05 |
| API Server | 256MB | 0.1 |
| Per Call Agent | 400MB | 0.3 |
| **Total (5 calls)** | **3.6GB** | **1.85** |

---

### 5. STT Accuracy

**Risk:** Speech recognition errors lead to wrong responses

**Common Issues:**
- Background noise
- Accents
- Domain-specific terms
- Numbers and dates

**Mitigations:**
```
1. Use Deepgram Nova-2 (best accuracy)
2. Custom vocabulary for domain terms
3. Confirmation for critical data (phone, dates)
4. "Did you mean...?" clarification
5. Log and review misrecognitions
```

---

### 6. Knowledge Retrieval Quality

**Risk:** RAG returns irrelevant or no results

**Mitigations:**
```
1. Tune chunk size (500 tokens optimal)
2. Overlap chunks (50 tokens)
3. Hybrid search (semantic + keyword)
4. Confidence threshold (ignore low scores)
5. Fallback: "I don't have that information"
6. Regular knowledge base review
```

---

## Monitoring & Alerts

### Key Metrics to Track

| Metric | Warning | Critical |
|--------|---------|----------|
| Response latency | >500ms | >1000ms |
| LLM error rate | >1% | >5% |
| STT error rate | >2% | >10% |
| Call drop rate | >1% | >5% |
| Memory usage | >80% | >95% |
| CPU usage | >70% | >90% |
| Queue depth | >10 | >50 |

### Alert Channels
- Telegram bot for critical alerts
- Email for warnings
- Dashboard for metrics

---

## Contingency Plans

### If OpenAI is down:
1. Switch to Anthropic automatically
2. If both down → pre-recorded "technical difficulties" message
3. Log all affected calls for retry

### If server overloaded:
1. Reject new calls with busy signal
2. Prioritize existing calls
3. Scale up (manual for MVP)

### If telephony fails:
1. No automatic failover (single provider)
2. Alert immediately
3. Manual intervention required
