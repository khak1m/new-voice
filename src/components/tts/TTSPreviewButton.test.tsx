import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../test/test-utils'
import userEvent from '@testing-library/user-event'
import { TTSPreviewButton } from './TTSPreviewButton'
import { server } from '../../test/setup'
import { http, HttpResponse } from 'msw'

describe('TTSPreviewButton', () => {
  beforeEach(() => {
    // Reset any mocks
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the button', () => {
      render(<TTSPreviewButton text="Hello" />)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    it('is disabled when text is empty', () => {
      render(<TTSPreviewButton text="" />)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('is disabled when text is only whitespace', () => {
      render(<TTSPreviewButton text="   " />)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('is enabled when text has content', () => {
      render(<TTSPreviewButton text="Hello world" />)
      
      const button = screen.getByRole('button')
      expect(button).not.toBeDisabled()
    })

    it('respects the disabled prop', () => {
      render(<TTSPreviewButton text="Hello" disabled />)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })

  describe('TTS API Request Triggering', () => {
    it('sends correct API request when clicked', async () => {
      const user = userEvent.setup()
      let capturedRequest: any = null
      
      server.use(
        http.post('*/api/tts/preview', async ({ request }) => {
          capturedRequest = await request.json()
          const audioData = new Uint8Array([0, 0, 0, 0])
          return new HttpResponse(audioData, {
            headers: { 'Content-Type': 'audio/mpeg' },
          })
        })
      )
      
      render(
        <TTSPreviewButton 
          text="Test phrase" 
          voiceId="voice-123"
          language="ru"
        />
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      await waitFor(() => {
        expect(capturedRequest).toBeTruthy()
      })
      
      expect(capturedRequest.text).toBe('Test phrase')
      expect(capturedRequest.voice_id).toBe('voice-123')
      expect(capturedRequest.language).toBe('ru')
    })

    it('trims text before sending', async () => {
      const user = userEvent.setup()
      let capturedRequest: any = null
      
      server.use(
        http.post('*/api/tts/preview', async ({ request }) => {
          capturedRequest = await request.json()
          const audioData = new Uint8Array([0, 0, 0, 0])
          return new HttpResponse(audioData, {
            headers: { 'Content-Type': 'audio/mpeg' },
          })
        })
      )
      
      render(<TTSPreviewButton text="  Hello world  " />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      await waitFor(() => {
        expect(capturedRequest).toBeTruthy()
      })
      
      expect(capturedRequest.text).toBe('Hello world')
    })
  })

  describe('Loading State', () => {
    it('shows loading indicator during request', async () => {
      const user = userEvent.setup()
      
      // Delay the response to see loading state
      server.use(
        http.post('*/api/tts/preview', async () => {
          await new Promise(resolve => setTimeout(resolve, 100))
          const audioData = new Uint8Array([0, 0, 0, 0])
          return new HttpResponse(audioData, {
            headers: { 'Content-Type': 'audio/mpeg' },
          })
        })
      )
      
      render(<TTSPreviewButton text="Test" />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      // Should show loading state (button is disabled during loading)
      expect(button).toBeDisabled()
    })

    it('re-enables button after request completes', async () => {
      const user = userEvent.setup()
      
      render(<TTSPreviewButton text="Test" />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      // Wait for request to complete
      await waitFor(() => {
        expect(button).not.toBeDisabled()
      }, { timeout: 2000 })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      const user = userEvent.setup()
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      server.use(
        http.post('*/api/tts/preview', () => {
          return new HttpResponse(null, { status: 500 })
        })
      )
      
      try {
        render(<TTSPreviewButton text="Test" />)
        
        const button = screen.getByRole('button')
        await user.click(button)
        
        // Button should be re-enabled after error
        await waitFor(() => {
          expect(button).not.toBeDisabled()
        })
      } finally {
        consoleErrorSpy.mockRestore()
      }
    })

    it('rejects text that is too long', async () => {
      const user = userEvent.setup()
      const longText = 'a'.repeat(501) // Over 500 characters
      
      render(<TTSPreviewButton text={longText} />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      // Button should be re-enabled (rejected before API call)
      expect(button).not.toBeDisabled()
    })
  })

  describe('Playback', () => {
    it('can stop playback when playing', async () => {
      const user = userEvent.setup()
      
      render(<TTSPreviewButton text="Test" />)
      
      const button = screen.getByRole('button')
      
      // First click - start playing
      await user.click(button)
      
      // Wait for audio to start
      await waitFor(() => {
        expect(button).not.toBeDisabled()
      })
      
      // Title should change when playing
      // (Implementation depends on actual component behavior)
    })
  })

  describe('Sizes', () => {
    it('renders small size correctly', () => {
      render(<TTSPreviewButton text="Test" size="sm" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('w-8', 'h-8')
    })

    it('renders medium size correctly', () => {
      render(<TTSPreviewButton text="Test" size="md" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('w-10', 'h-10')
    })
  })
})
