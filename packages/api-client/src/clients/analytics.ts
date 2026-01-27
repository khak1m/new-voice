import { apiClient } from '../client'
import type { AnalyticsData } from '@new-voice/types'

export const analyticsClient = {
  overview: (params?: { company_id?: string; start_date?: string; end_date?: string }) =>
    apiClient.get<AnalyticsData>('/analytics/overview', { params }),

  calls: (params?: { company_id?: string; start_date?: string; end_date?: string }) =>
    apiClient.get('/analytics/calls', { params }),

  campaigns: (params?: { company_id?: string; start_date?: string; end_date?: string }) =>
    apiClient.get('/analytics/campaigns', { params }),

  conversion: (params?: { company_id?: string; start_date?: string; end_date?: string }) =>
    apiClient.get('/analytics/conversion', { params }),

  costs: (params?: { company_id?: string; start_date?: string; end_date?: string }) =>
    apiClient.get('/analytics/costs', { params }),
}
