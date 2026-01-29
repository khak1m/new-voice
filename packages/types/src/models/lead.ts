export interface Lead {
  id: string
  call_id?: string
  bot_id?: string
  company_id?: string
  name?: string
  phone?: string
  email?: string
  data: Record<string, unknown>
  status: LeadStatus
  notes?: string
  webhook_sent: boolean
  created_at: string
  updated_at: string
}

export type LeadStatus = 'new' | 'contacted' | 'converted' | 'rejected'
