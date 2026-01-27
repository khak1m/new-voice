import type { SkillbaseConfig, Voice } from '../models'

export interface TTSPreviewRequest {
  text: string
  voice_id: string
}

export interface TTSPreviewResponse {
  audio_url: string
  duration: number
  voice_id: string
  text: string
}

export interface TestCallRequest {
  phone_number: string
}

export interface TestCallResponse {
  call_id: string
  status: string
  phone_number: string
  skillbase_id: string
  message: string
}

export interface SkillbaseConfigResponse {
  id: string
  name: string
  config: SkillbaseConfig
  version: number
  updated_at: string
}

export interface VoicesListResponse {
  voices: Voice[]
}
