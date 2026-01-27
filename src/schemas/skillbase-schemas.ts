import { z } from 'zod'

// Create Skillbase Schema
export const createSkillbaseSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name must be less than 100 characters'),
  description: z.string().optional(),
  company_id: z.string().min(1, 'Company is required'),
})

export type CreateSkillbaseInput = z.infer<typeof createSkillbaseSchema>

// Context Tab Schema
export const contextConfigSchema = z.object({
  role: z.string().min(1, 'Role is required'),
  style: z.string().min(1, 'Style is required'),
  rules: z.array(z.string()),
  facts: z.array(z.string()),
  lead_criteria: z.array(
    z.object({
      condition: z.string(),
      action: z.string(),
    })
  ),
  language: z.string().min(1, 'Language is required'),
  voice_id: z.string().min(1, 'Voice is required'),
  max_call_duration: z.number().min(30).max(3600),
})

// Flow Tab Schema
export const flowConfigSchema = z.object({
  greeting_phrases: z.array(z.string()).min(1, 'At least one greeting phrase is required'),
  conversation_plan: z.array(z.string()).min(1, 'At least one conversation step is required'),
})

// Agent Tab Schema
export const agentConfigSchema = z.object({
  lead_transfer_fields: z.array(
    z.object({
      name: z.string().min(1, 'Field name is required'),
      instruction: z.string().min(1, 'Instruction is required'),
    })
  ),
  closing_message: z.object({
    type: z.enum(['llm_prompt', 'static_template']),
    prompt: z.string().optional(),
    template: z.string().optional(),
  }),
})

// Tools Tab Schema
export const toolConfigSchema = z.object({
  name: z.enum([
    'transfer_call',
    'end_call',
    'detect_language',
    'skip_turn',
    'transfer_to_agent',
    'dtmf_tone',
  ]),
  enabled: z.boolean(),
  config: z.record(z.unknown()),
})

export const toolsConfigSchema = z.array(toolConfigSchema)

// Knowledge Base Tab Schema
export const knowledgeBaseConfigSchema = z.object({
  document_ids: z.array(z.string()),
})

// Full Skillbase Config Schema
export const skillbaseConfigSchema = z.object({
  context: contextConfigSchema,
  flow: flowConfigSchema,
  agent: agentConfigSchema,
  tools: toolsConfigSchema,
  knowledge_base: knowledgeBaseConfigSchema,
})

export type SkillbaseConfigInput = z.infer<typeof skillbaseConfigSchema>
