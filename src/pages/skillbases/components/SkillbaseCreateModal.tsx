import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { skillbasesClient } from '@new-voice/api-client'
import { Button } from '@new-voice/ui'
import { FormInput } from '../../../components/FormInput'
import { createSkillbaseSchema, type CreateSkillbaseInput } from '../../../schemas/skillbase-schemas'
import { useCompanyId } from '../../../contexts/AuthContext'
import toast from 'react-hot-toast'

interface SkillbaseCreateModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SkillbaseCreateModal({ isOpen, onClose }: SkillbaseCreateModalProps) {
  const queryClient = useQueryClient()
  const companyId = useCompanyId()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateSkillbaseInput>({
    resolver: zodResolver(createSkillbaseSchema),
    defaultValues: {
      name: '',
      description: '',
      company_id: companyId,
    },
  })

  const createMutation = useMutation({
    mutationFn: skillbasesClient.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skillbases'] })
      toast.success('Skillbase created successfully')
      reset()
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create skillbase')
    },
  })

  const onSubmit = (data: CreateSkillbaseInput) => {
    createMutation.mutate(data)
  }

  const handleClose = () => {
    reset()
    onClose()
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
      <div className="relative bg-white px-6 py-6 rounded-lg shadow-xl max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Skillbase</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <FormInput
              id="name"
              {...register('name')}
              placeholder="Enter skillbase name"
              error={errors.name?.message}
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <FormInput
              id="description"
              {...register('description')}
              placeholder="Enter description (optional)"
              error={errors.description?.message}
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
