import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { callsClient } from '@new-voice/api-client'
import type { CallTranscript, TranscriptMessage } from '@new-voice/types'
import { CallDetailHeader } from './components/CallDetailHeader'
import { CallInfoBlocks } from './components/CallInfoBlocks'
import { CallDetailTabs } from './components/CallDetailTabs'
import { ReportModal } from './components/ReportModal'

export function CallDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)

  // Fetch call data
  const { 
    data: call, 
    isLoading: isLoadingCall, 
    error: callError 
  } = useQuery({
    queryKey: ['call', id],
    queryFn: () => callsClient.get(id!),
    enabled: !!id,
    staleTime: 30000, // Cache for 30 seconds
    select: (response) => response.data,
  })

  // Fetch transcript
  const { 
    data: transcript 
  } = useQuery({
    queryKey: ['call', id, 'transcript'],
    queryFn: () => callsClient.getTranscript(id!),
    enabled: !!id && !!call,
    staleTime: 60000, // Cache for 1 minute
    select: (response) => {
      const data = response.data as CallTranscript | TranscriptMessage[] | undefined
      return Array.isArray(data) ? data : data?.messages ?? []
    },
  })

  const handleReport = () => {
    setIsReportModalOpen(true)
  }

  // Loading state
  if (isLoadingCall) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="animate-pulse">
            <div className="h-4 w-24 bg-gray-200 rounded mb-4" />
            <div className="h-8 w-64 bg-gray-200 rounded mb-2" />
            <div className="h-4 w-48 bg-gray-200 rounded" />
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
                <div className="h-4 w-32 bg-gray-200 rounded mb-4" />
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="flex justify-between">
                      <div className="h-4 w-20 bg-gray-200 rounded" />
                      <div className="h-4 w-24 bg-gray-200 rounded" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
            <div className="h-10 bg-gray-200 rounded mb-4" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-200 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (callError || !call) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span className="text-sm font-medium">Back to list</span>
          </button>
        </div>
        
        <div className="p-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center max-w-lg mx-auto">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Call Not Found</h3>
            <p className="text-gray-600 mb-6">
              The call you're looking for doesn't exist or you don't have permission to view it.
            </p>
            <button
              onClick={() => navigate('/calls')}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Go to Calls List
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <CallDetailHeader call={call} onReport={handleReport} />

      {/* Content - responsive padding */}
      <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
        {/* Info Blocks */}
        <CallInfoBlocks call={call} />

        {/* Tabs */}
        <CallDetailTabs
          call={call}
          transcript={transcript || []}
          agreements={call.agreements || []}
          session={call.session}
          contactInfo={call.contact_info}
          transferStatus={call.transfer_status}
          leadTransfer={call.lead_transfer}
        />
      </div>

      {/* Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        call={call}
      />
    </div>
  )
}
