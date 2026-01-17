"""
SystemPromptBuilder - конвертирует Skillbase config в промпт для VoiceAgent.

Этот модуль отвечает за генерацию system prompt из JSONB конфигурации Skillbase.
Промпт определяет поведение голосового ассистента во время звонка.
"""

import os
from pathlib import Path
from typing import List, Optional
from schemas.skillbase_schemas import SkillbaseConfig

# Путь к базовому промпту (общие правила для всех ботов)
BASE_PROMPT_PATH = Path(__file__).parent.parent.parent / "config" / "base_prompt.txt"


class SystemPromptBuilder:
    """
    Строит system prompt для VoiceAgent из Skillbase конфигурации.
    
    Промпт включает:
    - Роль и стиль общения (из context)
    - Правила безопасности (из context.safety_rules)
    - Факты о компании (из context.facts)
    - Инструкции по сбору данных (из flow)
    - Настройки агента (из agent)
    """
    
    @staticmethod
    def build(config: SkillbaseConfig, company_name: str = "Компания") -> str:
        """
        Построить system prompt из Skillbase конфигурации.
        
        Args:
            config: Валидированная конфигурация Skillbase
            company_name: Название компании (для промпта)
            
        Returns:
            Полный system prompt для агента
        """
        builder = SystemPromptBuilder()
        
        sections = [
            builder._build_base_instructions(),
            builder._build_role_section(config, company_name),
            builder._build_context_section(config),
            builder._build_flow_section(config),
            builder._build_safety_section(config),
            builder._build_language_section(),
        ]
        
        return "\n".join(sections)
    
    def _build_base_instructions(self) -> str:
        """
        Базовые инструкции для всех ботов.
        
        Загружает из файла config/base_prompt.txt.
        Можно переопределить через переменную окружения BASE_PROMPT_PATH.
        """
        # Проверяем переменную окружения (для кастомизации)
        custom_path = os.getenv("BASE_PROMPT_PATH")
        prompt_path = Path(custom_path) if custom_path else BASE_PROMPT_PATH
        
        # Читаем базовый промпт из файла
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Fallback на дефолтный промпт если файл не найден
            return """# КТО ТЫ
Ты — голосовой ассистент, который отвечает на звонки.
Говори как живой человек, а не как робот.

# КАК ГОВОРИТЬ
- Короткие фразы, 1-2 предложения
- Разговорные слова: "ага", "понял", "хорошо", "отлично"
- Паузы: "секундочку...", "так-так..."
- Переспрашивай если нужно: "правильно понял, что...?"

# ЧЕГО НЕ ДЕЛАТЬ
- Длинные сложные предложения
- Канцелярит: "в рамках", "осуществить"
- Повторять одно и то же
- Говорить "как я могу вам помочь"
- Извиняться слишком часто
"""
    
    def _build_role_section(self, config: SkillbaseConfig, company_name: str) -> str:
        """Секция с ролью и компанией."""
        role = config.context.role
        style = config.context.style
        
        section = f"""# ТВОЯ РОЛЬ
Ты работаешь в компании "{company_name}".
Твоя роль: {role}
Стиль общения: {style}
"""
        return section
    
    def _build_context_section(self, config: SkillbaseConfig) -> str:
        """Секция с фактами о компании."""
        if not config.context.facts:
            return ""
        
        section = "# О КОМПАНИИ\n"
        for fact in config.context.facts:
            section += f"- {fact}\n"
        section += "\n"
        
        return section
    
    def _build_flow_section(self, config: SkillbaseConfig) -> str:
        """Секция с инструкциями по сбору данных."""
        if config.flow.type == "linear":
            return self._build_linear_flow(config)
        elif config.flow.type == "graph":
            return self._build_graph_flow(config)
        else:
            return ""
    
    def _build_linear_flow(self, config: SkillbaseConfig) -> str:
        """Линейный flow - последовательный сбор данных."""
        if not config.flow.states:
            return ""
        
        section = """# ТВОЯ ЗАДАЧА
Веди разговор последовательно, переходя от одного этапа к другому.

# ЭТАПЫ РАЗГОВОРА
"""
        for i, state in enumerate(config.flow.states, 1):
            # Поддержка и строк, и StateConfig объектов
            if isinstance(state, str):
                section += f"{i}. {state}\n"
            else:
                section += f"{i}. {state.name}\n"
        
        section += "\nПереходи к следующему этапу только когда текущий завершён.\n\n"
        
        return section
    
    def _build_graph_flow(self, config: SkillbaseConfig) -> str:
        """Graph flow - условные переходы между состояниями."""
        if not config.flow.states:
            return ""
        
        section = """# ТВОЯ ЗАДАЧА
Веди разговор, переходя между состояниями в зависимости от ответов клиента.

# СОСТОЯНИЯ
"""
        for state in config.flow.states:
            # Поддержка и строк, и StateConfig объектов
            if isinstance(state, str):
                section += f"- {state}\n"
            else:
                section += f"- {state.name}\n"
        
        if config.flow.transitions:
            section += "\n# ПЕРЕХОДЫ\n"
            for transition in config.flow.transitions:
                from_state = transition.from_state
                to_state = transition.to_state
                condition = transition.condition or "всегда"
                section += f"- {from_state} → {to_state} (если {condition})\n"
        
        section += "\n"
        
        return section
    
    def _build_safety_section(self, config: SkillbaseConfig) -> str:
        """Секция с правилами безопасности."""
        if not config.context.safety_rules:
            return ""
        
        section = "# ПРАВИЛА БЕЗОПАСНОСТИ\n"
        for rule in config.context.safety_rules:
            section += f"- {rule}\n"
        section += "\n"
        
        return section
    
    def _build_language_section(self) -> str:
        """Секция с языковыми настройками."""
        return """# ЯЗЫК
- Говори на русском языке
- Используй "вы" по умолчанию
"""


def build_prompt_from_skillbase(config: SkillbaseConfig, company_name: str = "Компания") -> str:
    """
    Удобная функция для построения промпта.
    
    Args:
        config: Валидированная конфигурация Skillbase
        company_name: Название компании
        
    Returns:
        System prompt для агента
        
    Example:
        >>> from schemas.skillbase_schemas import SkillbaseConfig
        >>> config = SkillbaseConfig(**skillbase.config)
        >>> prompt = build_prompt_from_skillbase(config, "Салон красоты")
    """
    return SystemPromptBuilder.build(config, company_name)
