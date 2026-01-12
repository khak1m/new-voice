"""
Модели данных для Scenario Engine.

Гибкая архитектура — клиент сам задаёт этапы и переходы.
LLM генерирует естественные ответы, а не шаблоны.
"""

from enum import Enum
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =============================================================================
# Базовые типы
# =============================================================================

class Outcome(str, Enum):
    """Результаты звонка."""
    LEAD = "lead"               # Лид — есть контакт и интерес
    CALLBACK = "callback"       # Нужен перезвон
    INFO_ONLY = "info_only"     # Только спросил информацию
    NOT_TARGET = "not_target"   # Не наш клиент
    FAILED = "failed"           # Неудача (таймаут, ошибка)
    CUSTOM = "custom"           # Кастомный outcome от клиента


class FieldType(str, Enum):
    """Типы данных для сбора."""
    TEXT = "text"
    PHONE = "phone"
    EMAIL = "email"
    DATE = "date"
    TIME = "time"
    NUMBER = "number"
    CHOICE = "choice"
    BOOLEAN = "boolean"


class LocalizedText(BaseModel):
    """Текст на разных языках."""
    ru: str = ""
    en: str = ""
    
    def get(self, lang: str) -> str:
        """Получить текст на нужном языке."""
        return getattr(self, lang, self.ru) or self.ru


class LanguagePolicy(BaseModel):
    """Политика определения и переключения языка."""
    default: str = "ru"
    detect: bool = True
    allow_switch: bool = True


# =============================================================================
# Гибкие этапы (States) — клиент задаёт сам
# =============================================================================

class FieldValidation(BaseModel):
    """Правила валидации поля."""
    pattern: Optional[str] = None           # Regex паттерн
    min_value: Optional[float] = None       # Минимальное значение
    max_value: Optional[float] = None       # Максимальное значение
    min_length: Optional[int] = None        # Минимальная длина
    max_length: Optional[int] = None        # Максимальная длина
    choices: list[dict] = Field(default_factory=list)  # Варианты выбора


class FieldToCollect(BaseModel):
    """Поле, которое нужно собрать на этапе."""
    id: str                                 # Уникальный ID поля
    type: FieldType = FieldType.TEXT        # Тип данных
    required: bool = True                   # Обязательное?
    description: str = ""                   # Описание для LLM (что это за поле)
    validation_hint: Optional[str] = None   # Подсказка для валидации
    validation: Optional[FieldValidation] = None  # Правила валидации
    examples: list[str] = Field(default_factory=list)  # Примеры значений


class StateConfig(BaseModel):
    """
    Конфигурация одного этапа диалога.
    
    Клиент сам задаёт:
    - Название этапа
    - Цель этапа (что бот должен сделать)
    - Какие данные собрать
    - Контекст для LLM
    """
    id: str                                 # Уникальный ID этапа
    name: LocalizedText                     # Название для отображения
    goal: str                               # Цель этапа (для LLM)
    
    # Что собирать на этом этапе
    collect_fields: list[FieldToCollect] = Field(default_factory=list)
    
    # Контекст для LLM
    system_prompt_addition: str = ""        # Дополнение к системному промпту
    examples: list[dict] = Field(default_factory=list)  # Примеры диалогов
    
    # Поведение
    use_knowledge_base: bool = False        # Использовать RAG на этом этапе
    max_turns: Optional[int] = None         # Лимит реплик на этапе
    
    # Флаги
    is_start: bool = False                  # Начальный этап
    is_end: bool = False                    # Конечный этап


# =============================================================================
# Переходы между этапами — клиент задаёт сам
# =============================================================================

class TransitionCondition(BaseModel):
    """Условие для перехода."""
    type: str                   # field_collected, intent_detected, keyword, custom
    field: Optional[str] = None # Для field_collected
    intent: Optional[str] = None # Для intent_detected
    keywords: list[str] = Field(default_factory=list)  # Для keyword
    custom_rule: Optional[str] = None  # Для custom (выражение)


class Transition(BaseModel):
    """
    Переход между этапами.
    
    Клиент задаёт:
    - Откуда и куда
    - При каком условии
    - Приоритет (если несколько переходов возможны)
    """
    from_state: str                         # ID исходного этапа
    to_state: str                           # ID целевого этапа
    condition: TransitionCondition          # Когда переходить
    priority: int = 0                       # Приоритет (выше = важнее)
    description: str = ""                   # Описание для понимания


# =============================================================================
# Outcomes — клиент задаёт правила классификации
# =============================================================================

class OutcomeRule(BaseModel):
    """Правило для определения outcome."""
    field: str                  # Какое поле проверять
    condition: str              # is_set, is_not_set, equals, contains, greater_than
    value: Optional[Any] = None # Значение для сравнения


