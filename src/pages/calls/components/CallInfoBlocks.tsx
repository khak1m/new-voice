import type { Call } from '@new-voice/types'
import { Badge } from '@new-voice/ui'

interface CallInfoBlocksProps {
  call: Call
}

export function CallInfoBlocks({ call }: CallInfoBlocksProps) {
  // Format time as DD.MM.YYYY HH:MM:SS
  const formatDateTime = (dateString?: string): string => {
    if (!dateString) return '\u2014'
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  // Format duration as MM:SS
  const formatDuration = (seconds?: number): string => {
    if (seconds === undefined || seconds === null) return '\u2014'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      pending: 'Pending',
      in_progress: 'In Progress',
      completed: 'Completed',
      failed: 'Failed',
      no_answer: 'No Answer',
      busy: 'Busy',
    }
    return labels[status] || status
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
      {/* Basic Info Block */}
      <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Basic Information
        </h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Phone</span>
            <span className="text-sm font-medium text-gray-900">{call.phone_number}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Status</span>
            <Badge variant={call.status === 'completed' ? 'default' : call.status === 'failed' ? 'destructive' : 'secondary'}>
              {getStatusLabel(call.status)}
            </Badge>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Type</span>
            <Badge variant="outline" className="flex items-center gap-1">
              {call.direction === 'inbound' ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  Inbound
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 3h5m0 0v5m0-5l-6 6M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.28 3H5z" />
                  </svg>
                  Outbound
                </>
              )}
            </Badge>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Agreement</span>
            <Badge variant={call.agreement ? 'default' : 'secondary'}>
              {call.agreement ? 'Yes' : 'No'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Time Metrics Block */}
      <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Time Metrics
        </h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Started</span>
            <span className="text-sm font-medium text-gray-900 tabular-nums">
              {formatDateTime(call.started_at)}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Connected</span>
            <span className="text-sm font-medium text-gray-900 tabular-nums">
              {formatDateTime(call.connected_at)}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Ended</span>
            <span className="text-sm font-medium text-gray-900 tabular-nums">
              {formatDateTime(call.ended_at)}
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Duration</span>
            <span className="text-sm font-medium text-gray-900 tabular-nums">
              {formatDuration(call.duration)}
            </span>
          </div>
        </div>
      </div>

      {/* Completion Details Block */}
      <div className="bg-white rounded-lg border border-gray-200 p-3 sm:p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Completion Details
        </h3>
        
        <div className="space-y-3">
          <div>
            <span className="text-sm text-gray-500">Completion Reason</span>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {call.completion_reason || '\u2014'}
            </p>
          </div>
          
          <div>
            <span className="text-sm text-gray-500">Rejection Reason</span>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {call.rejection_reason || '\u2014'}
            </p>
          </div>
          
          <div>
            <span className="text-sm text-gray-500">Outcome</span>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {call.outcome || '\u2014'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
