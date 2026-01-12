# Scenario Engine MVP Specification

## Document Info
- **Version:** 1.0
- **Status:** Draft
- **Last Updated:** 2026-01-12

---

# Part 1: Goals and Scope

## 1.1 Goals

1. Provide config-driven conversation flow without code changes
2. Support deterministic state machine (LLM is helper, not brain)
3. Handle inbound and outbound calls with same engine
4. Collect structured data (leads, bookings) reliably
5. Integrate with RAG knowledge base for support questions
6. Classify call outcomes deterministically
7. Work reliably with weak/slow LLMs

## 1.2 Non-Goals (MVP)

1. ❌ Visual scenario editor (config files only)
2. ❌ Complex branching logic (max 2 levels deep)
3. ❌ A/B testing of scenarios
4. ❌ Real-time scenario updates during call
5. ❌ CRM integration (webhook only)
6. ❌ Call transfer to human agent
7. ❌ Multi-bot handoff
8. ❌ Sentiment analysis
9. ❌ Custom NLU models

---

# Part 2: State Machine

## 2.1 Minimal State Set

```
┌─────────────┐
│    INIT     │ ← Call connected
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  GREETING   │ ← Bot speaks first
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   INTAKE    │◄───►│   SUPPORT   │
│ (collect    │     │ (RAG query) │
│  fields)    │     └─────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  CONFIRM    │ ← Verify collected data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   CLOSING   │ ← Final message
└──────┬──────┘
       │
       ▼
┌─────────────┐
│     END     │ ← Hangup + outcome
└─────────────┘
```

## 2.2 State Definitions

| State | Purpose | Exit Conditions |
|-------|---------|-----------------|
| INIT | System initialization | Always → GREETING |
| GREETING | Deliver opening message | User responds → INTAKE |
| INTAKE | Collect required fields | All fields collected → CONFIRM |
| SUPPORT | Answer from knowledge base | Answer delivered → return to previous |
| CONFIRM | Verify collected data | Confirmed → CLOSING |
| CLOSING | Deliver goodbye message | Message complete → END |
| END | Terminate call, save outcome | Terminal state |

## 2.3 Transitions

```yaml
transitions:
  INIT:
    - to: GREETING
      trigger: call_connected

  GREETING:
    - to: INTAKE
      trigger: user_response
    - to: END
      trigger: silence_timeout
      outcome: FAILED

  INTAKE:
    - to: SUPPORT
      trigger: support_question_detected
    - to: CONFIRM
      trigger: all_fields_collected
    - to: END
      trigger: not_target_detected
      outcome: NOT_TARGET
    - to: END
      trigger: max_turns_exceeded
      outcome: FAILED

  SUPPORT:
    - to: INTAKE
      trigger: answer_delivered
    - to: END
      trigger: escalation_requested
      outcome: CALLBACK

  CONFIRM:
    - to: INTAKE
      trigger: user_correction
    - to: CLOSING
      trigger: user_confirmed
    - to: END
      trigger: user_declined
      outcome: INFO_ONLY

  CLOSING:
    - to: END
      trigger: message_complete
      outcome: LEAD  # or CALLBACK based on data
```

---

# Part 3: Configuration Schema

## 3.1 Entity Relationships

```
Company (1) ──────► (N) Bot
                         │
                         ▼
                    ScenarioConfig
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    IntakeFields    DialogFlow      Outcomes
```

## 3.2 ScenarioConfig Schema

```yaml
# Root schema
scenario_config:
  version: string           # "1.0"
  bot_id: uuid              # Reference to bot
  
  # REQUIRED SECTIONS
  goal:                     # What this bot does
    ru: string
    en: string
  
  language_policy:          # Language handling
    default: "ru" | "en"
    detect: boolean         # Auto-detect from user
    allow_switch: boolean   # Allow mid-call switch
  
  greeting:                 # Opening message
    inbound:
      ru: string
      en: string
    outbound:
      ru: string
      en: string
  
  intake_fields: []         # Fields to collect (see 3.3)
  
  dialog_flow:              # Conversation settings (see 3.4)
    max_turns: integer
    silence_timeout_sec: integer
    fallback_phrases: {}
    confirmation_strategy: string
  
  outcomes: []              # Outcome definitions (see 3.5)
  
  # OPTIONAL SECTIONS
  support_mode:             # RAG integration (see 3.6)
    enabled: boolean
    trigger_keywords: []
    fallback_phrase: {}
  
  guardrails:               # Safety settings (see 3.7)
    banned_topics: []
    escalation_triggers: []
    max_repeats: integer
```


