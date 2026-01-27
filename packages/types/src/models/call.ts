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
}

export type CallStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'no_answer' | 'busy'

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
