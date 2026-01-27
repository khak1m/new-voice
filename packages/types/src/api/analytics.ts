export interface AnalyticsData {
  total_calls: number
  successful_calls: number
  failed_calls: number
  avg_duration: number
  total_cost: number
  conversion_rate: number
}

export interface DashboardStats {
  active_campaigns: number
  total_calls_today: number
  successful_calls_today: number
  total_cost_today: number
}