## 3.3 Intake Fields Schema

```yaml
intake_fields:
  - id: string              # Unique field ID (e.g., "client_name")
    type: "text" | "phone" | "email" | "date" | "time" | "number" | "choice"
    required: boolean
    
    ask_template:           # How to ask for this field
      ru: string
      en: string
    
    retry_template:         # If validation fails
      ru: string
      en: string
    
    validation:             # Optional validation rules
      pattern: regex        # For text/phone/email
      min: number           # For number
      max: number
      choices: []           # For choice type
    
    extract_hints: []       # Keywords to help extraction
    confirm_back: boolean   # Repeat value back to user
```

**Supported Field Types:**

| Type | Validation | Example |
|------|------------|---------|
| text | min/max length | Name, address |
| phone | E.164 format | +79001234567 |
| email | RFC 5322 | user@example.com |
| date | ISO 8601 | 2026-01-15 |
| time | HH:MM | 14:30 |
| number | min/max range | Age, quantity |
| choice | enum list | Service type |

## 3.4 Dialog Flow Schema

```yaml
dialog_flow:
  max_turns: 20                    # Max conversation turns
  silence_timeout_sec: 10          # Hangup after silence
  interrupt_handling: "allow" | "queue" | "ignore"
  
  fallback_phrases:
    not_understood:
      ru: "Извините, не расслышала. Повторите, пожалуйста."
      en: "Sorry, I didn't catch that. Could you repeat?"
    
    out_of_scope:
      ru: "К сожалению, я не могу помочь с этим вопросом."
      en: "Unfortunately, I can't help with that."
    
    technical_error:
      ru: "Произошла техническая ошибка. Перезвоните позже."
      en: "A technical error occurred. Please call back later."
  
  confirmation_strategy: "explicit" | "implicit" | "none"
  # explicit: "Вы сказали X, верно?"
  # implicit: "Записала X. Что дальше?"
  # none: No confirmation
  
  repeat_policy:
    max_repeats: 3                 # Per field
    rephrase_on_repeat: true       # Use different wording
```

## 3.5 Outcomes Schema

```yaml
outcomes:
  - id: "LEAD"
    display_name:
      ru: "Лид"
      en: "Lead"
    
    # Deterministic rules (ALL must be true)
    rules:
      - field: "client_phone"
        condition: "is_set"
      - field: "service_type"
        condition: "is_set"
    
    # Required evidence for this outcome
    required_evidence:
      - "client_phone"
      - "service_type"
    
    # Webhook payload template
    webhook_template:
      type: "lead"
      phone: "{{client_phone}}"
      service: "{{service_type}}"
      name: "{{client_name}}"

  - id: "CALLBACK"
    rules:
      - field: "callback_requested"
        condition: "equals"
        value: true
    required_evidence:
      - "client_phone"

  - id: "INFO_ONLY"
    rules:
      - field: "support_questions_count"
        condition: "greater_than"
        value: 0
      - field: "client_phone"
        condition: "is_not_set"

  - id: "NOT_TARGET"
    rules:
      - field: "not_target_reason"
        condition: "is_set"

  - id: "FAILED"
    # Default if no other outcome matches
    is_default: true
```

**Outcome Taxonomy:**

| Outcome | Definition | Required Evidence |
|---------|------------|-------------------|
| LEAD | Qualified prospect with contact | phone + intent |
| CALLBACK | User requested callback | phone + request |
| INFO_ONLY | Got info, no contact left | questions asked |
| NOT_TARGET | Not our customer | reason detected |
| FAILED | Technical/timeout/unclear | none |

## 3.6 Support Mode Schema

```yaml
support_mode:
  enabled: true
  
  # When to trigger RAG search
  trigger_keywords:
    ru: ["вопрос", "сколько стоит", "как", "что", "где", "когда"]
    en: ["question", "how much", "how", "what", "where", "when"]
  
  # Or trigger on intent classification
  trigger_intents: ["question", "pricing", "info_request"]
  
  # RAG settings
  rag_config:
    top_k: 3                       # Number of chunks to retrieve
    min_score: 0.7                 # Minimum relevance score
    include_source: false          # Cite source in answer
  
  # If RAG returns nothing
  fallback_phrase:
    ru: "К сожалению, у меня нет информации по этому вопросу. Могу записать вас на консультацию."
    en: "Unfortunately, I don't have information on that. I can schedule a consultation for you."
  
  # Max support questions before redirect
  max_questions: 5
  redirect_after_max:
    ru: "У вас много вопросов. Давайте я запишу вас на консультацию со специалистом."
    en: "You have many questions. Let me schedule a consultation with a specialist."
```

