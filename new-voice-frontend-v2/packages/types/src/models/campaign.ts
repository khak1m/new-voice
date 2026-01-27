export interface Campaign {
  id: string
  name: string
  description?: string
  company_id: string
  skillbase_id: string
  status: CampaignStatus
  
  // Scheduling
  start_time?: string
  end_time?: string
  daily_start_time: string
  daily_end_time: string
  timezone: string
  
  // Rate limiting
  max_concurrent_calls: number
  calls_per_minute: number
  max_retries: number
  retry_delay_minutes: number
  
  // Stats
  total_tasks: number
  completed_tasks: number
  failed_tasks: number
  
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

export type CampaignStatus = 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed'

export interface CampaignSchedule {
  start_time?: string
  end_time?: string
  timezone?: string
}

export interface RateLimits {
  max_concurrent_calls?: number
  calls_per_minute?: number
}

export interface RetryConfig {
  max_retries?: number
  retry_delay?: number
}
