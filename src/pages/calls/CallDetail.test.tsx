import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, within } from '../../test/test-utils'
import userEvent from '@testing-library/user-event'
import { CallDetail } from './CallDetail'
import { server } from '../../test/setup'
import { http, HttpResponse } from 'msw'

// Mock useParams to return a call ID
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: 'test-call-id' }),
  }
})

describe('CallDetail Page', () => {
  describe('Data Fetching', () => {
    it('fetches and displays call data', async () => {
      render(<CallDetail />)
      
      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Call +7 999 123 4567')
      })
      
      // Check that call status is displayed
      expect(screen.getAllByText('Completed').length).toBeGreaterThan(0)
    })

    it('fetches and displays transcript', async () => {
      render(<CallDetail />)
      
      // Wait for transcript to load
      await waitFor(() => {
        expect(screen.getByText(/Hello, this is AI assistant/)).toBeInTheDocument()
      })
      
      // Check other messages
      expect(screen.getByText(/I want to know about your services/)).toBeInTheDocument()
      expect(screen.getByText(/We offer voice AI solutions/)).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows loading skeleton while fetching', async () => {
      // Delay the response
      server.use(
        http.get('*/api/calls/:id', async () => {
          await new Promise(resolve => setTimeout(resolve, 200))
          return HttpResponse.json({
            id: 'test-call-id',
            phone_number: '+7 999 123 4567',
            status: 'completed',
            direction: 'outbound',
          })
        })
      )
      
      render(<CallDetail />)
      
      // Should show loading state (skeleton)
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Error Handling', () => {
    it('shows error state when call not found (404)', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      server.use(
        http.get('*/api/calls/:id', () => {
          return new HttpResponse(null, { status: 404 })
        })
      )
      
      try {
        render(<CallDetail />)
        
        await waitFor(() => {
          expect(screen.getByText(/Call Not Found/i)).toBeInTheDocument()
        })
        
        // Should show helpful message
        expect(screen.getByText(/doesn't exist/i)).toBeInTheDocument()
      } finally {
        consoleErrorSpy.mockRestore()
      }
    })

    it('shows error state on network error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      server.use(
        http.get('*/api/calls/:id', () => {
          return HttpResponse.error()
        })
      )
      
      try {
        render(<CallDetail />)
        
        await waitFor(() => {
          expect(screen.getByText(/Call Not Found/i)).toBeInTheDocument()
        })
      } finally {
        consoleErrorSpy.mockRestore()
      }
    })
  })

  describe('Call Detail Header', () => {
    it('displays call phone number in title', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/Call.*\+7 999 123 4567/)
      })
    })

    it('displays direction badge', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Outbound').length).toBeGreaterThan(0)
      })
    })

    it('displays status badge', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Completed').length).toBeGreaterThan(0)
      })
    })

    it('has back button that navigates', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Call +7 999 123 4567')
      })
      
      // Find back button (contains arrow icon or "Back" text)
      const backButton = screen.getByText('Back to list').closest('button')
      expect(backButton).not.toBeNull()
    })
  })

  describe('Info Blocks', () => {
    it('displays basic information block', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByText('Basic Information')).toBeInTheDocument()
      })
      
      // Should show phone
      expect(screen.getByText('Phone')).toBeInTheDocument()
    })

    it('displays time metrics block', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByText('Time Metrics')).toBeInTheDocument()
      })
      
      // Should show duration
      expect(screen.getByText('Duration')).toBeInTheDocument()
    })

    it('displays completion details block', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByText('Completion Details')).toBeInTheDocument()
      })
    })

    it('formats duration as MM:SS', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        // 120 seconds = 02:00
        expect(screen.getByText('02:00')).toBeInTheDocument()
      })
    })

    it('displays em-dash for null values', async () => {
      server.use(
        http.get('*/api/calls/:id', () => {
          return HttpResponse.json({
            id: 'test-call-id',
            phone_number: '+7 999 123 4567',
            status: 'completed',
            direction: 'outbound',
            duration: null,
            completion_reason: null,
          })
        })
      )
      
      render(<CallDetail />)
      
      await waitFor(() => {
        const emDashes = screen.getAllByText('—')
        expect(emDashes.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Tabs', () => {
    it('shows dialog history tab by default', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        const dialogTab = screen.getByRole('tab', { name: /Dialog History/i })
        expect(dialogTab).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('can switch between tabs', async () => {
      const user = userEvent.setup()
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByText('Dialog History')).toBeInTheDocument()
      })
      
      // Click on Agreements tab
      const agreementsTab = screen.getByRole('tab', { name: /Agreements/i })
      await user.click(agreementsTab)
      
      // Should show empty state for agreements
      expect(screen.getByText(/No agreements/i)).toBeInTheDocument()
    })

    it('displays transcript messages in dialog tab', async () => {
      render(<CallDetail />)
      
      await waitFor(() => {
        // Check for AI message
        expect(screen.getAllByText('AI').length).toBeGreaterThan(0)
        // Check for Client indicator
        expect(screen.getAllByText('C').length).toBeGreaterThan(0)
      })
    })

    it('shows empty state when no transcript', async () => {
      server.use(
        http.get('*/api/calls/:id/transcript', () => {
          return HttpResponse.json({ messages: [] })
        })
      )
      
      render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByText(/No dialog history/i)).toBeInTheDocument()
      })
    })
  })

  describe('Recording', () => {
    it('shows recording button when recording URL exists', async () => {
      server.use(
        http.get('*/api/calls/:id', () => {
          return HttpResponse.json({
            id: 'test-call-id',
            phone_number: '+7 999 123 4567',
            status: 'completed',
            direction: 'outbound',
            recording_url: 'http://example.com/recording.mp3',
          })
        })
      )
      
      render(<CallDetail />)
      
      await waitFor(() => {
        const recordingButton = screen.getByRole('button', { name: /recording/i })
        expect(recordingButton).not.toBeDisabled()
      })
    })

    it('disables recording button when no recording', async () => {
      server.use(
        http.get('*/api/calls/:id', () => {
          return HttpResponse.json({
            id: 'test-call-id',
            phone_number: '+7 999 123 4567',
            status: 'completed',
            direction: 'outbound',
            recording_url: null,
          })
        })
      )
      
      render(<CallDetail />)
      
      await waitFor(() => {
        const recordingButton = screen.getByRole('button', { name: /recording/i })
        expect(recordingButton).toBeDisabled()
      })
    })
  })

  describe('Caching', () => {
    it('uses cached data on subsequent renders', async () => {
      let fetchCount = 0
      
      server.use(
        http.get('*/api/calls/:id', () => {
          fetchCount++
          return HttpResponse.json({
            id: 'test-call-id',
            phone_number: '+7 999 123 4567',
            status: 'completed',
            direction: 'outbound',
          })
        })
      )
      
      const { rerender } = render(<CallDetail />)
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Call +7 999 123 4567')
      })
      
      // Rerender the component
      rerender(<CallDetail />)
      
      // Should still show the data (from cache)
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Call +7 999 123 4567')
      
      // Should only have fetched once (due to caching with staleTime)
      expect(fetchCount).toBe(1)
    })
  })
})