## 3.7 Guardrails Schema

```yaml
guardrails:
  # Topics to refuse
  banned_topics:
    - pattern: "политик|выбор|голосов"
      response:
        ru: "Извините, я не обсуждаю такие темы."
        en: "Sorry, I don't discuss such topics."
    
    - pattern: "конкурент|другая компания"
      response:
        ru: "Я могу рассказать только о наших услугах."
        en: "I can only tell you about our services."
  
  # Triggers for escalation/callback
  escalation_triggers:
    - pattern: "оператор|человек|менеджер|живой"
      action: "request_callback"
      response:
        ru: "Хорошо, оставьте номер, и наш менеджер перезвонит."
        en: "Sure, leave your number and our manager will call back."
    
    - pattern: "жалоба|претензия|недовол"
      action: "request_callback"
      response:
        ru: "Понимаю вашу ситуацию. Оставьте номер для связи с руководством."
        en: "I understand. Leave your number to speak with management."
  
  # Repeat protection
  max_repeats: 3
  on_max_repeats:
    ru: "Кажется, у нас проблемы со связью. Давайте я запишу ваш номер для перезвона."
    en: "Seems we have connection issues. Let me take your number for a callback."
```


---

# Part 4: Edge Case Handling

## 4.1 User Questions (Support/RAG)

```
Detection:
1. Check trigger_keywords match
2. Check if user utterance is a question (ends with ?)
3. LLM intent classification (if enabled)

Flow:
1. Pause current intake state
2. Query RAG with user question
3. If score >= min_score → deliver answer
4. If score < min_score → deliver fallback_phrase
5. Return to previous state
6. Increment support_questions_count

Constraints:
- Max 5 support questions per call (configurable)
- After max → redirect to callback/specialist
```

## 4.2 Interruptions

```
Strategy: "allow" (default)

When user interrupts bot speech:
1. Stop TTS immediately
2. Process user utterance
3. If new intent detected → handle it
4. If continuation of current topic → continue flow

Strategy: "queue"
1. Complete current TTS
2. Then process user utterance

Strategy: "ignore"
1. Ignore until bot finishes speaking
```

## 4.3 Repeats

```
When user says "repeat" / "что?" / "не понял":
1. Increment repeat_count for current prompt
2. If repeat_count <= max_repeats:
   - If rephrase_on_repeat: use alternative phrasing
   - Else: repeat same phrase
3. If repeat_count > max_repeats:
   - Trigger escalation (request callback)
   - Set outcome = CALLBACK
```

## 4.4 Unclear Speech

```
When STT confidence < threshold OR empty result:
1. Deliver not_understood fallback phrase
2. Increment unclear_count
3. If unclear_count > 3:
   - "Кажется, плохая связь. Оставьте номер для перезвона."
   - Set outcome = CALLBACK

When extracted value fails validation:
1. Deliver retry_template for that field
2. Increment field_retry_count
3. If field_retry_count > 2:
   - Skip field if not required
   - Or escalate if required
```

## 4.5 Language Switching

```
If language_policy.detect = true:
1. Detect language from first user utterance
2. Switch all responses to detected language

If language_policy.allow_switch = true:
1. Monitor for language change mid-call
2. If detected → switch responses
3. Log language_switched event

If allow_switch = false:
1. Continue in default language
2. Add note to transcript
```

---

# Part 5: Outcome Classification

## 5.1 Deterministic Rules

Outcomes are determined by rule evaluation, NOT by LLM:

```python
def classify_outcome(call_context):
    # Check rules in priority order
    
    # 1. NOT_TARGET (highest priority)
    if call_context.not_target_reason:
        return "NOT_TARGET"
    
    # 2. LEAD (has contact + intent)
    if call_context.client_phone and call_context.service_type:
        return "LEAD"
    
    # 3. CALLBACK (requested or escalated)
    if call_context.callback_requested and call_context.client_phone:
        return "CALLBACK"
    
    # 4. INFO_ONLY (asked questions, no contact)
    if call_context.support_questions_count > 0:
        return "INFO_ONLY"
    
    # 5. FAILED (default)
    return "FAILED"
```

