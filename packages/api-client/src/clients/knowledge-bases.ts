import { apiClient } from '../client'
import type { KnowledgeBase, Document, SearchResponse } from '@new-voice/types'

export const knowledgeBasesClient = {
  list: (params?: { company_id?: string; skip?: number; limit?: number }) =>
    apiClient.get<KnowledgeBase[]>('/knowledge-bases', { params }),

  get: (id: string) => apiClient.get<KnowledgeBase>(`/knowledge-bases/${id}`),

  create: (data: { name: string; description?: string; company_id: string }) =>
    apiClient.post<KnowledgeBase>('/knowledge-bases', data),

  update: (id: string, data: Partial<KnowledgeBase>) =>
    apiClient.put<KnowledgeBase>(`/knowledge-bases/${id}`, data),

  delete: (id: string) => apiClient.delete(`/knowledge-bases/${id}`),

  // Documents
  listDocuments: (id: string) =>
    apiClient.get<Document[]>(`/knowledge-bases/${id}/documents`),

  addDocument: (id: string, data: { title: string; content: string; source_type?: string }) =>
    apiClient.post<Document>(`/knowledge-bases/${id}/documents`, data),

  deleteDocument: (id: string, docId: string) =>
    apiClient.delete(`/knowledge-bases/${id}/documents/${docId}`),

  // Search
  search: (id: string, query: string, top_k: number = 3) =>
    apiClient.post<SearchResponse>(`/knowledge-bases/${id}/search`, { query, top_k }),
}
