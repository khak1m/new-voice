export interface Company {
  id: string
  name: string
  description?: string
  settings?: Record<string, unknown>
  limits?: CompanyLimits
  created_at: string
  updated_at: string
}

export interface CompanyLimits {
  max_bots?: number
  max_calls_per_month?: number
  max_concurrent_calls?: number
}
