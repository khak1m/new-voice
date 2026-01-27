import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { skillbasesClient } from '@new-voice/api-client'
import { Button, Badge } from '@new-voice/ui'
import type { Skillbase } from '@new-voice/types'
import { SkillbaseConfigurator } from './components/SkillbaseConfigurator'
import toast from 'react-hot-toast'

export function SkillbaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isEditing, setIsEditing] = useState(false)

  const { data: skillbase, isLoading } = useQuery({
    queryKey: ['skillbase', id],
    queryFn: () => skillbasesClient.get(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => skillbasesClient.delete(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skillbases'] })
      toast.success('Skillbase deleted successfully')
      navigate('/skillbases')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete skillbase')
    },
  })

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this skillbase? This action cannot be undone.')) {
      deleteMutation.mutate()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading skillbase...</div>
      </div>
    )
  }

  if (!skillbase) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Skillbase not found</h2>
        <Link to="/skillbases" className="text-indigo-600 hover:text-indigo-800">
          ← Back to Skillbases
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6">
        <Link to="/skillbases" className="text-indigo-600 hover:text-indigo-800 text-sm">
          ← Back to Skillbases
        </Link>
      </div>

      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{skillbase.name}</h1>
          {skillbase.description && (
            <p className="text-gray-600">{skillbase.description}</p>
          )}
        </div>
        <div className="flex gap-3">
          <Badge variant="success">Active</Badge>
          <Button
            variant="outline"
            onClick={() => setIsEditing(!isEditing)}
          >
            {isEditing ? 'Cancel Edit' : 'Edit'}
          </Button>
          <Button
            variant="outline"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </div>

      <SkillbaseConfigurator
        skillbase={skillbase}
        isEditing={isEditing}
        onSaveComplete={() => setIsEditing(false)}
      />
    </div>
  )
}
