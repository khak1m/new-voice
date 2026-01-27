import { apiClient } from '../client'
import type { Lead, ListResponse } from '@new-voice/types'

export const leadsClient = {
  list: (params?: {
    company_id?: string
    campaign_id?: string
    status?: string
    skip?: number
    limit?: number
  }) => apiClient.get<ListResponse<Lead>>('/leads', { params }),

  get: (id: string) => apiClient.get<Lead>(`/leads/${id}`),

  create: (data: Partial<Lead>) => apiClient.post<Lead>('/leads', data),

  update: (id: string, data: Partial<Lead>) => apiClient.put<Lead>(`/leads/${id}`, data),

  delete: (id: string) => apiClient.delete(`/leads/${id}`),

  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/leads/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  export: (params?: { company_id?: string; campaign_id?: string }) =>
    apiClient.get('/leads/export', { params, responseType: 'blob' }),
}
