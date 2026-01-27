import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Call } from '@new-voice/types'
import { Button, Badge } from '@new-voice/ui'
import { AudioPlayer } from '../../../components/audio/AudioPlayer'

interface CallDetailHeaderProps {
  call: Call
  onReport?: () => void
}

export function CallDetailHeader({ call, onReport }: CallDetailHeaderProps) {
  const navigate = useNavigate()
  const [showPlayer, setShowPlayer] = useState(false)

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
      pending: { variant: 'secondary', label: 'Pending' },
      in_progress: { variant: 'default', label: 'In Progress' },
      completed: { variant: 'default', label: 'Completed' },
      failed: { variant: 'destructive', label: 'Failed' },
      no_answer: { variant: 'outline', label: 'No Answer' },
      busy: { variant: 'outline', label: 'Busy' },
    }
    const config = statusConfig[status] || { variant: 'secondary' as const, label: status }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const getDirectionBadge = (direction?: string) => {
    if (!direction) return null
    const isInbound = direction === 'inbound'
    return (
      <Badge variant="outline" className="flex items-center gap-1">
        {isInbound ? (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
        ) : (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 3h5m0 0v5m0-5l-6 6M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.28 3H5z" />
          </svg>
        )}
        {isInbound ? 'Inbound' : 'Outbound'}
      </Badge>
    )
  }

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      {/* Top row with back button and actions */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span className="text-sm font-medium">Back to list</span>
        </button>

        <button
          onClick={onReport}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Report issue
        </button>
      </div>

      {/* Call title and badges */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-gray-900">
              Call {call.phone_number}
            </h1>
            {getDirectionBadge(call.direction)}
            {getStatusBadge(call.status)}
          </div>
          
          <p className="text-sm text-gray-500">
            {call.started_at && new Date(call.started_at).toLocaleString('ru-RU', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </p>
        </div>

        {/* Recording button */}
        <Button
          onClick={() => setShowPlayer(!showPlayer)}
          variant={showPlayer ? 'secondary' : 'default'}
          disabled={!call.recording_url}
          className="flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
          </svg>
          {showPlayer ? 'Hide recording' : 'Listen to recording'}
        </Button>
      </div>

      {/* Audio Player */}
      {showPlayer && call.recording_url && (
        <div className="mt-4">
          <AudioPlayer
            src={call.recording_url}
            title={`Recording - ${call.phone_number}`}
          />
        </div>
      )}
    </div>
  )
}
