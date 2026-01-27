import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { skillbasesClient } from '@new-voice/api-client'
import { Button, Card, Badge } from '@new-voice/ui'
import type { Skillbase } from '@new-voice/types'
import { SkillbaseCreateModal } from './components/SkillbaseCreateModal'

export function SkillbasesList() {
  const queryClient = useQueryClient()
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  console.log('SkillbasesList component loaded - VERSION 2.0 WITH CREATE BUTTON')

  const { data: skillbases, isLoading, error } = useQuery({
    queryKey: ['skillbases'],
    queryFn: () => skillbasesClient.list({ skip: 0, limit: 50 }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading skillbases...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Skillbases</h1>
          <Button onClick={() => setIsCreateModalOpen(true)}>Create Skillbase</Button>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Skillbases</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Unable to connect to the backend server. Please make sure the API is running at{' '}
            <code className="bg-red-100 px-2 py-1 rounded text-sm">http://77.233.212.58:8000</code>
          </p>
          <div className="flex gap-3 justify-center">
            <Button 
              onClick={() => queryClient.invalidateQueries({ queryKey: ['skillbases'] })}
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

        <SkillbaseCreateModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Skillbases</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create Skillbase</Button>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {skillbases?.items?.map((skillbase: Skillbase) => (
          <Link key={skillbase.id} to={`/skillbases/${skillbase.id}`}>
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{skillbase.name}</h3>
                  <Badge variant="success">Active</Badge>
                </div>
                {skillbase.description && (
                  <p className="text-gray-600 text-sm mb-4">{skillbase.description}</p>
                )}
                <div className="text-xs text-gray-500">
                  Created: {new Date(skillbase.created_at).toLocaleDateString()}
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {(!skillbases?.items || skillbases.items.length === 0) && (
        <Card>
          <div className="p-12 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No skillbases yet</h3>
            <p className="text-gray-600 mb-6">Create your first skillbase to get started</p>
            <Button onClick={() => setIsCreateModalOpen(true)}>Create Skillbase</Button>
          </div>
        </Card>
      )}

      <SkillbaseCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  )
}
