"""
Адаптер для конвертации Skillbase config → ScenarioEngine config.

Skillbase использует упрощенную схему (ContextConfig, FlowConfig, etc.)
ScenarioEngine использует полную схему (StateConfig, Transition, etc.)

Этот адаптер делает мост между ними.
"""

from typing import List, Dict, Any, Tuple
from schemas.skillbase_schemas import SkillbaseConfig, FlowType, ToolConfig as SkillbaseToolConfig
from scenario_engine.models import (
    ScenarioConfig,
    BotPersonality,
    LanguageConfig,
    StateConfig,
    LocalizedText,
    Transition,
    TransitionCondition,
    OutcomeConfig,
    GuardrailRule,
    LimitsConfig,
    FieldToCollect,
    FieldType,
)
from tools.base import get_registry, Tool


class SkillbaseToScenarioAdapter:
    """
    Конвертирует Skillbase конфигурацию в ScenarioEngine конфигурацию.
    
    Usage:
        skillbase_config = SkillbaseConfig(**skillbase.config)
        adapter = SkillbaseToScenarioAdapter()
        scenario_config = adapter.convert(skillbase_config, skillbase.id)
    """
    
    @staticmethod
    def convert(
        skillbase: SkillbaseConfig,
        skillbase_id: str,
        company_name: str = "Компания"
    ) -> Tuple[ScenarioConfig, List[Tool]]:
        """
        Конвертировать Skillbase config в ScenarioEngine config + Tools.
        
        Args:
            skillbase: Skillbase конфигурация
            skillbase_id: UUID Skillbase
            company_name: Название компании
            
        Returns:
            Tuple (ScenarioConfig, List[Tool]) для ScenarioEngine
        """
        adapter = SkillbaseToScenarioAdapter()
        
        # Конвертируем личность бота
        personality = adapter._convert_personality(skillbase, company_name)
        
        # Конвертируем языковые настройки
        language = adapter._convert_language(skillbase)
        
        # Конвертируем flow в states и transitions
        states, transitions = adapter._convert_flow(skillbase)
        
        # Конвертируем outcomes (пока дефолтные)
        outcomes = adapter._convert_outcomes(skillbase)
        
        # Конвертируем guardrails
        guardrails = adapter._convert_guardrails(skillbase)
        
        # Конвертируем tools
        tools = adapter._convert_tools(skillbase)
        
        # Лимиты (дефолтные)
        limits = LimitsConfig()
        
        scenario_config = ScenarioConfig(
            version="2.0",
            bot_id=skillbase_id,
            personality=personality,
            language=language,
            states=states,
            transitions=transitions,
            outcomes=outcomes,
            guardrails=guardrails,
            limits=limits,
            knowledge_base_id=None,  # TODO: добавить когда будет интеграция с KB
            rag_min_score=0.7
        )
        
        return scenario_config, tools
    
    def _convert_personality(
        self,
        skillbase: SkillbaseConfig,
        company_name: str
    ) -> BotPersonality:
        """Конвертировать context в BotPersonality."""
        context = skillbase.context
        
        # Базовый промпт будет загружен из config/base_prompt.txt
        # Здесь добавляем только специфику клиента
        base_prompt = f"""Ты работаешь в компании "{company_name}".
Твоя роль: {context.role}
Стиль общения: {context.style}
"""
        
        if context.facts:
            base_prompt += "\nФакты о компании:\n"
            for fact in context.facts:
                base_prompt += f"- {fact}\n"
        
        return BotPersonality(
            name="Ассистент",  # TODO: добавить в Skillbase.config
            role=context.role,
            company=company_name,
            tone=context.style.lower(),
            language_style=context.style,
            base_system_prompt=base_prompt
        )
    
    def _convert_language(self, skillbase: SkillbaseConfig) -> LanguageConfig:
        """Конвертировать voice settings в LanguageConfig."""
        # Определяем язык из STT настроек
        stt_lang = skillbase.voice.stt_language or "ru"
        
        return LanguageConfig(
            default=stt_lang,
            supported=[stt_lang, "en"] if stt_lang != "en" else ["en", "ru"],
            auto_detect=True,
            allow_switch=True
        )
    
    def _convert_flow(
        self,
        skillbase: SkillbaseConfig
    ) -> tuple[List[StateConfig], List[Transition]]:
        """
        Конвертировать FlowConfig в states и transitions.
        
        Поддерживает:
        - linear: последовательные этапы
        - graph: этапы с условными переходами
        """
        flow = skillbase.flow
        
        if flow.type == FlowType.LINEAR:
            return self._convert_linear_flow(flow)
        elif flow.type == FlowType.GRAPH:
            return self._convert_graph_flow(flow)
        else:
            # Fallback: один этап
            return self._create_default_flow()
    
    def _convert_linear_flow(
        self,
        flow
    ) -> tuple[List[StateConfig], List[Transition]]:
        """Конвертировать линейный flow."""
        states = []
        transitions = []
        
        if not flow.states:
            return self._create_default_flow()
        
        for i, state in enumerate(flow.states):
            # Поддержка и строк, и StateConfig объектов
            if isinstance(state, str):
                state_name = state
                state_goal = f"Выполнить этап: {state}"
            else:
                state_name = state.name
                state_goal = state.prompt or f"Выполнить этап: {state.name}"
            
            state_id = f"state_{i+1}"
            
            # Создаём StateConfig
            state_config = StateConfig(
                id=state_id,
                name=LocalizedText(ru=state_name, en=state_name),
                goal=state_goal,
                collect_fields=[],  # TODO: добавить когда будет field extraction
                system_prompt_addition="",
                examples=[],
                use_knowledge_base=False,
                max_turns=None,
                is_start=(i == 0),
                is_end=(i == len(flow.states) - 1)
            )
            
            states.append(state_config)
            
            # Создаём переход к следующему этапу
            if i < len(flow.states) - 1:
                transition = Transition(
                    from_state=state_id,
                    to_state=f"state_{i+2}",
                    condition=TransitionCondition(
                        type="custom",
                        custom_rule="always"  # Всегда переходим к следующему
                    ),
                    priority=0,
                    description=f"Переход от '{state_name}' к следующему этапу"
                )
                transitions.append(transition)
        
        return states, transitions
    
    def _convert_graph_flow(
        self,
        flow
    ) -> tuple[List[StateConfig], List[Transition]]:
        """Конвертировать graph flow с условными переходами."""
        states = []
        transitions = []
        
        if not flow.states:
            return self._create_default_flow()
        
        # Создаём states
        for i, state in enumerate(flow.states):
            if isinstance(state, str):
                state_name = state
                state_goal = f"Выполнить этап: {state}"
                state_id = f"state_{i+1}"
            else:
                state_name = state.name
                state_goal = state.prompt or f"Выполнить этап: {state.name}"
                state_id = state.name.lower().replace(" ", "_")
            
            state_config = StateConfig(
                id=state_id,
                name=LocalizedText(ru=state_name, en=state_name),
                goal=state_goal,
                collect_fields=[],
                system_prompt_addition="",
                examples=[],
                use_knowledge_base=False,
                max_turns=None,
                is_start=(i == 0),
                is_end=False  # В graph flow конечный этап определяется переходами
            )
            
            states.append(state_config)
        
        # Создаём transitions из flow.transitions
        if flow.transitions:
            for trans in flow.transitions:
                transition = Transition(
                    from_state=trans.from_state.lower().replace(" ", "_"),
                    to_state=trans.to_state.lower().replace(" ", "_"),
                    condition=TransitionCondition(
                        type="keyword" if trans.condition else "custom",
                        keywords=[trans.condition] if trans.condition else [],
                        custom_rule=trans.condition or "always"
                    ),
                    priority=0,
                    description=f"Переход: {trans.from_state} → {trans.to_state}"
                )
                transitions.append(transition)
        
        # Если нет transitions, создаём линейные переходы
        if not transitions and len(states) > 1:
            for i in range(len(states) - 1):
                transition = Transition(
                    from_state=states[i].id,
                    to_state=states[i+1].id,
                    condition=TransitionCondition(
                        type="custom",
                        custom_rule="always"
                    ),
                    priority=0,
                    description=f"Переход от '{states[i].name.ru}' к '{states[i+1].name.ru}'"
                )
                transitions.append(transition)
        
        # Помечаем последний state как конечный
        if states:
            states[-1].is_end = True
        
        return states, transitions
    
    def _create_default_flow(self) -> tuple[List[StateConfig], List[Transition]]:
        """Создать дефолтный flow если не задан."""
        state = StateConfig(
            id="default",
            name=LocalizedText(ru="Общение", en="Conversation"),
            goal="Вести естественный диалог с клиентом",
            collect_fields=[],
            system_prompt_addition="",
            examples=[],
            use_knowledge_base=False,
            max_turns=None,
            is_start=True,
            is_end=True
        )
        
        return [state], []
    
    def _convert_outcomes(self, skillbase: SkillbaseConfig) -> List[OutcomeConfig]:
        """Конвертировать outcomes (пока дефолтные)."""
        # TODO: добавить кастомные outcomes в Skillbase.config
        return [
            OutcomeConfig(
                id="lead",
                name=LocalizedText(ru="Лид", en="Lead"),
                rules=[],
                required_fields=[],
                is_default=False
            ),
            OutcomeConfig(
                id="info_only",
                name=LocalizedText(ru="Только информация", en="Info only"),
                rules=[],
                required_fields=[],
                is_default=True
            ),
            OutcomeConfig(
                id="not_target",
                name=LocalizedText(ru="Не целевой", en="Not target"),
                rules=[],
                required_fields=[],
                is_default=False
            )
        ]
    
    def _convert_guardrails(self, skillbase: SkillbaseConfig) -> List[GuardrailRule]:
        """Конвертировать safety_rules в guardrails."""
        guardrails = []
        
        if skillbase.context.safety_rules:
            for i, rule in enumerate(skillbase.context.safety_rules):
                # Простая эвристика: если правило содержит "не", то это banned topic
                if "не" in rule.lower() or "нельзя" in rule.lower():
                    guardrail = GuardrailRule(
                        id=f"safety_{i+1}",
                        type="banned_topic",
                        pattern=rule.lower(),  # TODO: улучшить pattern matching
                        action="respond",
                        response_hint="Извините, я не могу обсуждать эту тему."
                    )
                    guardrails.append(guardrail)
        
        return guardrails
    
    def _convert_tools(self, skillbase: SkillbaseConfig) -> List[Tool]:
        """Конвертировать tools из Skillbase в Tool instances."""
        tools = []
        registry = get_registry()
        
        for tool_config in skillbase.tools:
            if not tool_config.enabled:
                continue
            
            # Получаем tool из реестра
            tool = registry.get(tool_config.name, tool_config.config)
            
            if tool:
                tools.append(tool)
            else:
                # Логируем warning если tool не найден
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Tool '{tool_config.name}' not found in registry")
        
        return tools


def convert_skillbase_to_scenario(
    skillbase: SkillbaseConfig,
    skillbase_id: str,
    company_name: str = "Компания"
) -> Tuple[ScenarioConfig, List[Tool]]:
    """
    Удобная функция для конвертации.
    
    Args:
        skillbase: Skillbase конфигурация
        skillbase_id: UUID Skillbase
        company_name: Название компании
        
    Returns:
        Tuple (ScenarioConfig, List[Tool]) для ScenarioEngine
        
    Example:
        >>> from schemas.skillbase_schemas import SkillbaseConfig
        >>> config = SkillbaseConfig(**skillbase.config)
        >>> scenario, tools = convert_skillbase_to_scenario(config, str(skillbase.id), "Салон")
    """
    return SkillbaseToScenarioAdapter.convert(skillbase, skillbase_id, company_name)
