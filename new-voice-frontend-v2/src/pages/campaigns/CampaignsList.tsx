import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { campaignsClient } from '@new-voice/api-client'
import { Button } from '@new-voice/ui'
import { CampaignCreateModal } from './components/CampaignCreateModal'

export function CampaignsList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const response = await campaignsClient.list()
      return response.data
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800'
      case 'paused':
        return 'bg-yellow-100 text-yellow-800'
      case 'completed':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'scheduled':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Campaigns</h1>
        </div>
        <div className="text-gray-500">Loading campaigns...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <Button onClick={() => setIsCreateModalOpen(true)}>Create Campaign</Button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Campaigns</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Unable to connect to the backend server. Please make sure the API is running at{' '}
            <code className="bg-red-100 px-2 py-1 rounded text-sm">http://77.233.212.58:8000</code>
          </p>
          <div className="flex gap-3 justify-center">
            <Button 
              onClick={() => queryClient.invalidateQueries({ queryKey: ['campaigns'] })}
              variant="outline"
            >
              Try Again
            </Button>
            <Button 
              onClick={() => window.open('http://77.233.212.58:8000/docs', '_blank')}
              variant="outline"
            >
              Check API Status
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Error: {(error as Error).message}
          </p>
        </div>

        <CampaignCreateModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Campaigns</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create Campaign</Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.items.map((campaign) => (
            <div
              key={campaign.id}
              onClick={() => navigate(`/campaigns/${campaign.id}`)}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold">{campaign.name}</h3>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(campaign.status)}`}>
                  {campaign.status}
                </span>
              </div>

              {campaign.description && (
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">{campaign.description}</p>
              )}

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Tasks:</span>
                  <span className="font-medium">{campaign.total_tasks || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Completed:</span>
                  <span className="font-medium text-green-600">{campaign.completed_tasks || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Failed:</span>
                  <span className="font-medium text-red-600">{campaign.failed_tasks || 0}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  Created: {new Date(campaign.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">No campaigns yet</p>
          <Button onClick={() => setIsCreateModalOpen(true)}>Create Your First Campaign</Button>
        </div>
      )}

      <CampaignCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}
