"""
Pydantic schemas for Skillbase configuration validation.

Based on Sasha AI specification with 5 tabs:
1. Context (role, style, rules, facts, voice, language)
2. Flow (greeting phrases, conversation plan)
3. Agent (lead transfer, closing message)
4. Tools (transfer call, end call, etc.)
5. Knowledge Base (document IDs)

Author: Senior Backend Engineer
Date: 2026-01-21
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# =============================================================================
# Enums and Constants
# =============================================================================

AVAILABLE_LANGUAGES = ["ru", "en", "es", "de", "fr", "it", "pt"]
AVAILABLE_VOICES = [
    {"id": "sasha_v1", "name": "Саша v1", "gender": "female", "style": "friendly"},
    {"id": "dima_v1", "name": "Дима v1", "gender": "male", "style": "business"},
    {"id": "sergey_v1", "name": "Сергей v1", "gender": "male", "style": "calm"},
    {"id": "tatyana_v1", "name": "Татьяна v1", "gender": "female", "style": "trustworthy"},
]


# =============================================================================
# TAB 1: Context Configuration
# =============================================================================

class LeadCriteria(BaseModel):
    """Критерий передачи лида."""
    condition: str = Field(..., max_length=500)
    action: str = Field(..., max_length=500)


class ContextConfig(BaseModel):
    """
    TAB 1: Контекст
    
    Определяет личность и поведение ИИ бота.
    """
    
    role: str = Field(
        ...,
        description="Роль продавца (до 500 символов)",
        min_length=1,
        max_length=500
    )
    
    style: str = Field(
        ...,
        description="Стиль речи (до 500 символов)",
        min_length=1,
        max_length=500
    )
    
    rules: List[str] = Field(
        default_factory=list,
        description="Важные правила (каждое до 500 символов)"
    )
    
    facts: List[str] = Field(
        default_factory=list,
        description="Аргументы и факты (каждый до 500 символов)"
    )
    
    lead_criteria: List[LeadCriteria] = Field(
        default_factory=list,
        description="Критерии передачи лида"
    )
    
    language: str = Field(
        default="ru",
        description="Язык ИИ бота"
    )
    
    voice_id: str = Field(
        default="sasha_v1",
        description="ID голоса"
    )
    
    max_call_duration: int = Field(
        default=600,
        description="Максимальная длительность звонка (секунды)",
        ge=60,
        le=3600
    )
    
    @field_validator('rules', 'facts')
    @classmethod
    def validate_list_items(cls, v):
        """Проверка элементов списка."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Элементы списка должны быть непустыми строками")
            if len(item) > 500:
                raise ValueError("Элемент списка не должен превышать 500 символов")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "Тебя зовут Зиля, ты живой сотрудник. Ты работаешь в управляющей компании...",
                "style": "Говори максимально кратко и по делу. Один вопрос — одна короткая фраза...",
                "rules": [
                    "Отвечай опираясь на последнюю речь клиента",
                    "Не сдавайся. Если клиент отказывает — сохраняй спокойствие..."
                ],
                "facts": [
                    "Мы работаем с 9:00 до 21:00",
                    "Принимаем оплату картой и наличными"
                ],
                "lead_criteria": [],
                "language": "ru",
                "voice_id": "sasha_v1",
                "max_call_duration": 600
            }
        }


# =============================================================================
# TAB 2: Flow Configuration
# =============================================================================

