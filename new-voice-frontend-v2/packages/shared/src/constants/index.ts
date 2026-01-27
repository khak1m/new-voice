// API base URL - will be configured at build time
export const API_BASE_URL = '/api'

export const AVAILABLE_LANGUAGES = ['ru', 'en', 'es', 'de', 'fr', 'it', 'pt'] as const

export const CAMPAIGN_STATUSES = ['draft', 'scheduled', 'running', 'paused', 'completed', 'failed'] as const

export const CALL_STATUSES = ['pending', 'in_progress', 'completed', 'failed', 'no_answer', 'busy'] as const

export const LEAD_STATUSES = ['new', 'contacted', 'qualified', 'converted', 'rejected'] as const
