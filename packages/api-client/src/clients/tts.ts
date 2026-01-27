import { apiClient } from '../client'

export interface TTSPreviewRequest {
  text: string
  voice_id?: string
  language?: string
}

export interface TTSPreviewResponse {
  audio_url: string
  duration?: number
}

export const ttsClient = {
  /**
   * Generate TTS preview audio from text
   * Returns audio blob for playback
   */
  preview: async (data: TTSPreviewRequest): Promise<Blob> => {
    const response = await apiClient.post('/tts/preview', data, {
      responseType: 'blob',
      headers: {
        'Accept': 'audio/mpeg, audio/wav, audio/*',
      },
    })
    return response.data
  },

  /**
   * Get TTS preview as data URL for direct playback
   */
  previewAsDataUrl: async (data: TTSPreviewRequest): Promise<string> => {
    const blob = await ttsClient.preview(data)
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result)
        } else {
          reject(new Error('Failed to convert blob to data URL'))
        }
      }
      reader.onerror = () => reject(new Error('Failed to read blob'))
      reader.readAsDataURL(blob)
    })
  },

  /**
   * Get available voices
   */
  getVoices: async (language?: string) => {
    const response = await apiClient.get('/tts/voices', {
      params: language ? { language } : undefined,
    })
    return response.data
  },
}
