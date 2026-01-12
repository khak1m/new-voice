"""
ScenarioEngine — основной движок диалогов.

Связывает все компоненты:
- StateMachine — переходы между этапами
- ContextManager — контекст звонка
- FieldExtractor — извлечение данных
- OutcomeClassifier — классификация результата
- LanguageDetector — определение языка

LLM генерирует естественные ответы на основе контекста.
"""

from typing import Optional, Any, Protocol
from dataclasses import dataclass

from .models import (
    ScenarioConfig,
    CallContext,
    CallResult,
    TurnResult,
    Message,
    StateConfig,
    FieldToCollect,
    LanguagePolicy,
)
from .state_machine import StateMachine
from .context_manager import ContextManager
from .field_extractor import FieldExtractor
from .outcome_classifier import OutcomeClassifier
from .language_detector import LanguageDetector
from .exceptions import ScenarioEngineError


# =============================================================================
# Интерфейсы для внешних сервисов
# =============================================================================

class LLMProvider(Protocol):
    """Интерфейс для LLM провайдера."""
    
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 150
    ) -> str:
        """Сгенерировать ответ."""
        ...


class RAGProvider(Protocol):
    """Интерфейс для RAG провайдера."""
    
    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """Найти релевантные документы."""
        ...


# =============================================================================
# Простые заглушки для MVP (без внешних сервисов)
# =============================================================================

class SimpleLLMProvider:
    """
    Простой LLM провайдер для MVP.
    
    Генерирует ответы на основе шаблонов.
    В продакшене заменить на Groq/OpenAI.
    """
    
    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 150
    ) -> str:
        """Простая генерация — вернуть последний assistant hint."""
        # Ищем подсказку в system_prompt
        if "RESPOND:" in system_prompt:
            # Извлекаем подсказку после RESPOND:
            parts = system_prompt.split("RESPOND:")
            if len(parts) > 1:
                return parts[1].strip().split("\n")[0]
        
        return "Продолжим. Чем могу помочь?"


class SimpleRAGProvider:
    """Заглушка RAG для MVP."""
    
    def query(self, question: str, top_k: int = 3) -> list[dict]:
        return []


# =============================================================================
# Основной движок
# =============================================================================

