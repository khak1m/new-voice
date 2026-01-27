import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { campaignsClient } from '@new-voice/api-client'
import { Button } from '@new-voice/ui'
import { updateCampaignSchema, type UpdateCampaignInput } from '../../../schemas/campaign-schemas'
import { FormInput } from '../../../components/FormInput'
import toast from 'react-hot-toast'
import type { Campaign } from '@new-voice/types'

interface CampaignEditorProps {
  campaign: Campaign
  onCancel: () => void
  onSave: () => void
}

export function CampaignEditor({ campaign, onCancel, onSave }: CampaignEditorProps) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<UpdateCampaignInput>({
    resolver: zodResolver(updateCampaignSchema),
    defaultValues: {
      name: campaign.name,
      description: campaign.description || '',
      daily_start_time: campaign.daily_start_time,
      daily_end_time: campaign.daily_end_time,
      timezone: campaign.timezone,
      max_concurrent_calls: campaign.max_concurrent_calls,
      calls_per_minute: campaign.calls_per_minute,
      max_retries: campaign.max_retries,
      retry_delay_minutes: campaign.retry_delay_minutes,
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (data: UpdateCampaignInput) => {
      const response = await campaignsClient.update(campaign.id, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', campaign.id] })
      toast.success('Campaign updated successfully!')
      onSave()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update campaign')
    },
  })

  const onSubmit = (data: UpdateCampaignInput) => {
    updateMutation.mutate(data)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {isDirty && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">You have unsaved changes</p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Basic Info */}
        <div>
          <FormInput
            label="Campaign Name"
            {...register('name')}
            error={errors.name?.message}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            {...register('description')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
          />
        </div>

        {/* Scheduling */}
        <div className="border-t pt-4">
          <h3 className="font-semibold mb-3">Schedule</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <FormInput
              label="Daily Start Time"
              type="time"
              {...register('daily_start_time')}
              error={errors.daily_start_time?.message}
            />

            <FormInput
              label="Daily End Time"
              type="time"
              {...register('daily_end_time')}
              error={errors.daily_end_time?.message}
            />
          </div>

          <div className="mt-4">
            <FormInput
              label="Timezone"
              {...register('timezone')}
              error={errors.timezone?.message}
            />
          </div>
        </div>

        {/* Rate Limiting */}
        <div className="border-t pt-4">
          <h3 className="font-semibold mb-3">Rate Limiting</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <FormInput
              label="Max Concurrent Calls"
              type="number"
              {...register('max_concurrent_calls', { valueAsNumber: true })}
              error={errors.max_concurrent_calls?.message}
            />

            <FormInput
              label="Calls Per Minute"
              type="number"
              {...register('calls_per_minute', { valueAsNumber: true })}
              error={errors.calls_per_minute?.message}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <FormInput
              label="Max Retries"
              type="number"
              {...register('max_retries', { valueAsNumber: true })}
              error={errors.max_retries?.message}
            />

            <FormInput
              label="Retry Delay (minutes)"
              type="number"
              {...register('retry_delay_minutes', { valueAsNumber: true })}
              error={errors.retry_delay_minutes?.message}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={updateMutation.isPending || !isDirty}>
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </div>
  )
}