class OutcomeConfig(BaseModel):
    """
    Конфигурация результата звонка.
    
    Клиент задаёт:
    - Какие outcomes возможны
    - По каким правилам определять
    """
    id: str                                 # ID outcome
    name: LocalizedText                     # Название
    rules: list[OutcomeRule] = Field(default_factory=list)  # Правила (AND)
    required_fields: list[str] = Field(default_factory=list)  # Обязательные поля
    is_default: bool = False                # Дефолтный outcome
    webhook_template: Optional[dict] = None # Шаблон для webhook


# =============================================================================
# Guardrails — защитные правила
# =============================================================================

class GuardrailRule(BaseModel):
    """Защитное правило."""
    id: str
    type: str                   # banned_topic, escalation, safety
    pattern: str                # Regex или ключевые слова
    action: str                 # respond, escalate, end_call
    response_hint: str = ""     # Подсказка для LLM как ответить


# =============================================================================
# Главная конфигурация сценария
# =============================================================================

class BotPersonality(BaseModel):
    """Личность бота — как он общается."""
    name: str = "Ассистент"                 # Имя бота
    role: str = ""                          # Роль (администратор, консультант)
    company: str = ""                       # Название компании
    tone: str = "friendly"                  # Тон: friendly, professional, casual
    language_style: str = ""                # Стиль речи (описание)
    
    # Системный промпт для LLM
    base_system_prompt: str = ""            # Базовый промпт


class LanguageConfig(BaseModel):
    """Настройки языка."""
    default: str = "ru"
    supported: list[str] = Field(default_factory=lambda: ["ru", "en"])
    auto_detect: bool = True
    allow_switch: bool = True


class LimitsConfig(BaseModel):
    """Лимиты и таймауты."""
    max_turns: int = 30                     # Максимум реплик за звонок
    max_turn_retries: int = 3               # Повторов на одну реплику
    silence_timeout_sec: int = 15           # Таймаут тишины
    max_call_duration_sec: int = 600        # Максимум длительность звонка


class ScenarioConfig(BaseModel):
    """
    Полная конфигурация сценария бота.
    
    Клиент настраивает:
    - Личность бота (как общается)
    - Этапы диалога (states)
    - Переходы между этапами
    - Правила классификации результатов
    - Защитные правила
    """
    version: str = "2.0"
    bot_id: str
    
    # Личность и стиль
    personality: BotPersonality
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    
    # Гибкие этапы и переходы
    states: list[StateConfig] = Field(default_factory=list)
    transitions: list[Transition] = Field(default_factory=list)
    
    # Результаты
    outcomes: list[OutcomeConfig] = Field(default_factory=list)
    
    # Защита
    guardrails: list[GuardrailRule] = Field(default_factory=list)
    
    # Лимиты
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    
    # RAG настройки
    knowledge_base_id: Optional[str] = None  # ID базы знаний
    rag_min_score: float = 0.7


# =============================================================================
# Контекст звонка (в памяти во время звонка)
# =============================================================================

class Message(BaseModel):
    """Сообщение в истории."""
    role: str                   # user, assistant, system
    content: str
    timestamp: float = 0.0
    state_id: Optional[str] = None


class CallContext(BaseModel):
    """
    Контекст звонка — хранится в памяти во время разговора.
    
    Отслеживает:
    - Текущий этап
    - Собранные данные
    - Историю диалога
    """
    call_id: str
    bot_id: str
    direction: str = "inbound"
    
    # Текущее состояние
    current_state_id: Optional[str] = None
    previous_state_id: Optional[str] = None
    language: str = "ru"
    
    # Счётчики
    turn_count: int = 0
    state_turn_count: int = 0               # Реплик на текущем этапе
    retry_count: int = 0
    support_questions_count: int = 0        # Вопросов в режиме поддержки
    
    # Собранные данные
    collected_data: dict[str, Any] = Field(default_factory=dict)
    
    # Флаги
    callback_requested: bool = False
    escalation_triggered: bool = False
    not_target_reason: Optional[str] = None
    
    # История
    messages: list[Message] = Field(default_factory=list)
    last_bot_message: Optional[str] = None  # Последнее сообщение бота
    
    # Время
    started_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Результаты
# =============================================================================

class CallResult(BaseModel):
    """Результат звонка."""
    call_id: str
    bot_id: str
    direction: str
    
    # Результат
    outcome: str                            # ID outcome
    outcome_data: dict[str, Any] = Field(default_factory=dict)
    
    # Данные
    collected_data: dict[str, Any] = Field(default_factory=dict)
    messages: list[Message] = Field(default_factory=list)
    
    # Метрики
    duration_sec: int = 0
    turn_count: int = 0
    states_visited: list[str] = Field(default_factory=list)
    language: str = "ru"
    ended_reason: str = "completed"


class TurnResult(BaseModel):
    """Результат обработки одной реплики."""
    response: str                           # Ответ бота (сгенерирован LLM)
    current_state_id: str
    should_end: bool = False
    outcome: Optional[str] = None
    collected_in_turn: dict[str, Any] = Field(default_factory=dict)
