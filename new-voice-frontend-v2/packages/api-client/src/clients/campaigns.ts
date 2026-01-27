import { apiClient } from '../client'
import type { Campaign, ListResponse } from '@new-voice/types'

export const campaignsClient = {
  list: async (params?: {
    company_id?: string
    skillbase_id?: string
    status?: string
    skip?: number
    limit?: number
  }) => {
    const response = await apiClient.get<ListResponse<Campaign>>('/campaigns', { params })
    return response
  },

  get: async (id: string) => {
    const response = await apiClient.get<Campaign>(`/campaigns/${id}`)
    return response
  },

  create: async (data: Partial<Campaign>) => {
    const response = await apiClient.post<Campaign>('/campaigns', data)
    return response
  },

  update: async (id: string, data: Partial<Campaign>) => {
    const response = await apiClient.put<Campaign>(`/campaigns/${id}`, data)
    return response
  },

  delete: async (id: string) => {
    const response = await apiClient.delete(`/campaigns/${id}`)
    return response
  },

  // Control endpoints
  start: async (id: string) => {
    const response = await apiClient.post(`/campaigns/${id}/start`)
    return response
  },

  pause: async (id: string) => {
    const response = await apiClient.post(`/campaigns/${id}/pause`)
    return response
  },

  resume: async (id: string) => {
    const response = await apiClient.post(`/campaigns/${id}/resume`)
    return response
  },

  stop: async (id: string) => {
    const response = await apiClient.post(`/campaigns/${id}/stop`)
    return response
  },

  getStats: async (id: string) => {
    const response = await apiClient.get(`/campaigns/${id}/stats`)
    return response
  },
}
