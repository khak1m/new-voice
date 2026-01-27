export interface Lead {
  id: string
  campaign_id: string
  company_id: string
  phone_number: string
  first_name?: string
  last_name?: string
  email?: string
  status: LeadStatus
  custom_data?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'converted' | 'rejected'
