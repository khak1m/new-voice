import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@new-voice/api-client'
import { Button, Card, Input, Table, Dialog } from '@new-voice/ui'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { knowledgeBaseCreateSchema, type KnowledgeBaseCreateInput } from '../../schemas/knowledge-base-schemas'
import { toast } from 'sonner'

export function KnowledgeBasesList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: knowledgeBases, isLoading, error } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => {
      const response = await apiClient.knowledgeBases.list()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: KnowledgeBaseCreateInput) =>
      apiClient.knowledgeBases.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      setIsCreateModalOpen(false)
      toast.success('База знаний создана')
      form.reset()
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.knowledgeBases.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      toast.success('База знаний удалена')
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`)
    },
  })

  const form = useForm<KnowledgeBaseCreateInput>({
    resolver: zodResolver(knowledgeBaseCreateSchema),
    defaultValues: {
      name: '',
      description: '',
      company_id: 'default-company',
    },
  })

  const onSubmit = (data: KnowledgeBaseCreateInput) => {
    createMutation.mutate(data)
  }

  const filteredKBs = knowledgeBases?.filter((kb) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      kb.name.toLowerCase().includes(query) ||
      kb.description?.toLowerCase().includes(query)
    )
  })

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Удалить базу знаний "${name}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Базы знаний</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Создать базу знаний
        </Button>
      </div>

      <Card className="p-6">
        <div className="mb-6">
          <Input
            placeholder="Поиск по названию или описанию..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {isLoading && (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        )}

        {error && (
          <div className="text-center py-12 text-red-500">
            Ошибка загрузки: {error.message}
          </div>
        )}

        {!isLoading && !error && filteredKBs && (
          <Table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Описание</th>
                <th>Документов</th>
                <th>Чанков</th>
                <th>Создана</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredKBs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-500">
                    Базы знаний не найдены
                  </td>
                </tr>
              ) : (
                filteredKBs.map((kb) => (
                  <tr key={kb.id}>
                    <td className="font-medium">{kb.name}</td>
                    <td>{kb.description || '—'}</td>
                    <td>{kb.document_count}</td>
                    <td>{kb.chunk_count}</td>
                    <td>
                      {new Date(kb.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <Link to={`/knowledge-bases/${kb.id}`}>
                          <Button variant="ghost" size="sm">
                            Открыть
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(kb.id, kb.name)}
                          disabled={deleteMutation.isPending}
                        >
                          Удалить
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        )}
      </Card>

      {/* Create Modal */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Создать базу знаний</h2>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Название *
              </label>
              <Input {...form.register('name')} placeholder="Моя база знаний" />
              {form.formState.errors.name && (
                <p className="text-sm text-red-500 mt-1">
                  {form.formState.errors.name.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Описание
              </label>
              <Input
                {...form.register('description')}
                placeholder="Описание базы знаний..."
              />
            </div>

            <div className="flex gap-2 justify-end">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateModalOpen(false)}
              >
                Отмена
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Создание...' : 'Создать'}
              </Button>
            </div>
          </form>
        </div>
      </Dialog>
    </div>
  )
}
