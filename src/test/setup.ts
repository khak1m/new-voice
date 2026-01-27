import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, afterAll } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// Mock handlers for API requests
export const handlers = [
  // Mock calls list
  http.get('*/api/calls', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'call-1',
          phone_number: '+7 999 123 4567',
          status: 'completed',
          direction: 'outbound',
          duration: 120,
          started_at: '2026-01-27T10:00:00Z',
          ended_at: '2026-01-27T10:02:00Z',
          outcome: 'success',
          agreement: true,
        },
        {
          id: 'call-2',
          phone_number: '+7 999 765 4321',
          status: 'failed',
          direction: 'inbound',
          duration: 30,
          started_at: '2026-01-27T09:00:00Z',
          ended_at: '2026-01-27T09:00:30Z',
          outcome: 'no_answer',
          agreement: false,
        },
      ],
      total: 2,
    })
  }),

  // Mock single call
  http.get('*/api/calls/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      phone_number: '+7 999 123 4567',
      status: 'completed',
      direction: 'outbound',
      duration: 120,
      started_at: '2026-01-27T10:00:00Z',
      ended_at: '2026-01-27T10:02:00Z',
      connected_at: '2026-01-27T10:00:05Z',
      outcome: 'success',
      agreement: true,
      completion_reason: 'Call completed successfully',
      skillbase_id: 'skillbase-1',
    })
  }),

  // Mock transcript
  http.get('*/api/calls/:id/transcript', () => {
    return HttpResponse.json({
      messages: [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'Hello, this is AI assistant. How can I help you?',
          timestamp: '2026-01-27T10:00:10Z',
        },
        {
          id: 'msg-2',
          role: 'user',
          content: 'I want to know about your services.',
          timestamp: '2026-01-27T10:00:20Z',
        },
        {
          id: 'msg-3',
          role: 'assistant',
          content: 'Sure! We offer voice AI solutions for businesses.',
          timestamp: '2026-01-27T10:00:30Z',
        },
      ],
    })
  }),

  // Mock TTS preview
  http.post('*/api/tts/preview', async () => {
    // Return a mock audio blob
    const audioData = new Uint8Array([0, 0, 0, 0])
    return new HttpResponse(audioData, {
      headers: {
        'Content-Type': 'audio/mpeg',
      },
    })
  }),

  // Mock skillbases list
  http.get('*/api/skillbases', () => {
    return HttpResponse.json({
      items: [
        {
          id: 'skillbase-1',
          name: 'Sales Bot',
          description: 'Sales assistant',
          company_id: 'company-1',
          is_active: true,
          config: {
            flow: {
              greeting_phrases: ['Hello!', 'Hi there!'],
              conversation_plan: ['Greet', 'Ask needs', 'Offer solution'],
            },
            voice: {
              tts_voice_id: 'voice-1',
              language: 'ru',
            },
          },
        },
      ],
      total: 1,
    })
  }),
]

// Setup MSW server
export const server = setupServer(...handlers)

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }))

// Reset handlers after each test
afterEach(() => {
  cleanup()
  server.resetHandlers()
})

// Close server after all tests
afterAll(() => server.close())

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.IntersectionObserver = MockIntersectionObserver as any

// Mock Audio API
window.HTMLMediaElement.prototype.play = () => Promise.resolve()
window.HTMLMediaElement.prototype.pause = () => {}