class FlowConfig(BaseModel):
    """
    TAB 2: План разговора
    
    Определяет структуру разговора.
    """
    
    greeting_phrases: List[str] = Field(
        default_factory=list,
        description="Начало разговора (макс. 3 фразы, каждая до 500 символов)",
        max_items=3
    )
    
    conversation_plan: List[str] = Field(
        default_factory=list,
        description="План разговора (каждый пункт до 500 символов)"
    )
    
    @field_validator('greeting_phrases', 'conversation_plan')
    @classmethod
    def validate_phrases(cls, v):
        """Проверка фраз."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Фразы должны быть непустыми строками")
            if len(item) > 500:
                raise ValueError("Фраза не должна превышать 500 символов")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "greeting_phrases": [
                    "Алло...",
                    "Даа, добрый день... подскажите от управляющей компании вам, квитанции приходят верно?"
                ],
                "conversation_plan": [
                    "Узнай как к собеседнику обращаться",
                    "Подтверди что это владелец квартиры",
                    "Сообщи о задолженности по оплате коммунальных услуг"
                ]
            }
        }


# =============================================================================
# TAB 3: Agent Configuration
# =============================================================================

class LeadTransferField(BaseModel):
    """Кастомное поле для передачи в CRM."""
    name: str = Field(..., max_length=50)
    instruction: str = Field(..., max_length=1000)


class ClosingMessage(BaseModel):
    """Формирователь закрывающего сообщения."""
    type: Literal["llm_prompt", "static_template"] = Field(default="llm_prompt")
    prompt: Optional[str] = Field(None, max_length=300)
    template: Optional[str] = None


class AgentConfig(BaseModel):
    """
    TAB 3: Агенты
    
    Настройки лид трансфера и закрывающего сообщения.
    """
    
    lead_transfer_fields: List[LeadTransferField] = Field(
        default_factory=list,
        description="Кастомные поля для передачи в CRM"
    )
    
    closing_message: ClosingMessage = Field(
        default_factory=ClosingMessage,
        description="Формирователь закрывающего сообщения"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_transfer_fields": [
                    {
                        "name": "funnelID",
                        "instruction": "укажи ID воронки, 38 - если клиент был на мероприятии..."
                    }
                ],
                "closing_message": {
                    "type": "llm_prompt",
                    "prompt": "Сформируй дружелюбное закрывающее сообщение на основе контекста разговора"
                }
            }
        }


# =============================================================================
# TAB 4: Tools Configuration
# =============================================================================

class TransferRule(BaseModel):
    """Правило перевода звонка."""
    condition: str = Field(..., description="Условие для перевода")
    context_rules: str = Field(..., description="Правила для проговаривания контекста")
    phone_or_sip: str = Field(..., description="Номер телефона или SIP-адрес")


class ToolConfig(BaseModel):
    """
    Конфигурация инструмента.
    """
    
    name: Literal[
        "transfer_call",
        "end_call",
        "detect_language",
        "skip_turn",
        "transfer_to_agent",
        "dtmf_tone"
    ] = Field(..., description="Название инструмента")
    
    enabled: bool = Field(default=False, description="Активен ли инструмент")
    
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Конфигурация инструмента"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "transfer_call",
                "enabled": True,
                "config": {
                    "description": "",
                    "rules": [
                        {
                            "condition": "Клиент просит перевести на менеджера",
                            "context_rules": "Иван, 31 год, ищет двухкомнатную квартиру",
                            "phone_or_sip": "+79991234567"
                        }
                    ]
                }
            }
        }


# =============================================================================
# TAB 5: Knowledge Base Configuration
# =============================================================================

class KnowledgeBaseConfig(BaseModel):
    """
    TAB 5: База знаний
    
    Привязка документов из базы знаний.
    """
    
    document_ids: List[str] = Field(
        default_factory=list,
        description="ID документов из базы знаний"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
                ]
            }
        }


# =============================================================================
# Complete Skillbase Configuration (Sasha AI spec)
# =============================================================================

class SkillbaseConfig(BaseModel):
    """
    Полная конфигурация Skillbase по спецификации Sasha AI.
    
    Структура из 5 табов:
    1. Context - роль, стиль, правила, факты, голос
    2. Flow - приветствие, план разговора
    3. Agent - лид трансфер, закрывающее сообщение
    4. Tools - инструменты (перевод, завершение звонка и т.д.)
    5. Knowledge Base - привязка документов
    """
    
    context: ContextConfig = Field(
        ...,
        description="TAB 1: Контекст (роль, стиль, правила, факты, голос)"
    )
    
    flow: FlowConfig = Field(
        ...,
        description="TAB 2: План разговора (приветствие, план)"
    )
    
    agent: AgentConfig = Field(
        default_factory=AgentConfig,
        description="TAB 3: Агенты (лид трансфер, закрывающее сообщение)"
    )
    
    tools: List[ToolConfig] = Field(
        default_factory=list,
        description="TAB 4: Инструменты"
    )
    
    knowledge_base: KnowledgeBaseConfig = Field(
        default_factory=KnowledgeBaseConfig,
        description="TAB 5: База знаний"
    )
    
    @field_validator('tools')
    @classmethod
    def validate_unique_tool_names(cls, v):
        """Проверка уникальности имен инструментов."""
        if v:
            names = [tool.name for tool in v]
            if len(names) != len(set(names)):
                raise ValueError("Имена инструментов должны быть уникальными")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "context": {
                    "role": "Тебя зовут Зиля, ты живой сотрудник...",
                    "style": "Говори максимально кратко и по делу...",
                    "rules": ["Отвечай опираясь на последнюю речь клиента"],
                    "facts": ["Мы работаем с 9:00 до 21:00"],
                    "lead_criteria": [],
                    "language": "ru",
                    "voice_id": "sasha_v1",
                    "max_call_duration": 600
                },
                "flow": {
                    "greeting_phrases": ["Алло...", "Добрый день..."],
                    "conversation_plan": [
                        "Узнай как к собеседнику обращаться",
                        "Подтверди что это владелец квартиры"
                    ]
                },
                "agent": {
                    "lead_transfer_fields": [],
                    "closing_message": {
                        "type": "llm_prompt",
                        "prompt": "Сформируй дружелюбное закрывающее сообщение"
                    }
                },
                "tools": [
                    {
                        "name": "transfer_call",
                        "enabled": True,
                        "config": {"description": "", "rules": []}
                    },
                    {
                        "name": "end_call",
                        "enabled": True,
                        "config": {}
                    }
                ],
                "knowledge_base": {
                    "document_ids": []
                }
            }
        }


# =============================================================================
# API Request/Response Schemas
# =============================================================================

class SkillbaseCreate(BaseModel):
    """Схема создания Skillbase."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    company_id: UUID
    knowledge_base_id: Optional[UUID] = None
    config: Optional[SkillbaseConfig] = None


class SkillbaseUpdate(BaseModel):
    """Схема обновления Skillbase."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    company_id: Optional[UUID] = None
    knowledge_base_id: Optional[UUID] = None
    config: Optional[SkillbaseConfig] = None


class SkillbaseResponse(BaseModel):
    """Схема ответа Skillbase."""
    id: UUID
    name: str
    description: Optional[str]
    company_id: UUID
    knowledge_base_id: Optional[UUID]
    config: Optional[SkillbaseConfig]
    created_at: Any
    updated_at: Any
    
    class Config:
        from_attributes = True


class SkillbaseListResponse(BaseModel):
    """Список Skillbases."""
    items: List[SkillbaseResponse]
    total: int


# =============================================================================
# Voice API Schemas
# =============================================================================

class VoiceInfo(BaseModel):
    """Информация о голосе."""
    id: str
    name: str
    gender: Literal["male", "female"]
    style: str


class TTSPreviewRequest(BaseModel):
    """Запрос на TTS preview."""
    text: str = Field(..., max_length=500)
    voice_id: str


class TestCallRequest(BaseModel):
    """Запрос на тестовый звонок."""
    phone_number: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")

