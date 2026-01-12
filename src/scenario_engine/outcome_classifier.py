"""
OutcomeClassifier — классификация результата звонка.

В конце звонка определяет что получилось:
- LEAD — клиент оставил контакт и хочет услугу
- CALLBACK — нужен перезвон
- INFO_ONLY — просто спросил информацию
- NOT_TARGET — не наш клиент
- FAILED — ошибка, таймаут
"""

from typing import Any, Optional
from dataclasses import dataclass

from .models import (
    ScenarioConfig,
    CallContext,
    OutcomeConfig,
    OutcomeRule,
)


@dataclass
class ClassificationResult:
    """Результат классификации."""
    outcome_id: str                         # ID outcome
    outcome_name: str                       # Название
    confidence: float = 1.0                 # Уверенность
    evidence: dict[str, Any] = None         # Доказательства (собранные поля)
    matched_rules: list[str] = None         # Какие правила сработали
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = {}
        if self.matched_rules is None:
            self.matched_rules = []


class OutcomeClassifier:
    """
    Классификатор результатов звонка.
    
    Работает по правилам из конфига — детерминистично, без LLM.
    
    Использование:
        classifier = OutcomeClassifier(config)
        result = classifier.classify(context)
        
        print(f"Результат: {result.outcome_id}")
        print(f"Данные: {result.evidence}")
    """
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
        self._outcomes = {o.id: o for o in config.outcomes}
        self._default_outcome = self._find_default_outcome()
    
    def _find_default_outcome(self) -> Optional[OutcomeConfig]:
        """Найти дефолтный outcome."""
        for outcome in self.config.outcomes:
            if outcome.is_default:
                return outcome
        return None
    
    def classify(self, context: CallContext) -> ClassificationResult:
        """
        Классифицировать результат звонка.
        
        Проверяет правила каждого outcome по порядку.
        Возвращает первый подходящий.
        """
        # Проверяем каждый outcome
        for outcome in self.config.outcomes:
            if outcome.is_default:
                continue  # Дефолтный проверяем в конце
            
            match_result = self._check_outcome(outcome, context)
            if match_result:
                return match_result
        
        # Если ничего не подошло — дефолтный
        if self._default_outcome:
            return ClassificationResult(
                outcome_id=self._default_outcome.id,
                outcome_name=self._default_outcome.name.ru,
                confidence=0.5,
                evidence=self._collect_evidence(self._default_outcome, context),
                matched_rules=["default"]
            )
        
        # Совсем fallback
        return ClassificationResult(
            outcome_id="unknown",
            outcome_name="Неизвестно",
            confidence=0.0,
            evidence={},
            matched_rules=[]
        )
    
    def _check_outcome(
        self, 
        outcome: OutcomeConfig, 
        context: CallContext
    ) -> Optional[ClassificationResult]:
        """Проверить подходит ли outcome."""
        
        if not outcome.rules:
            return None
        
        matched_rules = []
        
        # Все правила должны выполниться (AND)
        for rule in outcome.rules:
            if self._check_rule(rule, context):
                matched_rules.append(f"{rule.field}:{rule.condition}")
            else:
                return None  # Правило не выполнилось
        
        # Все правила выполнились
        return ClassificationResult(
            outcome_id=outcome.id,
            outcome_name=outcome.name.ru,
            confidence=1.0,
            evidence=self._collect_evidence(outcome, context),
            matched_rules=matched_rules
        )
    
    def _check_rule(self, rule: OutcomeRule, context: CallContext) -> bool:
        """Проверить одно правило."""
        field = rule.field
        condition = rule.condition
        expected_value = rule.value
        
        # Получаем значение поля
        actual_value = self._get_field_value(field, context)
        
        # Проверяем условие
        if condition == "is_set":
            return actual_value is not None and actual_value != ""
        
        elif condition == "is_not_set":
            return actual_value is None or actual_value == ""
        
        elif condition == "equals":
            return actual_value == expected_value
        
        elif condition == "not_equals":
            return actual_value != expected_value
        
        elif condition == "contains":
            if isinstance(actual_value, str):
                return str(expected_value).lower() in actual_value.lower()
            return False
        
        elif condition == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (TypeError, ValueError):
                return False
        
        elif condition == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (TypeError, ValueError):
                return False
        
        return False
    
    def _get_field_value(self, field: str, context: CallContext) -> Any:
        """Получить значение поля из контекста."""
        
        # Специальные поля
        if field == "callback_requested":
            return context.callback_requested
        
        if field == "not_target_reason":
            return context.not_target_reason
        
        if field == "escalation_triggered":
            return context.escalation_triggered
        
        if field == "support_questions_count":
            return context.support_questions_count
        
        if field == "turn_count":
            return context.turn_count
        
        # Обычные поля из collected_data
        return context.collected_data.get(field)
    
    def _collect_evidence(
        self, 
        outcome: OutcomeConfig, 
        context: CallContext
    ) -> dict[str, Any]:
        """Собрать доказательства для outcome."""
        evidence = {}
        
        # Собираем required_fields
        for field_id in outcome.required_fields:
            value = self._get_field_value(field_id, context)
            if value is not None:
                evidence[field_id] = value
        
        # Добавляем базовую информацию
        evidence["_turn_count"] = context.turn_count
        evidence["_language"] = context.language
        
        return evidence
    
    def get_outcome_config(self, outcome_id: str) -> Optional[OutcomeConfig]:
        """Получить конфигурацию outcome по ID."""
        return self._outcomes.get(outcome_id)
    
    def list_outcomes(self) -> list[str]:
        """Список всех outcome ID."""
        return list(self._outcomes.keys())
