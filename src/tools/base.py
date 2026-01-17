"""
Базовые классы для function calling tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ToolStatus(str, Enum):
    """Статус выполнения tool."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class ToolResult:
    """Результат выполнения tool."""
    status: ToolStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Проверить успешность выполнения."""
        return self.status == ToolStatus.SUCCESS


class Tool(ABC):
    """
    Базовый класс для всех tools.
    
    Каждый tool должен:
    - Иметь уникальное имя
    - Описывать свои параметры
    - Реализовать метод execute()
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация tool с конфигурацией.
        
        Args:
            config: Конфигурация из Skillbase.tools[].config
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя tool."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Описание что делает tool."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        JSON Schema параметров tool.
        
        Используется для function calling в LLM.
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Выполнить tool с заданными параметрами.
        
        Args:
            **kwargs: Параметры согласно self.parameters
            
        Returns:
            ToolResult с результатом выполнения
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Валидировать параметры перед выполнением.
        
        Args:
            params: Параметры для проверки
            
        Returns:
            True если параметры валидны
        """
        # Базовая валидация - проверяем обязательные поля
        required = self.parameters.get("required", [])
        for field in required:
            if field not in params:
                self.logger.error(f"Missing required parameter: {field}")
                return False
        return True
    
    def to_function_schema(self) -> Dict[str, Any]:
        """
        Конвертировать в OpenAI function calling schema.
        
        Returns:
            Schema для передачи в LLM
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ToolRegistry:
    """
    Реестр доступных tools.
    
    Управляет регистрацией и получением tools.
    """
    
    def __init__(self):
        """Инициализация пустого реестра."""
        self._tools: Dict[str, type[Tool]] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, tool_class: type[Tool]) -> None:
        """
        Зарегистрировать tool class.
        
        Args:
            tool_class: Класс tool для регистрации
        """
        # Создаём временный экземпляр чтобы получить имя
        temp_instance = tool_class({})
        name = temp_instance.name
        
        if name in self._tools:
            self.logger.warning(f"Tool '{name}' already registered, overwriting")
        
        self._tools[name] = tool_class
        self.logger.info(f"Registered tool: {name}")
    
    def get(self, name: str, config: Dict[str, Any]) -> Optional[Tool]:
        """
        Получить экземпляр tool по имени.
        
        Args:
            name: Имя tool
            config: Конфигурация для tool
            
        Returns:
            Экземпляр Tool или None если не найден
        """
        tool_class = self._tools.get(name)
        if not tool_class:
            self.logger.error(f"Tool '{name}' not found in registry")
            return None
        
        try:
            return tool_class(config)
        except Exception as e:
            self.logger.error(f"Failed to instantiate tool '{name}': {e}")
            return None
    
    def list_tools(self) -> List[str]:
        """
        Получить список зарегистрированных tools.
        
        Returns:
            Список имён tools
        """
        return list(self._tools.keys())
    
    def get_all_schemas(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Получить schemas всех tools для LLM.
        
        Args:
            configs: Список конфигураций tools из Skillbase
            
        Returns:
            Список function schemas для OpenAI
        """
        schemas = []
        
        for config in configs:
            name = config.get("name")
            if not name:
                continue
            
            tool = self.get(name, config.get("config", {}))
            if tool:
                schemas.append(tool.to_function_schema())
        
        return schemas


# Глобальный реестр
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Получить глобальный реестр tools."""
    return _global_registry


def register_tool(tool_class: type[Tool]) -> None:
    """
    Декоратор для регистрации tool.
    
    Usage:
        @register_tool
        class MyTool(Tool):
            ...
    """
    _global_registry.register(tool_class)
    return tool_class