class ScenarioEngine:
    """
    Основной движок управления диалогом.
    
    Использование:
        config = load_config("bot_config.yaml")
        engine = ScenarioEngine(config)
        
        # Опционально: подключить LLM и RAG
        engine.set_llm_provider(groq_provider)
        engine.set_rag_provider(qdrant_provider)
        
        # Начать звонок
        greeting = engine.start_call("call-123")
        
        # Обработать реплики
        response = engine.process_turn("Хочу записаться на маникюр")
        
        # Завершить
        result = engine.end_call()
    """
    
    def __init__(self, config: ScenarioConfig):
        """Инициализация движка с конфигурацией."""
        self.config = config
        
        # Компоненты
        self.state_machine = StateMachine(config)
        self.context_manager = ContextManager(config)
        self.field_extractor = FieldExtractor()
        self.outcome_classifier = OutcomeClassifier(config)
        
        # Language detector с политикой из конфига
        lang_policy = LanguagePolicy(
            default=config.language.default,
            detect=config.language.auto_detect,
            allow_switch=config.language.allow_switch
        )
        self.language_detector = LanguageDetector(lang_policy)
        
        # Внешние провайдеры (можно заменить)
        self._llm: LLMProvider = SimpleLLMProvider()
        self._rag: RAGProvider = SimpleRAGProvider()
        
        # Состояние
        self._call_active = False
    
    def set_llm_provider(self, provider: LLMProvider) -> None:
        """Установить LLM провайдер."""
        self._llm = provider
    
    def set_rag_provider(self, provider: RAGProvider) -> None:
        """Установить RAG провайдер."""
        self._rag = provider
    
    # =========================================================================
    # Основные методы
    # =========================================================================
    
    def start_call(self, call_id: str, direction: str = "inbound") -> str:
        """
        Начать новый звонок.
        
        Args:
            call_id: Уникальный ID звонка
            direction: "inbound" или "outbound"
            
        Returns:
            Приветственное сообщение
        """
        if self._call_active:
            raise ScenarioEngineError("Call already active. End current call first.")
        
        # Создать контекст
        self.context_manager.create(call_id, direction)
        self._call_active = True
        
        # Получить начальный этап
        start_state = self.state_machine.get_start_state()
        
        # Сгенерировать приветствие
        greeting = self._generate_greeting(start_state)
        
        # Записать в историю
        self.context_manager.add_message("assistant", greeting)
        
        return greeting
    
    def process_turn(self, user_input: str) -> TurnResult:
        """
        Обработать реплику пользователя.
        
        Args:
            user_input: Текст от пользователя (после STT)
            
        Returns:
            TurnResult с ответом бота
        """
        if not self._call_active:
            raise ScenarioEngineError("No active call. Call start_call() first.")
        
        context = self.context_manager.get_context()
        
        # Увеличить счётчик
        self.context_manager.increment_turn()
        
        # Записать сообщение пользователя
        self.context_manager.add_message("user", user_input)
        
        # Определить язык
        self._detect_and_switch_language(user_input)
        
        # Проверить лимиты
        if self.context_manager.is_max_turns_exceeded():
            return self._end_due_to_limit("max_turns")
        
        # Проверить guardrails
        guardrail_response = self._check_guardrails(user_input)
        if guardrail_response:
            return guardrail_response
        
        # Получить текущий этап
        current_state = self.state_machine.get_state(context.current_state_id)
        if not current_state:
            raise ScenarioEngineError(f"State not found: {context.current_state_id}")
        
        # Обработать в зависимости от этапа
        if current_state.use_knowledge_base:
            # Режим поддержки — ищем в RAG
            rag_response = self._handle_support_question(user_input, current_state)
            if rag_response:
                return rag_response
        
        # Попробовать извлечь данные
        collected = self._extract_fields(user_input, current_state)
        
        # Проверить переходы
        next_state_id = self.state_machine.get_next_state(
            context.current_state_id, 
            context
        )
        
        if next_state_id:
            # Переход на новый этап
            self.context_manager.set_state(next_state_id)
            next_state = self.state_machine.get_state(next_state_id)
            
            # Проверить конечный этап
            if next_state and next_state.is_end:
                return self._handle_end_state(next_state, collected)
        
        # Сгенерировать ответ
        response = self._generate_response(current_state, collected)
        
        # Записать ответ
        self.context_manager.add_message("assistant", response)
        
        return TurnResult(
            response=response,
            current_state_id=context.current_state_id,
            should_end=False,
            collected_in_turn=collected
        )
    
    def end_call(self, reason: str = "completed") -> CallResult:
        """
        Завершить звонок и получить результат.
        
        Args:
            reason: Причина завершения
            
        Returns:
            CallResult с outcome и собранными данными
        """
        if not self._call_active:
            raise ScenarioEngineError("No active call.")
        
        context = self.context_manager.get_context()
        
        # Классифицировать результат
        classification = self.outcome_classifier.classify(context)
        
        # Сформировать результат
        result = self.context_manager.to_result(
            outcome=classification.outcome_id,
            ended_reason=reason
        )
        
        # Добавить evidence
        result.outcome_data = classification.evidence
        
        self._call_active = False
        
        return result
    
    # =========================================================================
    # Вспомогательные методы
    # =========================================================================
    
    def _generate_greeting(self, state: StateConfig) -> str:
        """Сгенерировать приветствие."""
        context = self.context_manager.get_context()
        lang = context.language
        
        # Строим системный промпт
        system_prompt = self._build_system_prompt(state)
        system_prompt += f"\n\nRESPOND: Generate a greeting in {'Russian' if lang == 'ru' else 'English'}."
        system_prompt += f"\nBot name: {self.config.personality.name}"
        system_prompt += f"\nCompany: {self.config.personality.company}"
        system_prompt += f"\nRole: {self.config.personality.role}"
        
        # Генерируем через LLM
        response = self._llm.generate(
            system_prompt=system_prompt,
            messages=[],
            max_tokens=100
        )
        
        # Fallback если LLM не сработал
        if not response or response == "Продолжим. Чем могу помочь?":
            if lang == "ru":
                response = f"Здравствуйте! {self.config.personality.company}, {self.config.personality.name}. Чем могу помочь?"
            else:
                response = f"Hello! {self.config.personality.company}, {self.config.personality.name} speaking. How can I help you?"
        
        return response
    
    def _generate_response(
        self, 
        state: StateConfig, 
        collected: dict[str, Any]
    ) -> str:
        """Сгенерировать ответ на основе контекста."""
        context = self.context_manager.get_context()
        lang = context.language
        
        # Проверить нужно ли запросить поле
        missing_fields = self.state_machine.get_missing_required_fields(
            state.id, 
            context
        )
        
        # Строим промпт
        system_prompt = self._build_system_prompt(state)
        
        if missing_fields:
            field = missing_fields[0]
            system_prompt += f"\n\nRESPOND: Ask for {field.id} ({field.description})"
            system_prompt += f"\nField type: {field.type}"
            if field.examples:
                system_prompt += f"\nExamples: {', '.join(field.examples)}"
        elif collected:
            # Подтвердить собранные данные
            system_prompt += f"\n\nRESPOND: Confirm collected data: {collected}"
        else:
            system_prompt += f"\n\nRESPOND: Continue conversation naturally based on goal: {state.goal}"
        
        # История сообщений для LLM
        messages = self._format_messages_for_llm()
        
        response = self._llm.generate(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=150
        )
        
        # Fallback
        if not response or response == "Продолжим. Чем могу помочь?":
            if missing_fields:
                field = missing_fields[0]
                if lang == "ru":
                    response = f"Подскажите, пожалуйста, {field.description.lower()}?"
                else:
                    response = f"Could you please tell me your {field.description.lower()}?"
            else:
                response = "Хорошо, продолжим." if lang == "ru" else "Alright, let's continue."
        
        return response
    
    def _build_system_prompt(self, state: StateConfig) -> str:
        """Построить системный промпт для LLM."""
        personality = self.config.personality
        
        prompt = personality.base_system_prompt or ""
        prompt += f"\n\nYou are {personality.name}, {personality.role} at {personality.company}."
        prompt += f"\nTone: {personality.tone}"
        
        if personality.language_style:
            prompt += f"\nStyle: {personality.language_style}"
        
        prompt += f"\n\nCurrent stage: {state.name.ru}"
        prompt += f"\nGoal: {state.goal}"
        
        if state.system_prompt_addition:
            prompt += f"\n\n{state.system_prompt_addition}"
        
        return prompt
    
    def _format_messages_for_llm(self, limit: int = 10) -> list[dict]:
        """Форматировать историю для LLM."""
        messages = self.context_manager.get_messages(limit)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    
    def _extract_fields(
        self, 
        user_input: str, 
        state: StateConfig
    ) -> dict[str, Any]:
        """Извлечь данные из реплики пользователя."""
        collected = {}
        
        for field in state.collect_fields:
            # Пропускаем уже собранные
            if self.context_manager.has_field(field.id):
                continue
            
            # Пробуем извлечь
            result = self.field_extractor.extract_and_validate(user_input, field)
            
            if result.success:
                self.context_manager.set_field(field.id, result.value)
                collected[field.id] = result.value
                self.context_manager.reset_retry()
            elif field.required:
                # Не удалось извлечь обязательное поле
                self.context_manager.increment_retry()
        
        return collected
    
    def _detect_and_switch_language(self, user_input: str) -> None:
        """Определить язык и переключить если нужно."""
        context = self.context_manager.get_context()
        
        result = self.language_detector.detect(user_input, context.language)
        
        if result.should_switch:
            self.context_manager.set_language(result.language)
    
    def _check_guardrails(self, user_input: str) -> Optional[TurnResult]:
        """Проверить защитные правила."""
        import re
        
        user_lower = user_input.lower()
        context = self.context_manager.get_context()
        
        for rule in self.config.guardrails:
            # Проверяем паттерн
            if re.search(rule.pattern, user_lower, re.IGNORECASE):
                if rule.action == "escalate":
                    self.context_manager.trigger_escalation(rule.id)
                    response = rule.response_hint or "Переключаю на оператора."
                    self.context_manager.add_message("assistant", response)
                    return TurnResult(
                        response=response,
                        current_state_id=context.current_state_id,
                        should_end=True,
                        outcome="escalation"
                    )
                elif rule.action == "end_call":
                    response = rule.response_hint or "До свидания."
                    self.context_manager.add_message("assistant", response)
                    return TurnResult(
                        response=response,
                        current_state_id=context.current_state_id,
                        should_end=True,
                        outcome="guardrail_triggered"
                    )
                elif rule.action == "respond":
                    # Просто отвечаем и продолжаем
                    response = rule.response_hint
                    if response:
                        self.context_manager.add_message("assistant", response)
                        return TurnResult(
                            response=response,
                            current_state_id=context.current_state_id,
                            should_end=False
                        )
        
        return None
    
    def _handle_support_question(
        self, 
        user_input: str, 
        state: StateConfig
    ) -> Optional[TurnResult]:
        """Обработать вопрос через RAG."""
        context = self.context_manager.get_context()
        
        # Увеличить счётчик вопросов
        self.context_manager.increment_support_questions()
        
        # Запрос к RAG
        results = self._rag.query(user_input, top_k=3)
        
        if results:
            # Нашли ответ
            best_result = results[0]
            score = best_result.get("score", 0)
            
            if score >= self.config.rag_min_score:
                answer = best_result.get("content", "")
                response = f"{answer}"
                self.context_manager.add_message("assistant", response)
                return TurnResult(
                    response=response,
                    current_state_id=context.current_state_id,
                    should_end=False
                )
        
        # Не нашли — fallback
        lang = context.language
        if lang == "ru":
            response = "К сожалению, у меня нет информации по этому вопросу. Могу соединить с оператором?"
        else:
            response = "I'm sorry, I don't have information about that. Would you like me to connect you with an operator?"
        
        self.context_manager.add_message("assistant", response)
        return TurnResult(
            response=response,
            current_state_id=context.current_state_id,
            should_end=False
        )
    
    def _handle_end_state(
        self, 
        state: StateConfig, 
        collected: dict[str, Any]
    ) -> TurnResult:
        """Обработать конечный этап."""
        context = self.context_manager.get_context()
        lang = context.language
        
        # Классифицировать результат
        classification = self.outcome_classifier.classify(context)
        
        # Сгенерировать прощание
        if lang == "ru":
            response = "Спасибо за звонок! До свидания."
        else:
            response = "Thank you for calling! Goodbye."
        
        self.context_manager.add_message("assistant", response)
        
        return TurnResult(
            response=response,
            current_state_id=state.id,
            should_end=True,
            outcome=classification.outcome_id,
            collected_in_turn=collected
        )
    
    def _end_due_to_limit(self, limit_type: str) -> TurnResult:
        """Завершить из-за превышения лимита."""
        context = self.context_manager.get_context()
        lang = context.language
        
        if lang == "ru":
            response = "К сожалению, наше время истекло. Перезвоните позже или оставьте контакт для обратного звонка."
        else:
            response = "Unfortunately, we've run out of time. Please call back later or leave your contact for a callback."
        
        self.context_manager.add_message("assistant", response)
        
        return TurnResult(
            response=response,
            current_state_id=context.current_state_id,
            should_end=True,
            outcome="timeout"
        )
    
    # =========================================================================
    # Дополнительные методы
    # =========================================================================
    
    def get_context(self) -> CallContext:
        """Получить текущий контекст звонка."""
        return self.context_manager.get_context()
    
    def get_collected_data(self) -> dict[str, Any]:
        """Получить собранные данные."""
        return self.context_manager.get_all_fields()
    
    def is_call_active(self) -> bool:
        """Проверить активен ли звонок."""
        return self._call_active
    
    def force_transition(self, to_state_id: str) -> None:
        """Принудительно перейти на этап (для тестирования)."""
        self.context_manager.set_state(to_state_id)
