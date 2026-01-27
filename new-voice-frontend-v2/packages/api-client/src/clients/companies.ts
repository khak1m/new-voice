import { apiClient } from '../client'
import type { Company, ListResponse } from '@new-voice/types'

export const companiesClient = {
  list: () => apiClient.get<ListResponse<Company>>('/companies'),

  get: (id: string) => apiClient.get<Company>(`/companies/${id}`),

  create: (data: Partial<Company>) => apiClient.post<Company>('/companies', data),

  update: (id: string, data: Partial<Company>) =>
    apiClient.put<Company>(`/companies/${id}`, data),

  delete: (id: string) => apiClient.delete(`/companies/${id}`),
}
