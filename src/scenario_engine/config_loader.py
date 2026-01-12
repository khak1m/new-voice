"""
ConfigLoader — загрузка и валидация конфигурации бота.

Поддерживает YAML и JSON форматы.
Валидирует схему и связи между элементами.
"""

import json
from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError

from .models import ScenarioConfig
from .exceptions import ConfigValidationError


class ConfigLoader:
    """
    Загрузчик конфигурации сценария.
    
    Использование:
        loader = ConfigLoader()
        config = loader.load("bot_config.yaml")
        
        # Или из словаря
        config = loader.load_dict(config_dict)
        
        # Валидация без загрузки
        errors = loader.validate_file("bot_config.yaml")
    """
    
    def __init__(self):
        self.errors: list[dict] = []
    
    def load(self, path: Union[str, Path]) -> ScenarioConfig:
        """
        Загрузить конфигурацию из файла.
        
        Args:
            path: Путь к YAML или JSON файлу
            
        Returns:
            ScenarioConfig
            
        Raises:
            ConfigValidationError: Если конфиг невалидный
            FileNotFoundError: Если файл не найден
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        # Читаем файл
        content = path.read_text(encoding="utf-8")
        
        # Парсим в зависимости от расширения
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ConfigValidationError([{
                "field": "file",
                "reason": f"Unsupported file format: {path.suffix}. Use .yaml, .yml or .json"
            }])
        
        return self.load_dict(data)
    
    def load_dict(self, data: dict) -> ScenarioConfig:
        """
        Загрузить конфигурацию из словаря.
        
        Args:
            data: Словарь с конфигурацией
            
        Returns:
            ScenarioConfig
            
        Raises:
            ConfigValidationError: Если конфиг невалидный
        """
        self.errors = []
        
        # Валидация через Pydantic
        try:
            config = ScenarioConfig(**data)
        except ValidationError as e:
            self.errors = self._parse_pydantic_errors(e)
            raise ConfigValidationError(self.errors)
        
        # Дополнительная валидация связей
        self._validate_references(config)
        
        if self.errors:
            raise ConfigValidationError(self.errors)
        
        return config
    
    def validate_file(self, path: Union[str, Path]) -> list[dict]:
        """
        Валидировать файл без загрузки.
        
        Returns:
            Список ошибок (пустой если всё ок)
        """
        try:
            self.load(path)
            return []
        except ConfigValidationError as e:
            return e.errors
        except FileNotFoundError:
            return [{"field": "file", "reason": f"File not found: {path}"}]
        except Exception as e:
            return [{"field": "file", "reason": str(e)}]
    
    def _parse_pydantic_errors(self, error: ValidationError) -> list[dict]:
        """Преобразовать ошибки Pydantic в наш формат."""
        errors = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            errors.append({
                "field": field,
                "reason": err["msg"],
                "type": err["type"]
            })
        return errors
    
    def _validate_references(self, config: ScenarioConfig) -> None:
        """Проверить что все ссылки валидны."""
        
        # Собираем ID всех states
        state_ids = {state.id for state in config.states}
        
        # Проверяем что есть начальный state
        start_states = [s for s in config.states if s.is_start]
        if not start_states:
            self.errors.append({
                "field": "states",
                "reason": "No start state defined. Set is_start=true for one state."
            })
        elif len(start_states) > 1:
            self.errors.append({
                "field": "states",
                "reason": f"Multiple start states: {[s.id for s in start_states]}. Only one allowed."
            })
        
        # Проверяем что есть конечный state
        end_states = [s for s in config.states if s.is_end]
        if not end_states:
            self.errors.append({
                "field": "states",
                "reason": "No end state defined. Set is_end=true for at least one state."
            })
        
        # Проверяем transitions
        for i, trans in enumerate(config.transitions):
            if trans.from_state not in state_ids:
                self.errors.append({
                    "field": f"transitions.{i}.from_state",
                    "reason": f"Unknown state: '{trans.from_state}'"
                })
            if trans.to_state not in state_ids:
                self.errors.append({
                    "field": f"transitions.{i}.to_state",
                    "reason": f"Unknown state: '{trans.to_state}'"
                })
        
        # Проверяем outcome rules
        all_field_ids = set()
        for state in config.states:
            for field in state.collect_fields:
                all_field_ids.add(field.id)
        
        for i, outcome in enumerate(config.outcomes):
            for j, rule in enumerate(outcome.rules):
                # Специальные поля не проверяем
                special_fields = {"callback_requested", "not_target_reason", 
                                  "questions_answered", "all_required"}
                if rule.field not in all_field_ids and rule.field not in special_fields:
                    self.errors.append({
                        "field": f"outcomes.{i}.rules.{j}.field",
                        "reason": f"Unknown field: '{rule.field}'"
                    })
        
        # Проверяем что есть default outcome
        default_outcomes = [o for o in config.outcomes if o.is_default]
        if not default_outcomes and config.outcomes:
            self.errors.append({
                "field": "outcomes",
                "reason": "No default outcome. Set is_default=true for one outcome."
            })


def load_config(path: Union[str, Path]) -> ScenarioConfig:
    """
    Удобная функция для загрузки конфига.
    
    Использование:
        config = load_config("bot_config.yaml")
    """
    return ConfigLoader().load(path)
