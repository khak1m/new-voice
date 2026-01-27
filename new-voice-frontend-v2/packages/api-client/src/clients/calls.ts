import { apiClient } from '../client'
import type { Call, ListResponse } from '@new-voice/types'

export const callsClient = {
  list: (params?: {
    company_id?: string
    campaign_id?: string
    status?: string
    skip?: number
    limit?: number
  }) => apiClient.get<ListResponse<Call>>('/calls', { params }),

  get: (id: string) => apiClient.get<Call>(`/calls/${id}`),

  getTranscript: (id: string) => apiClient.get(`/calls/${id}/transcript`),

  getRecording: (id: string) => apiClient.get(`/calls/${id}/recording`),

  rate: (id: string, rating: number) => apiClient.post(`/calls/${id}/rate`, { rating }),
}
