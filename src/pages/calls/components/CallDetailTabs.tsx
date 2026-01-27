import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { 
  Call, 
  TranscriptMessage, 
  CallAgreement, 
  CallSession, 
  ContactInfo, 
  TransferStatus, 
  LeadTransfer 
} from '@new-voice/types'
import { Button } from '@new-voice/ui'

interface CallDetailTabsProps {
  call: Call
  transcript?: TranscriptMessage[]
  agreements?: CallAgreement[]
  session?: CallSession
  contactInfo?: ContactInfo
  transferStatus?: TransferStatus
  leadTransfer?: LeadTransfer
}

type TabId = 'dialog' | 'agreements' | 'session' | 'contact' | 'transfer' | 'lead'

export function CallDetailTabs({
  call,
  transcript = [],
  agreements = [],
  session,
  contactInfo,
  transferStatus,
  leadTransfer,
}: CallDetailTabsProps) {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabId>('dialog')

  const tabs: { id: TabId; label: string }[] = [
    { id: 'dialog', label: 'Dialog History' },
    { id: 'agreements', label: 'Agreements' },
    { id: 'session', label: 'Call Session' },
    { id: 'contact', label: 'Contact Info' },
    { id: 'transfer', label: 'Transfer Status' },
    { id: 'lead', label: 'Lead Transfer' },
  ]

  const EmptyState = ({ message }: { message: string }) => (
    <div className="text-center py-12">
      <svg className="w-12 h-12 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
      <p className="text-gray-500 text-sm">{message}</p>
    </div>
  )

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const renderDialogHistory = () => {
    if (transcript.length === 0) {
      return <EmptyState message="No dialog history available" />
    }

    return (
      <div className="space-y-4">
        {/* Link to skillbase */}
        {call.skillbase_id && (
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/skillbases/${call.skillbase_id}`)}
              className="flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              View Skillbase
            </Button>
          </div>
        )}

        {/* Messages */}
        <div className="space-y-3">
          {transcript.map((message, index) => (
            <div
              key={message.id || index}
              className={`flex gap-2 sm:gap-3 ${message.role === 'assistant' ? 'flex-row' : 'flex-row-reverse'}`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'assistant'
                    ? 'bg-indigo-100 text-indigo-600'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {message.role === 'assistant' ? (
                  <span className="text-xs font-bold">AI</span>
                ) : (
                  <span className="text-xs font-bold">C</span>
                )}
              </div>

              {/* Message bubble - wider on mobile */}
              <div
                className={`max-w-[85%] sm:max-w-[70%] rounded-lg px-3 sm:px-4 py-2 ${
                  message.role === 'assistant'
                    ? 'bg-indigo-50 text-gray-900'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm break-words">{message.content}</p>
                <span className="text-xs text-gray-400 mt-1 block">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderAgreements = () => {
    if (agreements.length === 0) {
      return <EmptyState message="No agreements recorded for this call" />
    }

    return (
      <div className="space-y-4">
        {agreements.map((agreement, index) => (
          <div key={agreement.id || index} className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-900">{agreement.description}</p>
            {agreement.value && (
              <p className="text-sm text-gray-600 mt-2">{agreement.value}</p>
            )}
            <span className="text-xs text-gray-400 mt-2 block">
              {formatTimestamp(agreement.created_at)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  const renderSession = () => {
    if (!session) {
      return <EmptyState message="No session details available" />
    }

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-500">Session ID</span>
            <p className="text-sm font-mono text-gray-900 mt-1 break-all">{session.session_id}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Provider</span>
            <p className="text-sm font-medium text-gray-900 mt-1">{session.provider}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">Start Time</span>
            <p className="text-sm font-medium text-gray-900 mt-1">{formatTimestamp(session.start_time)}</p>
          </div>
          <div>
            <span className="text-sm text-gray-500">End Time</span>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {session.end_time ? formatTimestamp(session.end_time) : '\u2014'}
            </p>
          </div>
          {session.quality_score !== undefined && (
            <div>
              <span className="text-sm text-gray-500">Quality Score</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{session.quality_score}%</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderContactInfo = () => {
    if (!contactInfo || (!contactInfo.name && !contactInfo.email && !contactInfo.company)) {
      return <EmptyState message="No contact information available" />
    }

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="space-y-3">
          {contactInfo.name && (
            <div>
              <span className="text-sm text-gray-500">Name</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{contactInfo.name}</p>
            </div>
          )}
          {contactInfo.email && (
            <div>
              <span className="text-sm text-gray-500">Email</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{contactInfo.email}</p>
            </div>
          )}
          {contactInfo.company && (
            <div>
              <span className="text-sm text-gray-500">Company</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{contactInfo.company}</p>
            </div>
          )}
          {contactInfo.notes && (
            <div>
              <span className="text-sm text-gray-500">Notes</span>
              <p className="text-sm text-gray-900 mt-1">{contactInfo.notes}</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderTransferStatus = () => {
    if (!transferStatus || !transferStatus.transferred) {
      return <EmptyState message="No transfer was made during this call" />
    }

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="space-y-3">
          <div>
            <span className="text-sm text-gray-500">Transfer Status</span>
            <p className="text-sm font-medium text-green-600 mt-1">Transferred successfully</p>
          </div>
          {transferStatus.transfer_to && (
            <div>
              <span className="text-sm text-gray-500">Transferred To</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{transferStatus.transfer_to}</p>
            </div>
          )}
          {transferStatus.transfer_time && (
            <div>
              <span className="text-sm text-gray-500">Transfer Time</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{formatTimestamp(transferStatus.transfer_time)}</p>
            </div>
          )}
          {transferStatus.transfer_reason && (
            <div>
              <span className="text-sm text-gray-500">Transfer Reason</span>
              <p className="text-sm text-gray-900 mt-1">{transferStatus.transfer_reason}</p>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderLeadTransfer = () => {
    if (!leadTransfer || !leadTransfer.transferred) {
      return <EmptyState message="No lead was transferred from this call" />
    }

    return (
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="space-y-3">
          <div>
            <span className="text-sm text-gray-500">Lead Status</span>
            <p className="text-sm font-medium text-green-600 mt-1">Lead transferred successfully</p>
          </div>
          {leadTransfer.lead_id && (
            <div>
              <span className="text-sm text-gray-500">Lead ID</span>
              <p className="text-sm font-mono text-gray-900 mt-1">{leadTransfer.lead_id}</p>
            </div>
          )}
          {leadTransfer.transferred_at && (
            <div>
              <span className="text-sm text-gray-500">Transferred At</span>
              <p className="text-sm font-medium text-gray-900 mt-1">{formatTimestamp(leadTransfer.transferred_at)}</p>
            </div>
          )}
          {leadTransfer.fields && Object.keys(leadTransfer.fields).length > 0 && (
            <div>
              <span className="text-sm text-gray-500">Lead Fields</span>
              <div className="mt-2 space-y-2">
                {Object.entries(leadTransfer.fields).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-sm text-gray-600">{key}:</span>
                    <span className="text-sm font-medium text-gray-900">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dialog':
        return renderDialogHistory()
      case 'agreements':
        return renderAgreements()
      case 'session':
        return renderSession()
      case 'contact':
        return renderContactInfo()
      case 'transfer':
        return renderTransferStatus()
      case 'lead':
        return renderLeadTransfer()
      default:
        return null
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Tab Navigation - scrollable on mobile */}
      <div className="border-b border-gray-200 overflow-x-auto scrollbar-hide">
        <nav className="flex -mb-px min-w-max" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`whitespace-nowrap border-b-2 py-3 sm:py-4 px-4 sm:px-6 text-xs sm:text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content - responsive padding */}
      <div className="p-4 sm:p-6">
        {renderTabContent()}
      </div>
    </div>
  )
}
