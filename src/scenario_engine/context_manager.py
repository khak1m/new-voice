"""
ContextManager — управление контекстом звонка.

Хранит всё что происходит во время звонка:
- Текущий этап
- Собранные данные
- История сообщений
- Счётчики и флаги
"""

from datetime import datetime
from typing import Any, Optional
import time

from .models import (
    CallContext,
    CallResult,
    Message,
    ScenarioConfig,
)


class ContextManager:
    """
    Управляет контекстом звонка.
    
    Использование:
        cm = ContextManager(config)
        
        # Создать контекст для нового звонка
        context = cm.create("call-123", direction="inbound")
        
        # Обновить данные
        cm.set_field("client_name", "Анна")
        cm.add_message("user", "Хочу записаться")
        cm.set_state("booking")
        
        # Получить результат
        result = cm.to_result(outcome="booking_complete")
    """
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
        self.context: Optional[CallContext] = None
    
    def create(
        self, 
        call_id: str, 
        direction: str = "inbound",
        start_state_id: Optional[str] = None
    ) -> CallContext:
        """
        Создать новый контекст звонка.
        
        Args:
            call_id: Уникальный ID звонка
            direction: "inbound" или "outbound"
            start_state_id: ID начального этапа (если не указан — берётся из конфига)
        """
        # Найти начальный этап
        if not start_state_id:
            for state in self.config.states:
                if state.is_start:
                    start_state_id = state.id
                    break
        
        self.context = CallContext(
            call_id=call_id,
            bot_id=self.config.bot_id,
            direction=direction,
            current_state_id=start_state_id,
            language=self.config.language.default,
            started_at=datetime.now(),
        )
        
        return self.context
    
    def get_context(self) -> CallContext:
        """Получить текущий контекст."""
        if not self.context:
            raise RuntimeError("Context not created. Call create() first.")
        return self.context
    
    # =========================================================================
    # Управление состоянием
    # =========================================================================
    
    def set_state(self, state_id: str) -> None:
        """Установить текущий этап."""
        ctx = self.get_context()
        ctx.previous_state_id = ctx.current_state_id
        ctx.current_state_id = state_id
        ctx.state_turn_count = 0  # Сбросить счётчик реплик на этапе
    
    def get_current_state_id(self) -> Optional[str]:
        """Получить ID текущего этапа."""
        return self.get_context().current_state_id
    
    # =========================================================================
    # Управление данными
    # =========================================================================
    
    def set_field(self, field_id: str, value: Any) -> None:
        """Установить значение поля."""
        self.get_context().collected_data[field_id] = value
    
    def get_field(self, field_id: str, default: Any = None) -> Any:
        """Получить значение поля."""
        return self.get_context().collected_data.get(field_id, default)
    
    def has_field(self, field_id: str) -> bool:
        """Проверить, собрано ли поле."""
        return field_id in self.get_context().collected_data
    
    def get_all_fields(self) -> dict[str, Any]:
        """Получить все собранные данные."""
        return self.get_context().collected_data.copy()
    
    # =========================================================================
    # История сообщений
    # =========================================================================
    
    def add_message(
        self, 
        role: str, 
        content: str,
        state_id: Optional[str] = None
    ) -> None:
        """
        Добавить сообщение в историю.
        
        Args:
            role: "user", "assistant", "system"
            content: Текст сообщения
            state_id: ID этапа (если не указан — текущий)
        """
        ctx = self.get_context()
        
        msg = Message(
            role=role,
            content=content,
            timestamp=time.time(),
            state_id=state_id or ctx.current_state_id,
        )
        ctx.messages.append(msg)
        
        # Обновить last_bot_message если это ответ бота
        if role == "assistant":
            ctx.last_bot_message = content
    
    def get_messages(self, limit: Optional[int] = None) -> list[Message]:
        """Получить историю сообщений."""
        messages = self.get_context().messages
        if limit:
            return messages[-limit:]
        return messages
    
    def get_last_user_message(self) -> Optional[str]:
        """Получить последнее сообщение пользователя."""
        for msg in reversed(self.get_context().messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def get_last_bot_message(self) -> Optional[str]:
        """Получить последнее сообщение бота."""
        return self.get_context().last_bot_message

    
    # =========================================================================
    # Счётчики
    # =========================================================================
    
    def increment_turn(self) -> int:
        """Увеличить счётчик реплик."""
        ctx = self.get_context()
        ctx.turn_count += 1
        ctx.state_turn_count += 1
        return ctx.turn_count
    
    def increment_retry(self) -> int:
        """Увеличить счётчик повторов."""
        ctx = self.get_context()
        ctx.retry_count += 1
        return ctx.retry_count
    
    def reset_retry(self) -> None:
        """Сбросить счётчик повторов."""
        self.get_context().retry_count = 0
    
    def increment_support_questions(self) -> int:
        """Увеличить счётчик вопросов поддержки."""
        ctx = self.get_context()
        ctx.support_questions_count += 1
        return ctx.support_questions_count
    
    # =========================================================================
    # Флаги
    # =========================================================================
    
    def request_callback(self, reason: str = "") -> None:
        """Отметить что нужен перезвон."""
        ctx = self.get_context()
        ctx.callback_requested = True
        if reason:
            ctx.collected_data["callback_reason"] = reason
    
    def mark_not_target(self, reason: str) -> None:
        """Отметить как нецелевой звонок."""
        ctx = self.get_context()
        ctx.not_target_reason = reason
    
    def trigger_escalation(self, reason: str = "") -> None:
        """Отметить эскалацию."""
        ctx = self.get_context()
        ctx.escalation_triggered = True
        if reason:
            ctx.collected_data["escalation_reason"] = reason
    
    def set_language(self, lang: str) -> None:
        """Установить язык."""
        self.get_context().language = lang
    
    def set_detected_intent(self, intent: str) -> None:
        """Установить определённый intent (для проверки переходов)."""
        self.get_context().collected_data["_detected_intent"] = intent
    
    # =========================================================================
    # Проверки лимитов
    # =========================================================================
    
    def is_max_turns_exceeded(self) -> bool:
        """Проверить превышение лимита реплик."""
        return self.get_context().turn_count >= self.config.limits.max_turns
    
    def is_max_retries_exceeded(self) -> bool:
        """Проверить превышение лимита повторов."""
        return self.get_context().retry_count >= self.config.limits.max_turn_retries
    
    def get_call_duration_sec(self) -> int:
        """Получить длительность звонка в секундах."""
        ctx = self.get_context()
        delta = datetime.now() - ctx.started_at
        return int(delta.total_seconds())
    
    # =========================================================================
    # Результат
    # =========================================================================
    
    def to_result(
        self, 
        outcome: str,
        ended_reason: str = "completed"
    ) -> CallResult:
        """
        Сформировать результат звонка.
        
        Args:
            outcome: ID outcome (из конфига)
            ended_reason: Причина завершения
        """
        ctx = self.get_context()
        
        # Собрать evidence для outcome
        outcome_data = {}
        for outcome_cfg in self.config.outcomes:
            if outcome_cfg.id == outcome:
                for field_id in outcome_cfg.required_fields:
                    if field_id in ctx.collected_data:
                        outcome_data[field_id] = ctx.collected_data[field_id]
                break
        
        # Собрать список посещённых этапов
        states_visited = []
        for msg in ctx.messages:
            if msg.state_id and msg.state_id not in states_visited:
                states_visited.append(msg.state_id)
        
        return CallResult(
            call_id=ctx.call_id,
            bot_id=ctx.bot_id,
            direction=ctx.direction,
            outcome=outcome,
            outcome_data=outcome_data,
            collected_data=ctx.collected_data.copy(),
            messages=ctx.messages.copy(),
            duration_sec=self.get_call_duration_sec(),
            turn_count=ctx.turn_count,
            states_visited=states_visited,
            language=ctx.language,
            ended_reason=ended_reason,
        )
