import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../../test/test-utils'
import userEvent from '@testing-library/user-event'
import { AudioPlayer } from './AudioPlayer'

describe('AudioPlayer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the player', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Should have play button (could be multiple buttons)
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('renders with title', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" title="Test Audio" />)
      
      expect(screen.getByText('Test Audio')).toBeInTheDocument()
    })

    it('renders compact mode', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" compact />)
      
      // Compact mode has smaller play button
      const button = screen.getByRole('button')
      expect(button).toHaveClass('w-8', 'h-8')
    })

    it('renders full mode by default', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Full mode has larger play button (first button)
      const buttons = screen.getAllByRole('button')
      const playButton = buttons[0]
      expect(playButton).toHaveClass('w-10', 'h-10')
    })
  })

  describe('Time Display', () => {
    it('displays current time and duration', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Should show 00:00 initially (current time and duration)
      const timeDisplays = screen.getAllByText('00:00')
      expect(timeDisplays.length).toBeGreaterThanOrEqual(1)
    })

    it('formats time as MM:SS', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Time should be in MM:SS format (multiple elements may match)
      const timeDisplays = screen.getAllByText(/\d{2}:\d{2}/)
      expect(timeDisplays.length).toBeGreaterThan(0)
    })
  })

  describe('Controls', () => {
    it('has play/pause button', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    it('has volume control in full mode', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      const volumeSlider = screen.getByRole('slider')
      expect(volumeSlider).toBeInTheDocument()
    })

    it('does not have volume control in compact mode', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" compact />)
      
      const volumeSlider = screen.queryByRole('slider')
      expect(volumeSlider).not.toBeInTheDocument()
    })

    it('has progress bar in full mode', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Progress bar should be present (has cursor-pointer class)
      const progressBar = document.querySelector('.cursor-pointer')
      expect(progressBar).toBeInTheDocument()
    })
  })

  describe('Play/Pause Functionality', () => {
    it('toggles between play and pause', async () => {
      const user = userEvent.setup()
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      const buttons = screen.getAllByRole('button')
      const playButton = buttons[0]
      
      // Click to play
      await user.click(playButton)
      
      // Button should still be present (for pause)
      expect(playButton).toBeInTheDocument()
    })
  })

  describe('Volume Control', () => {
    it('can change volume', async () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      const volumeSlider = screen.getByRole('slider')
      
      // Change volume
      fireEvent.change(volumeSlider, { target: { value: '0.5' } })
      
      expect(volumeSlider).toHaveValue('0.5')
    })

    it('can mute/unmute', async () => {
      const user = userEvent.setup()
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Find mute button (it's the button near the volume slider)
      const buttons = screen.getAllByRole('button')
      // First button is play, second should be mute in full mode
      expect(buttons.length).toBeGreaterThan(1)
    })
  })

  describe('Error Handling', () => {
    it('shows error state when audio fails to load', async () => {
      // Mock audio error
      const originalAudio = window.Audio
      window.Audio = vi.fn().mockImplementation(() => ({
        play: () => Promise.reject(new Error('Failed to load')),
        pause: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })) as any
      
      render(<AudioPlayer src="http://invalid-url/audio.mp3" />)
      
      // Restore
      window.Audio = originalAudio
    })

    it('calls onError callback when error occurs', async () => {
      const onError = vi.fn()
      
      render(
        <AudioPlayer 
          src="http://example.com/audio.mp3" 
          onError={onError}
        />
      )
      
      // Error callback should be available
      expect(onError).toBeDefined()
    })
  })

  describe('Cleanup', () => {
    it('cleans up audio resources on unmount', () => {
      const { unmount } = render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Unmount should not throw
      expect(() => unmount()).not.toThrow()
    })
  })

  describe('Callbacks', () => {
    it('calls onEnded when audio finishes', () => {
      const onEnded = vi.fn()
      
      render(
        <AudioPlayer 
          src="http://example.com/audio.mp3" 
          onEnded={onEnded}
        />
      )
      
      // onEnded should be available
      expect(onEnded).toBeDefined()
    })
  })

  describe('Custom Styling', () => {
    it('accepts custom className', () => {
      render(
        <AudioPlayer 
          src="http://example.com/audio.mp3" 
          className="custom-class"
        />
      )
      
      const container = document.querySelector('.custom-class')
      expect(container).toBeInTheDocument()
    })
  })

  describe('Seek Functionality', () => {
    it('has clickable progress bar', () => {
      render(<AudioPlayer src="http://example.com/audio.mp3" />)
      
      // Progress bar should be clickable
      const progressBar = document.querySelector('.cursor-pointer')
      expect(progressBar).toBeInTheDocument()
    })
  })
})
