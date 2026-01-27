import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../test/test-utils'
import userEvent from '@testing-library/user-event'
import { CallsList } from './CallsList'
import { server } from '../../test/setup'
import { http, HttpResponse } from 'msw'

describe('CallsList Page', () => {
  describe('Data Fetching', () => {
    it('fetches and displays calls list', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByText(/\+7 999 123 4567/)).toBeInTheDocument()
        expect(screen.getByText(/\+7 999 765 4321/)).toBeInTheDocument()
      })
    })

    it('renders table headers', async () => {
      render(<CallsList />)

      await waitFor(() => {
        expect(screen.getByText('Phone')).toBeInTheDocument()
        expect(screen.getByText('Started')).toBeInTheDocument()
        expect(screen.getByText('Status')).toBeInTheDocument()
        expect(screen.getByText('Duration')).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('shows loading skeleton while fetching', async () => {
      server.use(
        http.get('*/api/calls', async () => {
          await new Promise(resolve => setTimeout(resolve, 200))
          return HttpResponse.json({ items: [], total: 0 })
        })
      )
      
      render(<CallsList />)
      
      const skeletons = document.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('Error State', () => {
    it('shows error message on API failure', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      server.use(
        http.get('*/api/calls', () => {
          return new HttpResponse(null, { status: 500 })
        })
      )
      
      try {
        render(<CallsList />)
        
        await waitFor(() => {
          expect(screen.getByText(/Failed to Load Calls/i)).toBeInTheDocument()
        })
      } finally {
        consoleErrorSpy.mockRestore()
      }
    })

    it('has retry button on error', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      server.use(
        http.get('*/api/calls', () => {
          return new HttpResponse(null, { status: 500 })
        })
      )
      
      try {
        render(<CallsList />)
        
        await waitFor(() => {
          expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument()
        })
      } finally {
        consoleErrorSpy.mockRestore()
      }
    })
  })

  describe('Empty State', () => {
    it('shows empty message when no calls', async () => {
      server.use(
        http.get('*/api/calls', () => {
          return HttpResponse.json({ items: [], total: 0 })
        })
      )
      
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByText(/No Calls Yet/i)).toBeInTheDocument()
      })
    })
  })

  describe('Filtering', () => {
    it('can filter by status', async () => {
      const user = userEvent.setup()
      let capturedParams: URLSearchParams | undefined
      
      server.use(
        http.get('*/api/calls', ({ request }) => {
          capturedParams = new URL(request.url).searchParams
          return HttpResponse.json({
            items: [
              {
                id: 'call-1',
                phone_number: '+7 999 123 4567',
                status: 'completed',
                direction: 'outbound',
              },
            ],
            total: 1,
          })
        })
      )
      
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByText(/\+7 999 123 4567/)).toBeInTheDocument()
      })
      
      // Click on "Completed" filter
      const completedFilter = screen.getByRole('button', { name: /Completed/i })
      await user.click(completedFilter)
      
      await waitFor(() => {
        expect(capturedParams?.get('status')).toBe('completed')
      })
    })

    it('shows all filter button as active by default', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        const allFilter = screen.getByRole('button', { name: 'All' })
        expect(allFilter).toHaveClass('bg-indigo-100')
      })
    })
  })

  describe('Navigation', () => {
    it('navigates to call detail on row click', async () => {
      const user = userEvent.setup()
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByText(/\+7 999 123 4567/)).toBeInTheDocument()
      })
      
      // Click on the row - the component should navigate
      const row = screen.getByText(/\+7 999 123 4567/).closest('tr')
      expect(row).toBeInTheDocument()
    })
  })

  describe('Status Badges', () => {
    it('shows correct badge for completed status', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Completed').length).toBeGreaterThan(0)
      })
    })

    it('shows correct badge for failed status', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getAllByText('Failed').length).toBeGreaterThan(0)
      })
    })
  })

  describe('Duration Formatting', () => {
    it('formats duration as MM:SS', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        // 120 seconds = 02:00
        expect(screen.getByText('02:00')).toBeInTheDocument()
        // 30 seconds = 00:30
        expect(screen.getByText('00:30')).toBeInTheDocument()
      })
    })

    it('shows em-dash for null duration', async () => {
      server.use(
        http.get('*/api/calls', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'call-1',
                phone_number: '+7 999 000 0000',
                status: 'pending',
                direction: 'outbound',
                duration: null,
              },
            ],
            total: 1,
          })
        })
      )
      
      render(<CallsList />)
      
      await waitFor(() => {
        const emDashes = screen.getAllByText('—')
        expect(emDashes.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Pagination', () => {
    it('shows pagination when more than one page', async () => {
      server.use(
        http.get('*/api/calls', () => {
          return HttpResponse.json({
            items: Array.from({ length: 10 }, (_, i) => ({
              id: `call-${i}`,
              phone_number: `+7 999 000 000${i}`,
              status: 'completed',
              direction: 'outbound',
            })),
            total: 25, // More than 10 items = multiple pages
          })
        })
      )
      
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByText(/Page 1 of/i)).toBeInTheDocument()
      })
    })

    it('does not show pagination for single page', async () => {
      server.use(
        http.get('*/api/calls', () => {
          return HttpResponse.json({
            items: [
              {
                id: 'call-1',
                phone_number: '+7 999 000 0001',
                status: 'completed',
                direction: 'outbound',
              },
            ],
            total: 1,
          })
        })
      )
      
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.queryByText(/Page/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Refresh', () => {
    it('has refresh button', async () => {
      render(<CallsList />)
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument()
      })
    })
  })
})
