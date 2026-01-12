"""
Исключения для Scenario Engine.
"""


class ScenarioEngineError(Exception):
    """Базовое исключение для всех ошибок Scenario Engine."""
    pass


class ConfigValidationError(ScenarioEngineError):
    """Ошибка валидации конфигурации."""
    
    def __init__(self, errors: list[dict]):
        self.errors = errors
        message = f"Config validation failed with {len(errors)} error(s)"
        super().__init__(message)
    
    def __str__(self):
        lines = ["Config validation failed:"]
        for err in self.errors:
            field = err.get("field", "unknown")
            reason = err.get("reason", "unknown error")
            lines.append(f"  - {field}: {reason}")
        return "\n".join(lines)


class StateTransitionError(ScenarioEngineError):
    """Недопустимый переход между состояниями."""
    
    def __init__(self, from_state: str, to_state: str, trigger: str = None):
        self.from_state = from_state
        self.to_state = to_state
        self.trigger = trigger
        message = f"Invalid transition from {from_state} to {to_state}"
        if trigger:
            message += f" (trigger: {trigger})"
        super().__init__(message)


class FieldExtractionError(ScenarioEngineError):
    """Ошибка извлечения данных из речи пользователя."""
    
    def __init__(self, field_id: str, reason: str):
        self.field_id = field_id
        self.reason = reason
        super().__init__(f"Failed to extract field '{field_id}': {reason}")


class MaxRetriesExceededError(ScenarioEngineError):
    """Превышено максимальное количество попыток."""
    
    def __init__(self, field_id: str, max_retries: int):
        self.field_id = field_id
        self.max_retries = max_retries
        super().__init__(f"Max retries ({max_retries}) exceeded for field '{field_id}'")
