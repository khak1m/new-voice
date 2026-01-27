import { apiClient } from '../client'
import type { KnowledgeBase, ListResponse } from '@new-voice/types'

export const knowledgeBasesClient = {
  list: (params?: { company_id?: string; skip?: number; limit?: number }) =>
    apiClient.get<ListResponse<KnowledgeBase>>('/knowledge-bases', { params }),

  get: (id: string) => apiClient.get<KnowledgeBase>(`/knowledge-bases/${id}`),

  create: (data: Partial<KnowledgeBase>) =>
    apiClient.post<KnowledgeBase>('/knowledge-bases', data),

  update: (id: string, data: Partial<KnowledgeBase>) =>
    apiClient.put<KnowledgeBase>(`/knowledge-bases/${id}`, data),

  delete: (id: string) => apiClient.delete(`/knowledge-bases/${id}`),

  uploadDocument: (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`/knowledge-bases/${id}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  deleteDocument: (id: string, docId: string) =>
    apiClient.delete(`/knowledge-bases/${id}/documents/${docId}`),
}
