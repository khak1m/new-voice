"""
StateMachine — управление переходами между этапами диалога.

Гибкая архитектура: этапы и переходы задаются в конфиге клиентом.
"""

from typing import Optional
from .models import (
    ScenarioConfig,
    StateConfig,
    Transition,
    TransitionCondition,
    CallContext,
)
from .exceptions import StateTransitionError


class StateMachine:
    """
    Управляет переходами между этапами диалога.
    
    Этапы и переходы берутся из конфига — клиент сам их задаёт.
    
    Использование:
        sm = StateMachine(config)
        
        # Начать диалог
        start_state = sm.get_start_state()
        
        # Проверить возможные переходы
        transitions = sm.get_available_transitions("greeting", context)
        
        # Выполнить переход
        new_state = sm.transition("greeting", "booking", context)
    """
    
    def __init__(self, config: ScenarioConfig):
        self.config = config
        self._states_map = {state.id: state for state in config.states}
        self._transitions_by_from = self._build_transitions_index()
    
    def _build_transitions_index(self) -> dict[str, list[Transition]]:
        """Построить индекс переходов по исходному состоянию."""
        index: dict[str, list[Transition]] = {}
        for trans in self.config.transitions:
            if trans.from_state not in index:
                index[trans.from_state] = []
            index[trans.from_state].append(trans)
        
        # Сортируем по приоритету (выше = важнее)
        for state_id in index:
            index[state_id].sort(key=lambda t: t.priority, reverse=True)
        
        return index
    
    def get_state(self, state_id: str) -> Optional[StateConfig]:
        """Получить конфигурацию этапа по ID."""
        return self._states_map.get(state_id)
    
    def get_start_state(self) -> StateConfig:
        """Получить начальный этап."""
        for state in self.config.states:
            if state.is_start:
                return state
        raise StateTransitionError("none", "start", "No start state defined")
    
    def get_end_states(self) -> list[StateConfig]:
        """Получить все конечные этапы."""
        return [s for s in self.config.states if s.is_end]
    
    def is_end_state(self, state_id: str) -> bool:
        """Проверить, является ли этап конечным."""
        state = self.get_state(state_id)
        return state.is_end if state else False
    
    def get_available_transitions(
        self, 
        from_state_id: str, 
        context: CallContext
    ) -> list[Transition]:
        """
        Получить доступные переходы из текущего этапа.
        
        Возвращает переходы, условия которых выполнены.
        Отсортированы по приоритету.
        """
        all_transitions = self._transitions_by_from.get(from_state_id, [])
        available = []
        
        for trans in all_transitions:
            if self._check_condition(trans.condition, context):
                available.append(trans)
        
        return available
    
    def get_next_state(
        self, 
        from_state_id: str, 
        context: CallContext
    ) -> Optional[str]:
        """
        Определить следующий этап на основе контекста.
        
        Возвращает ID следующего этапа или None если переход невозможен.
        """
        transitions = self.get_available_transitions(from_state_id, context)
        if transitions:
            return transitions[0].to_state  # Берём с наивысшим приоритетом
        return None
    
    def can_transition(
        self, 
        from_state_id: str, 
        to_state_id: str, 
        context: CallContext
    ) -> bool:
        """Проверить, возможен ли переход."""
        transitions = self.get_available_transitions(from_state_id, context)
        return any(t.to_state == to_state_id for t in transitions)
    
    def transition(
        self, 
        from_state_id: str, 
        to_state_id: str, 
        context: CallContext
    ) -> StateConfig:
        """
        Выполнить переход между этапами.
        
        Raises:
            StateTransitionError: Если переход невозможен
        """
        if not self.can_transition(from_state_id, to_state_id, context):
            raise StateTransitionError(
                from_state_id, 
                to_state_id,
                "Transition not allowed or condition not met"
            )
        
        new_state = self.get_state(to_state_id)
        if not new_state:
            raise StateTransitionError(
                from_state_id,
                to_state_id,
                f"Target state '{to_state_id}' not found"
            )
        
        return new_state

    
    def _check_condition(
        self, 
        condition: TransitionCondition, 
        context: CallContext
    ) -> bool:
        """
        Проверить выполнение условия перехода.
        
        Типы условий:
        - field_collected: поле собрано
        - intent_detected: определён intent (проверяется внешне)
        - keyword: ключевое слово в последнем сообщении
        - custom: кастомное правило
        - always: всегда true
        """
        cond_type = condition.type
        
        if cond_type == "always":
            return True
        
        if cond_type == "field_collected":
            field_id = condition.field
            if field_id == "all_required":
                # Проверяем что все обязательные поля собраны
                return self._all_required_fields_collected(context)
            return field_id in context.collected_data
        
        if cond_type == "intent_detected":
            # Intent проверяется внешне и записывается в context
            # Здесь просто проверяем флаг
            detected_intent = context.collected_data.get("_detected_intent")
            return detected_intent == condition.intent
        
        if cond_type == "keyword":
            # Проверяем ключевые слова в последнем сообщении пользователя
            last_user_msg = self._get_last_user_message(context)
            if not last_user_msg:
                return False
            msg_lower = last_user_msg.lower()
            return any(kw.lower() in msg_lower for kw in condition.keywords)
        
        if cond_type == "custom":
            # Кастомные правила — пока не реализовано
            # TODO: добавить eval или простой expression parser
            return False
        
        return False
    
    def _all_required_fields_collected(self, context: CallContext) -> bool:
        """Проверить что все обязательные поля текущего этапа собраны."""
        current_state = self.get_state(context.current_state_id)
        if not current_state:
            return False
        
        for field in current_state.collect_fields:
            if field.required and field.id not in context.collected_data:
                return False
        
        return True
    
    def _get_last_user_message(self, context: CallContext) -> Optional[str]:
        """Получить последнее сообщение пользователя."""
        for msg in reversed(context.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def get_fields_to_collect(self, state_id: str) -> list:
        """Получить список полей для сбора на этапе."""
        state = self.get_state(state_id)
        if state:
            return state.collect_fields
        return []
    
    def get_missing_required_fields(
        self, 
        state_id: str, 
        context: CallContext
    ) -> list:
        """Получить список несобранных обязательных полей."""
        state = self.get_state(state_id)
        if not state:
            return []
        
        missing = []
        for field in state.collect_fields:
            if field.required and field.id not in context.collected_data:
                missing.append(field)
        
        return missing