## 5.2 Evidence Requirements

| Outcome | Required Fields | Optional Fields |
|---------|-----------------|-----------------|
| LEAD | phone, service_type | name, date, time |
| CALLBACK | phone, callback_reason | name |
| INFO_ONLY | - | questions_asked |
| NOT_TARGET | not_target_reason | - |
| FAILED | - | failure_reason |

## 5.3 Not-Target Detection

```yaml
not_target_triggers:
  - pattern: "ошиблись номером|не туда попал"
    reason: "wrong_number"
  
  - pattern: "не интересует|не нужно|отстаньте"
    reason: "not_interested"
  
  - pattern: "уже есть|уже записан|уже клиент"
    reason: "existing_customer"
  
  - pattern: "другой город|не ваш регион"
    reason: "wrong_location"
```

---

# Part 6: Complete Example Config

```yaml
# Beauty Salon Bot - Reception + Qualification + Booking + Support
version: "1.0"
bot_id: "salon-bot-001"

goal:
  ru: "Приём звонков, запись на услуги, ответы на вопросы о салоне"
  en: "Receive calls, book appointments, answer questions about the salon"

language_policy:
  default: "ru"
  detect: true
  allow_switch: true

greeting:
  inbound:
    ru: "Здравствуйте! Салон красоты Элегант. Меня зовут Алиса. Чем могу помочь?"
    en: "Hello! Elegant Beauty Salon. My name is Alice. How can I help you?"
  outbound:
    ru: "Здравствуйте! Это салон красоты Элегант. Звоню подтвердить вашу запись."
    en: "Hello! This is Elegant Beauty Salon. I'm calling to confirm your appointment."

intake_fields:
  - id: "service_type"
    type: "choice"
    required: true
    ask_template:
      ru: "На какую услугу хотите записаться?"
      en: "What service would you like to book?"
    retry_template:
      ru: "У нас есть маникюр, педикюр, стрижка и окрашивание. Что выберете?"
      en: "We have manicure, pedicure, haircut and coloring. What would you choose?"
    validation:
      choices:
        - id: "manicure"
          ru: ["маникюр", "ногти", "руки"]
          en: ["manicure", "nails", "hands"]
        - id: "pedicure"
          ru: ["педикюр", "ноги", "стопы"]
          en: ["pedicure", "feet"]
        - id: "haircut"
          ru: ["стрижка", "подстричься", "волосы"]
          en: ["haircut", "hair", "cut"]
        - id: "coloring"
          ru: ["окрашивание", "покрасить", "цвет"]
          en: ["coloring", "color", "dye"]
    confirm_back: true

  - id: "preferred_date"
    type: "date"
    required: true
    ask_template:
      ru: "На какой день хотите записаться?"
      en: "What day would you like to book?"
    retry_template:
      ru: "Назовите дату, например, завтра или пятница."
      en: "Please say a date, for example, tomorrow or Friday."
    extract_hints: ["завтра", "послезавтра", "понедельник", "вторник"]
    confirm_back: true

  - id: "preferred_time"
    type: "time"
    required: true
    ask_template:
      ru: "В какое время удобно?"
      en: "What time works for you?"
    retry_template:
      ru: "Мы работаем с 9 до 21. Какое время предпочитаете?"
      en: "We're open 9 AM to 9 PM. What time do you prefer?"
    validation:
      min: "09:00"
      max: "21:00"
    confirm_back: true

  - id: "client_name"
    type: "text"
    required: true
    ask_template:
      ru: "Как вас зовут?"
      en: "What's your name?"
    retry_template:
      ru: "Подскажите ваше имя для записи."
      en: "Please tell me your name for the booking."
    confirm_back: false

  - id: "client_phone"
    type: "phone"
    required: true
    ask_template:
      ru: "Оставьте номер телефона для подтверждения записи."
      en: "Please leave your phone number to confirm the booking."
    retry_template:
      ru: "Продиктуйте номер телефона, начиная с 8 или +7."
      en: "Please say your phone number."
    validation:
      pattern: "^\\+?[78]\\d{10}$"
    confirm_back: true

dialog_flow:
  max_turns: 25
  silence_timeout_sec: 15
  interrupt_handling: "allow"
  
  fallback_phrases:
    not_understood:
      ru: "Извините, не расслышала. Повторите, пожалуйста."
      en: "Sorry, I didn't catch that. Could you repeat?"
    out_of_scope:
      ru: "К сожалению, я не могу помочь с этим. Хотите записаться на услугу?"
      en: "Unfortunately, I can't help with that. Would you like to book a service?"
    technical_error:
      ru: "Произошла ошибка. Пожалуйста, перезвоните или оставьте номер."
      en: "An error occurred. Please call back or leave your number."
  
  confirmation_strategy: "explicit"
  
  repeat_policy:
    max_repeats: 3
    rephrase_on_repeat: true

support_mode:
  enabled: true
  trigger_keywords:
    ru: ["сколько стоит", "цена", "прайс", "адрес", "где находитесь", "как добраться", "время работы", "вопрос"]
    en: ["how much", "price", "cost", "address", "where", "location", "hours", "question"]
  rag_config:
    top_k: 3
    min_score: 0.7
    include_source: false
  fallback_phrase:
    ru: "У меня нет точной информации. Могу записать вас на консультацию."
    en: "I don't have exact information. I can book a consultation for you."
  max_questions: 5

outcomes:
  - id: "LEAD"
    display_name:
      ru: "Запись"
      en: "Booking"
    rules:
      - field: "client_phone"
        condition: "is_set"
      - field: "service_type"
        condition: "is_set"
      - field: "preferred_date"
        condition: "is_set"
    required_evidence:
      - "client_phone"
      - "service_type"
      - "preferred_date"
      - "client_name"
    webhook_template:
      type: "booking"
      service: "{{service_type}}"
      date: "{{preferred_date}}"
      time: "{{preferred_time}}"
      client_name: "{{client_name}}"
      client_phone: "{{client_phone}}"

  - id: "CALLBACK"
    display_name:
      ru: "Перезвонить"
      en: "Callback"
    rules:
      - field: "callback_requested"
        condition: "equals"
        value: true
    required_evidence:
      - "client_phone"

  - id: "INFO_ONLY"
    display_name:
      ru: "Только информация"
      en: "Info Only"
    rules:
      - field: "support_questions_count"
        condition: "greater_than"
        value: 0
      - field: "client_phone"
        condition: "is_not_set"

  - id: "NOT_TARGET"
    display_name:
      ru: "Не целевой"
      en: "Not Target"
    rules:
      - field: "not_target_reason"
        condition: "is_set"

  - id: "FAILED"
    display_name:
      ru: "Неуспешный"
      en: "Failed"
    is_default: true

guardrails:
  banned_topics:
    - pattern: "политик|выбор|голосов|война"
      response:
        ru: "Извините, я не обсуждаю такие темы. Могу помочь с записью?"
        en: "Sorry, I don't discuss such topics. Can I help with a booking?"
  
  escalation_triggers:
    - pattern: "оператор|человек|менеджер|администратор"
      action: "request_callback"
      response:
        ru: "Хорошо, оставьте номер, и администратор перезвонит в течение 15 минут."
        en: "Sure, leave your number and an administrator will call back within 15 minutes."
    
    - pattern: "жалоба|претензия|недовольн|плохо"
      action: "request_callback"
      response:
        ru: "Мне очень жаль это слышать. Оставьте номер, руководитель свяжется с вами."
        en: "I'm sorry to hear that. Leave your number and a manager will contact you."
  
  max_repeats: 3
  on_max_repeats:
    ru: "Кажется, плохая связь. Оставьте номер, мы перезвоним."
    en: "Seems like a bad connection. Leave your number, we'll call back."

closing_messages:
  success:
    ru: "Отлично! Записала вас на {{service_type}} на {{preferred_date}} в {{preferred_time}}. Ждём вас! До свидания."
    en: "Great! I've booked you for {{service_type}} on {{preferred_date}} at {{preferred_time}}. See you then! Goodbye."
  callback:
    ru: "Хорошо, мы перезвоним вам в ближайшее время. До свидания!"
    en: "Okay, we'll call you back soon. Goodbye!"
  info_only:
    ru: "Рада была помочь! Если захотите записаться — звоните. До свидания!"
    en: "Glad I could help! Call us if you'd like to book. Goodbye!"
  failed:
    ru: "Спасибо за звонок. До свидания!"
    en: "Thank you for calling. Goodbye!"
```
