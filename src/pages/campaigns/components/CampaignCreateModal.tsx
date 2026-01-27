import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { campaignsClient, skillbasesClient } from '@new-voice/api-client'
import { Dialog, Button } from '@new-voice/ui'
import { createCampaignSchema, type CreateCampaignInput } from '../../../schemas/campaign-schemas'
import { FormInput } from '../../../components/FormInput'
import { NativeSelect } from '../../../components/NativeSelect'
import toast from 'react-hot-toast'
import type { Skillbase } from '@new-voice/types'

interface CampaignCreateModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CampaignCreateModal({ isOpen, onClose }: CampaignCreateModalProps) {
  const queryClient = useQueryClient()

  // Fetch skillbases for dropdown
  const { data: skillbasesData } = useQuery({
    queryKey: ['skillbases'],
    queryFn: () => skillbasesClient.list(),
    enabled: isOpen,
  })

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CreateCampaignInput>({
    resolver: zodResolver(createCampaignSchema),
    defaultValues: {
      daily_start_time: '09:00',
      daily_end_time: '18:00',
      timezone: 'UTC',
      max_concurrent_calls: 5,
      calls_per_minute: 10,
      max_retries: 3,
      retry_delay_minutes: 30,
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: CreateCampaignInput) => {
      // Get company_id from first skillbase (in real app, this would come from auth context)
      const companyId = skillbasesData?.items[0]?.company_id || '00000000-0000-0000-0000-000000000000'
      
      const response = await campaignsClient.create({
        ...data,
        company_id: companyId,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      toast.success('Campaign created successfully!')
      reset()
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create campaign')
    },
  })

  const onSubmit = (data: CreateCampaignInput) => {
    createMutation.mutate(data)
  }

  const handleClose = () => {
    reset()
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Create Campaign</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Basic Info */}
          <div>
            <FormInput
              label="Campaign Name"
              {...register('name')}
              error={errors.name?.message}
              placeholder="Enter campaign name"
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
              placeholder="Enter campaign description (optional)"
            />
          </div>

          <div>
            <NativeSelect
              label="Skillbase"
              {...register('skillbase_id')}
              error={errors.skillbase_id?.message}
            >
              <option value="">Select a skillbase</option>
              {skillbasesData?.items.map((skillbase: Skillbase) => (
                <option key={skillbase.id} value={skillbase.id}>
                  {skillbase.name}
                </option>
              ))}
            </NativeSelect>
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
                placeholder="UTC"
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
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Campaign'}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  )
}
