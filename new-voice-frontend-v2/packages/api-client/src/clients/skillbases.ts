import { apiClient } from '../client'
import type {
  Skillbase,
  ListResponse,
  SkillbaseConfigResponse,
  VoicesListResponse,
  TTSPreviewRequest,
  TTSPreviewResponse,
  TestCallRequest,
  TestCallResponse,
} from '@new-voice/types'

export const skillbasesClient = {
  list: async (params?: {
    company_id?: string
    is_active?: boolean
    is_published?: boolean
    skip?: number
    limit?: number
  }) => {
    const response = await apiClient.get<ListResponse<Skillbase>>('/skillbases', { params })
    return response.data
  },

  get: async (id: string) => {
    const response = await apiClient.get<Skillbase>(`/skillbases/${id}`)
    return response.data
  },

  create: async (data: Partial<Skillbase>) => {
    const response = await apiClient.post<Skillbase>('/skillbases', data)
    return response.data
  },

  update: async (id: string, data: Partial<Skillbase>) => {
    const response = await apiClient.put<Skillbase>(`/skillbases/${id}`, data)
    return response.data
  },

  delete: async (id: string) => {
    const response = await apiClient.delete(`/skillbases/${id}`)
    return response.data
  },

  // Config endpoints
  getConfig: async (id: string) => {
    const response = await apiClient.get<SkillbaseConfigResponse>(`/skillbases/${id}/config`)
    return response.data
  },

  updateConfig: async (id: string, config: SkillbaseConfigResponse['config']) => {
    const response = await apiClient.put<SkillbaseConfigResponse>(`/skillbases/${id}/config`, config)
    return response.data
  },

  // Voice endpoints
  listVoices: async () => {
    const response = await apiClient.get<VoicesListResponse>('/skillbases/voices/list')
    return response.data
  },

  ttsPreview: async (data: TTSPreviewRequest) => {
    const response = await apiClient.post<TTSPreviewResponse>('/skillbases/tts-preview', data)
    return response.data
  },

  testCall: async (id: string, data: TestCallRequest) => {
    const response = await apiClient.post<TestCallResponse>(`/skillbases/${id}/test-call`, data)
    return response.data
  },
}
