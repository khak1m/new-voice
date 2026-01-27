// Skillbase types based on Sasha AI specification (5 tabs)

export interface Skillbase {
  id: string
  name: string
  description?: string
  company_id: string
  knowledge_base_id?: string
  config?: SkillbaseConfig
  created_at: string
  updated_at: string
}

export interface SkillbaseConfig {
  context: ContextConfig
  flow: FlowConfig
  agent: AgentConfig
  tools: ToolConfig[]
  knowledge_base: KnowledgeBaseConfig
}

// TAB 1: Context
export interface ContextConfig {
  role: string
  style: string
  rules: string[]
  facts: string[]
  lead_criteria: LeadCriteria[]
  language: string
  voice_id: string
  max_call_duration: number
}

export interface LeadCriteria {
  condition: string
  action: string
}

// TAB 2: Flow
export interface FlowConfig {
  greeting_phrases: string[]
  conversation_plan: string[]
}

// TAB 3: Agent
export interface AgentConfig {
  lead_transfer_fields: LeadTransferField[]
  closing_message: ClosingMessage
}

export interface LeadTransferField {
  name: string
  instruction: string
}

export interface ClosingMessage {
  type: 'llm_prompt' | 'static_template'
  prompt?: string
  template?: string
}

// TAB 4: Tools
export interface ToolConfig {
  name: 'transfer_call' | 'end_call' | 'detect_language' | 'skip_turn' | 'transfer_to_agent' | 'dtmf_tone'
  enabled: boolean
  config: Record<string, unknown>
}

// TAB 5: Knowledge Base
export interface KnowledgeBaseConfig {
  document_ids: string[]
}

// Voice
export interface Voice {
  id: string
  name: string
  gender: 'male' | 'female'
  style: string
}
