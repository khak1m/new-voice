import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { campaignsClient } from '@new-voice/api-client'
import { Button, Dialog } from '@new-voice/ui'
import { CampaignEditor } from './components/CampaignEditor'
import { CallListUpload } from './components/CallListUpload'
import toast from 'react-hot-toast'

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)

  const { data: campaign, isLoading, error } = useQuery({
    queryKey: ['campaigns', id],
    queryFn: async () => {
      const response = await campaignsClient.get(id!)
      return response.data
    },
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => campaignsClient.delete(id!),
    onSuccess: () => {
      toast.success('Campaign deleted successfully')
      navigate('/campaigns')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete campaign')
    },
  })

  const startMutation = useMutation({
    mutationFn: () => campaignsClient.start(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', id] })
      toast.success('Campaign started successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start campaign')
    },
  })

  const pauseMutation = useMutation({
    mutationFn: () => campaignsClient.pause(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', id] })
      toast.success('Campaign paused successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to pause campaign')
    },
  })

  const resumeMutation = useMutation({
    mutationFn: () => campaignsClient.resume(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', id] })
      toast.success('Campaign resumed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to resume campaign')
    },
  })

  const stopMutation = useMutation({
    mutationFn: () => campaignsClient.stop(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', id] })
      toast.success('Campaign stopped successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to stop campaign')
    },
  })

  if (isLoading) {
    return <div className="p-6">Loading campaign...</div>
  }

  if (error || !campaign) {
    return <div className="p-6 text-red-500">Error loading campaign</div>
  }

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

  const canStart = campaign.status === 'draft' || campaign.status === 'scheduled'
  const canPause = campaign.status === 'running'
  const canResume = campaign.status === 'paused'
  const canStop = campaign.status === 'running' || campaign.status === 'paused'

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold">{campaign.name}</h1>
            <span className={`px-3 py-1 rounded text-sm font-medium ${getStatusColor(campaign.status)}`}>
              {campaign.status}
            </span>
          </div>
          {campaign.description && (
            <p className="text-gray-600">{campaign.description}</p>
          )}
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/campaigns')}>
            Back
          </Button>
          {!isEditing && (
            <>
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowDeleteDialog(true)}
                className="text-red-600 hover:text-red-700"
              >
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-2 mb-6">
        {canStart && (
          <Button
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
            className="bg-green-600 hover:bg-green-700"
          >
            {startMutation.isPending ? 'Starting...' : 'Start Campaign'}
          </Button>
        )}
        {canPause && (
          <Button
            onClick={() => pauseMutation.mutate()}
            disabled={pauseMutation.isPending}
            className="bg-yellow-600 hover:bg-yellow-700"
          >
            {pauseMutation.isPending ? 'Pausing...' : 'Pause Campaign'}
          </Button>
        )}
        {canResume && (
          <Button
            onClick={() => resumeMutation.mutate()}
            disabled={resumeMutation.isPending}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {resumeMutation.isPending ? 'Resuming...' : 'Resume Campaign'}
          </Button>
        )}
        {canStop && (
          <Button
            onClick={() => stopMutation.mutate()}
            disabled={stopMutation.isPending}
            variant="outline"
            className="text-red-600 hover:text-red-700"
          >
            {stopMutation.isPending ? 'Stopping...' : 'Stop Campaign'}
          </Button>
        )}
        <Button
          variant="outline"
          onClick={() => setShowUploadDialog(true)}
        >
          Upload Call List
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Total Tasks</div>
          <div className="text-2xl font-bold">{campaign.total_tasks || 0}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Completed</div>
          <div className="text-2xl font-bold text-green-600">{campaign.completed_tasks || 0}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Failed</div>
          <div className="text-2xl font-bold text-red-600">{campaign.failed_tasks || 0}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-500 mb-1">Success Rate</div>
          <div className="text-2xl font-bold">
            {campaign.total_tasks > 0
              ? Math.round((campaign.completed_tasks / campaign.total_tasks) * 100)
              : 0}
            %
          </div>
        </div>
      </div>

      {/* Editor or Details */}
      {isEditing ? (
        <CampaignEditor
          campaign={campaign}
          onCancel={() => setIsEditing(false)}
          onSave={() => setIsEditing(false)}
        />
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Campaign Details</h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-500">Daily Start Time</div>
              <div className="font-medium">{campaign.daily_start_time}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Daily End Time</div>
              <div className="font-medium">{campaign.daily_end_time}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Timezone</div>
              <div className="font-medium">{campaign.timezone}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Max Concurrent Calls</div>
              <div className="font-medium">{campaign.max_concurrent_calls}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Calls Per Minute</div>
              <div className="font-medium">{campaign.calls_per_minute}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Max Retries</div>
              <div className="font-medium">{campaign.max_retries}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Retry Delay</div>
              <div className="font-medium">{campaign.retry_delay_minutes} minutes</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Created</div>
              <div className="font-medium">{new Date(campaign.created_at).toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <div className="bg-white rounded-lg p-6 max-w-md">
          <h2 className="text-xl font-bold mb-4">Delete Campaign</h2>
          <p className="text-gray-600 mb-6">
            Are you sure you want to delete this campaign? This action cannot be undone and will delete all associated call tasks.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Dialog>

      {/* Upload Dialog */}
      {showUploadDialog && (
        <CallListUpload
          campaignId={id!}
          onClose={() => setShowUploadDialog(false)}
        />
      )}
    </div>
  )
}
