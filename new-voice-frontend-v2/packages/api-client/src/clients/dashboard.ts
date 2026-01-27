import { apiClient } from '../client'
import type { DashboardStats } from '@new-voice/types'

export const dashboardClient = {
  stats: (params?: { company_id?: string }) =>
    apiClient.get<DashboardStats>('/dashboard/stats', { params }),

  recentCalls: (params?: { company_id?: string; limit?: number }) =>
    apiClient.get('/dashboard/recent-calls', { params }),

  activeCampaigns: (params?: { company_id?: string }) =>
    apiClient.get('/dashboard/active-campaigns', { params }),
}
