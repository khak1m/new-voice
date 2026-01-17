"""
Pydantic schemas for Skillbase configuration validation.

These schemas validate the JSONB config field structure according to
the "Sasha AI" specification defined in the design document.

Author: Senior Backend Engineer
Date: 2026-01-17
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class FlowType(str, Enum):
    """Type of conversation flow."""
    LINEAR = "linear"
    GRAPH = "graph"


class TTSProvider(str, Enum):
    """Text-to-Speech provider."""
    CARTESIA = "cartesia"
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"


class STTProvider(str, Enum):
    """Speech-to-Text provider."""
    DEEPGRAM = "deepgram"
    ASSEMBLYAI = "assemblyai"
    OPENAI = "openai"


class LLMProvider(str, Enum):
    """LLM provider."""
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


# =============================================================================
# Context Configuration
# =============================================================================

class ContextConfig(BaseModel):
    """
    Context configuration for the bot's personality and knowledge.
    
    Defines:
    - Role: Who the bot is (e.g., "Receptionist at beauty salon")
    - Style: How the bot communicates (e.g., "Friendly and professional")
    - Safety rules: What the bot must NOT do
    - Facts: Static knowledge the bot should know
    """
    
    role: str = Field(
        ...,
        description="Bot's role/identity (e.g., 'Receptionist at beauty salon')",
        min_length=1,
        max_length=500
    )
    
    style: str = Field(
        ...,
        description="Communication style (e.g., 'Friendly and professional')",
        min_length=1,
        max_length=500
    )
    
    safety_rules: List[str] = Field(
        default_factory=list,
        description="List of rules the bot must follow (e.g., 'Never give medical advice')"
    )
    
    facts: List[str] = Field(
        default_factory=list,
        description="Static facts the bot should know (e.g., 'We work 9am-9pm')"
    )
    
    @field_validator('safety_rules', 'facts')
    @classmethod
    def validate_list_items(cls, v):
        """Ensure list items are non-empty strings."""
        if v:
            for item in v:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("List items must be non-empty strings")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "Receptionist at beauty salon 'Glamour'",
                "style": "Friendly, professional, helpful",
                "safety_rules": [
                    "Never give medical advice",
                    "Never discuss prices without checking availability"
                ],
                "facts": [
                    "We work Monday-Sunday 9am-9pm",
                    "We accept cash and cards",
                    "Parking is available"
                ]
            }
        }


# =============================================================================
# Flow Configuration
# =============================================================================

class StateConfig(BaseModel):
    """Configuration for a single conversation state."""
    
    id: str = Field(..., description="Unique state identifier")
    name: str = Field(..., description="Human-readable state name")
    prompt: Optional[str] = Field(None, description="Optional state-specific prompt")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "greeting",
                "name": "Greeting",
                "prompt": "Greet the customer warmly"
            }
        }


class TransitionConfig(BaseModel):
    """Configuration for state transition."""
    
    from_state: str = Field(..., description="Source state ID")
    to_state: str = Field(..., description="Target state ID")
    condition: Optional[str] = Field(None, description="Optional transition condition")
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_state": "greeting",
                "to_state": "service_inquiry",
                "condition": "user_responded"
            }
        }


class FlowConfig(BaseModel):
    """
    Flow configuration for conversation structure.
    
    Supports:
    - Linear: Sequential states (greeting -> inquiry -> booking -> confirmation)
    - Graph: Complex state machine with conditional transitions
    
    States can be:
    - Simple strings (for linear flows): ["greeting", "inquiry", "booking"]
    - StateConfig objects (for complex flows with prompts)
    """
    
    type: FlowType = Field(
        ...,
        description="Flow type: 'linear' for sequential, 'graph' for state machine"
    )
    
    states: List[Union[str, StateConfig]] = Field(
        ...,
        description="List of conversation states (strings or StateConfig objects)",
        min_items=1
    )
    
    transitions: List[TransitionConfig] = Field(
        default_factory=list,
        description="State transitions (required for 'graph' type)"
    )
    
    @model_validator(mode='after')
    def validate_flow_consistency(self):
        """Validate flow configuration consistency."""
        if not self.states:
            raise ValueError("At least one state is required")
        
        # For graph type, validate transitions reference valid states
        if self.type == FlowType.GRAPH and self.transitions:
            # Extract state IDs (handle both string and StateConfig)
            state_ids = set()
            for state in self.states:
                if isinstance(state, str):
                    state_ids.add(state)
                else:
                    state_ids.add(state.id)
            
            for transition in self.transitions:
                if transition.from_state not in state_ids:
                    raise ValueError(f"Transition references unknown state: {transition.from_state}")
                if transition.to_state not in state_ids:
                    raise ValueError(f"Transition references unknown state: {transition.to_state}")
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "linear",
                "states": [
                    {"id": "greeting", "name": "Greeting"},
                    {"id": "inquiry", "name": "Service Inquiry"},
                    {"id": "booking", "name": "Booking"},
                    {"id": "confirmation", "name": "Confirmation"}
                ],
                "transitions": []
            }
        }


# =============================================================================
# Agent Configuration
# =============================================================================

class AgentConfig(BaseModel):
    """
    Agent configuration for handoff and CRM integration.
    
    Defines:
    - When to transfer to human agent
    - How to map conversation data to CRM fields
    """
    
    handoff_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Criteria for transferring to human agent"
    )
    
    crm_field_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from conversation fields to CRM fields"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "handoff_criteria": {
                    "complex_request": True,
                    "customer_angry": True,
                    "technical_issue": True
                },
                "crm_field_mapping": {
                    "name": "client_name",
                    "phone": "client_phone",
                    "email": "client_email",
                    "service": "requested_service"
                }
            }
        }


# =============================================================================
# Tool Configuration
# =============================================================================

class ToolConfig(BaseModel):
    """
    Configuration for a function calling tool.
    
    Tools allow the bot to perform actions like:
    - Check calendar availability
    - Book appointments
    - Transfer calls
    - Send SMS/Email
    """
    
    name: str = Field(
        ...,
        description="Tool name (e.g., 'calendar', 'transfer', 'send_sms')",
        min_length=1
    )
    
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific configuration"
    )
    
    enabled: bool = Field(
        default=True,
        description="Whether this tool is enabled"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "calendar",
                "config": {
                    "api_url": "https://api.example.com/calendar",
                    "api_key": "secret_key"
                },
                "enabled": True
            }
        }


# =============================================================================
# Voice Configuration
# =============================================================================

class VoiceConfig(BaseModel):
    """
    Voice pipeline configuration.
    
    Defines:
    - TTS provider and voice
    - STT provider and language
    """
    
    tts_provider: TTSProvider = Field(
        ...,
        description="Text-to-Speech provider"
    )
    
    tts_voice_id: str = Field(
        ...,
        description="Voice ID from the TTS provider",
        min_length=1
    )
    
    stt_provider: STTProvider = Field(
        ...,
        description="Speech-to-Text provider"
    )
    
    stt_language: str = Field(
        default="ru",
        description="STT language code (e.g., 'ru', 'en', 'es')"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tts_provider": "cartesia",
                "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                "stt_provider": "deepgram",
                "stt_language": "ru"
            }
        }


# =============================================================================
# LLM Configuration
# =============================================================================

class LLMConfig(BaseModel):
    """
    LLM configuration.
    
    Defines:
    - Provider (Groq, OpenAI, Ollama, etc.)
    - Model name
    - Generation parameters
    """
    
    provider: LLMProvider = Field(
        ...,
        description="LLM provider"
    )
    
    model: str = Field(
        ...,
        description="Model name (e.g., 'llama-3.1-70b-versatile', 'gpt-4')",
        min_length=1
    )
    
    temperature: float = Field(
        default=0.7,
        description="Sampling temperature (0.0-2.0)",
        ge=0.0,
        le=2.0
    )
    
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens to generate",
        gt=0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "groq",
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.7,
                "max_tokens": 1024
            }
        }


# =============================================================================
# Complete Skillbase Configuration
# =============================================================================

class SkillbaseConfig(BaseModel):
    """
    Complete Skillbase configuration schema.
    
    This is the root schema that validates the entire JSONB config field.
    All sub-configurations are validated according to their respective schemas.
    
    **INTELLECTUAL HONESTY NOTE:**
    This schema is based on the design document specification.
    If any fields are missing or incorrect, they should be added/corrected
    based on actual requirements.
    """
    
    context: ContextConfig = Field(
        ...,
        description="Bot personality and knowledge context"
    )
    
    flow: FlowConfig = Field(
        ...,
        description="Conversation flow structure"
    )
    
    agent: AgentConfig = Field(
        default_factory=AgentConfig,
        description="Agent handoff and CRM configuration"
    )
    
    tools: List[ToolConfig] = Field(
        default_factory=list,
        description="Available function calling tools"
    )
    
    voice: VoiceConfig = Field(
        ...,
        description="Voice pipeline configuration"
    )
    
    llm: LLMConfig = Field(
        ...,
        description="LLM configuration"
    )
    
    @field_validator('tools')
    @classmethod
    def validate_unique_tool_names(cls, v):
        """Ensure tool names are unique."""
        if v:
            names = [tool.name for tool in v]
            if len(names) != len(set(names)):
                raise ValueError("Tool names must be unique")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "context": {
                    "role": "Receptionist at beauty salon 'Glamour'",
                    "style": "Friendly and professional",
                    "safety_rules": ["Never give medical advice"],
                    "facts": ["We work 9am-9pm", "We accept cards and cash"]
                },
                "flow": {
                    "type": "linear",
                    "states": [
                        {"id": "greeting", "name": "Greeting"},
                        {"id": "inquiry", "name": "Service Inquiry"},
                        {"id": "booking", "name": "Booking"}
                    ],
                    "transitions": []
                },
                "agent": {
                    "handoff_criteria": {"complex_request": True},
                    "crm_field_mapping": {"name": "client_name"}
                },
                "tools": [
                    {
                        "name": "calendar",
                        "config": {"api_url": "https://api.example.com"},
                        "enabled": True
                    }
                ],
                "voice": {
                    "tts_provider": "cartesia",
                    "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                    "stt_provider": "deepgram",
                    "stt_language": "ru"
                },
                "llm": {
                    "provider": "groq",
                    "model": "llama-3.1-70b-versatile",
                    "temperature": 0.7
                }
            }
        }
