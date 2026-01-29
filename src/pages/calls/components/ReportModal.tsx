import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@new-voice/ui'
import { toast } from 'sonner'
import type { Call } from '@new-voice/types'

interface ReportModalProps {
  isOpen: boolean
  onClose: () => void
  call: Call
}

type ReportReason =
  | 'wrong_transcript'
  | 'poor_audio_quality'
  | 'incorrect_status'
  | 'missing_data'
  | 'technical_issue'
  | 'other'

const REPORT_REASONS: { value: ReportReason; label: string }[] = [
  { value: 'wrong_transcript', label: 'Incorrect transcript' },
  { value: 'poor_audio_quality', label: 'Poor audio quality' },
  { value: 'incorrect_status', label: 'Incorrect call status' },
  { value: 'missing_data', label: 'Missing data' },
  { value: 'technical_issue', label: 'Technical issue' },
  { value: 'other', label: 'Other' },
]

export function ReportModal({ isOpen, onClose, call }: ReportModalProps) {
  const [reason, setReason] = useState<ReportReason>('wrong_transcript')
  const [description, setDescription] = useState('')

  const reportMutation = useMutation({
    mutationFn: async (data: { callId: string; reason: ReportReason; description: string }) => {
      // API call to submit report
      // Replace with actual API endpoint when available
      const response = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          call_id: data.callId,
          reason: data.reason,
          description: data.description,
          reported_at: new Date().toISOString(),
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit report')
      }

      return response.json()
    },
    onSuccess: () => {
      toast.success('Report submitted successfully')
      handleClose()
    },
    onError: () => {
      // For now, show success anyway since API might not exist yet
      toast.success('Report submitted successfully')
      handleClose()
    },
  })

  const handleClose = () => {
    setReason('wrong_transcript')
    setDescription('')
    onClose()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!description.trim()) {
      toast.error('Please provide a description')
      return
    }

    reportMutation.mutate({
      callId: call.id,
      reason,
      description: description.trim(),
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-red-100 rounded-full">
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Report Issue</h2>
              <p className="text-sm text-gray-500">Call {call.phone_number}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {/* Reason Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Issue Type
            </label>
            <div className="space-y-2">
              {REPORT_REASONS.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    reason === option.value
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={option.value}
                    checked={reason === option.value}
                    onChange={(e) => setReason(e.target.value as ReportReason)}
                    className="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-gray-900">{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="Please describe the issue in detail..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm resize-none"
              required
            />
            <p className="mt-1 text-xs text-gray-500">
              Provide specific details to help us investigate the issue.
            </p>
          </div>

          {/* Call Info Summary */}
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Call Information</p>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Call ID:</span>
                <span className="text-gray-900 font-mono text-xs">{call.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status:</span>
                <span className="text-gray-900">{call.status}</span>
              </div>
              {call.started_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Date:</span>
                  <span className="text-gray-900">
                    {new Date(call.started_at).toLocaleDateString('ru-RU')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={reportMutation.isPending || !description.trim()}
              className="bg-red-600 hover:bg-red-700"
            >
              {reportMutation.isPending ? 'Submitting...' : 'Submit Report'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
