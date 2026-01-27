export interface Call {
  id: string
  campaign_id: string
  lead_id?: string
  skillbase_id: string
  status: CallStatus
  phone_number: string
  duration?: number
  outcome?: string
  transcript?: string
  recording_url?: string
  metrics?: CallMetrics
  created_at: string
  updated_at: string
  started_at?: string
  ended_at?: string
  connected_at?: string
  // Extended fields for detail view
  direction?: CallDirection
  agreement?: boolean
  rejection_reason?: string
  completion_reason?: string
  skillbase_name?: string
  campaign_name?: string
}

export type CallStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'no_answer' | 'busy'

export type CallDirection = 'inbound' | 'outbound'

export interface CallMetrics {
  latency_avg?: number
  latency_min?: number
  latency_max?: number
  token_count_input?: number
  token_count_output?: number
  cost_total?: number
  interruptions?: number
  sentiment?: string
}

export interface TranscriptMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export interface CallTranscript {
  messages: TranscriptMessage[]
}

export interface CallAgreement {
  id: string
  description: string
  value?: string
  created_at: string
}

export interface CallSession {
  session_id: string
  provider: string
  start_time: string
  end_time?: string
  quality_score?: number
}

export interface ContactInfo {
  name?: string
  email?: string
  company?: string
  notes?: string
}

export interface TransferStatus {
  transferred: boolean
  transfer_time?: string
  transfer_to?: string
  transfer_reason?: string
}

export interface LeadTransfer {
  transferred: boolean
  lead_id?: string
  fields?: Record<string, string>
  transferred_at?: string
}
