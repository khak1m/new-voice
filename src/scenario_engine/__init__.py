"""
Scenario Engine — движок диалогов для голосовых AI-ботов.

Управляет потоком разговора на основе конфигурации:
- State machine для контроля этапов диалога
- Сбор данных от клиента (имя, телефон, услуга)
- Интеграция с RAG для ответов на вопросы
- Классификация результатов звонка
"""

from .models import (
    ScenarioConfig,
    CallContext,
    CallResult,
    Outcome,
    StateConfig,
    Transition,
    TurnResult,
    Message,
    FieldToCollect,
    FieldType,
    LanguagePolicy,
)
from .engine import ScenarioEngine
from .config_loader import ConfigLoader, load_config
from .state_machine import StateMachine
from .context_manager import ContextManager
from .field_extractor import FieldExtractor, ExtractionResult, ValidationResult
from .outcome_classifier import OutcomeClassifier, ClassificationResult
from .language_detector import LanguageDetector, DetectionResult
from .exceptions import (
    ScenarioEngineError,
    ConfigValidationError,
    StateTransitionError,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "ScenarioEngine",
    # Models
    "ScenarioConfig",
    "CallContext",
    "CallResult",
    "StateConfig",
    "Transition",
    "Outcome",
    "TurnResult",
    "Message",
    "FieldToCollect",
    "FieldType",
    "LanguagePolicy",
    # Components
    "ConfigLoader",
    "load_config",
    "StateMachine",
    "ContextManager",
    "FieldExtractor",
    "ExtractionResult",
    "ValidationResult",
    "OutcomeClassifier",
    "ClassificationResult",
    "LanguageDetector",
    "DetectionResult",
    # Exceptions
    "ScenarioEngineError",
    "ConfigValidationError",
    "StateTransitionError",
]
