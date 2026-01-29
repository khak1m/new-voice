import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@new-voice/api-client'
import { Button, Card, Table } from '@new-voice/ui'
import { DocumentAddModal } from './components/DocumentAddModal'
import { SearchPanel } from './components/SearchPanel'
import type { DocumentCreateInput } from '../../schemas/knowledge-base-schemas'
import type { SearchResult } from '@new-voice/types'
import { toast } from 'sonner'

export function KnowledgeBaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[] | undefined>()

  const { data: kb, isLoading, error } = useQuery({
    queryKey: ['knowledge-bases', id],
    queryFn: () => apiClient.knowledgeBases.get(id!),
    enabled: !!id,
  })

  const { data: documents } = useQuery({
    queryKey: ['knowledge-bases', id, 'documents'],
    queryFn: () => apiClient.knowledgeBases.listDocuments(id!),
    enabled: !!id,
  })

  const addDocumentMutation = useMutation({
    mutationFn: (data: DocumentCreateInput) =>
      apiClient.knowledgeBases.addDocument(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      setIsAddModalOpen(false)
      toast.success('Документ добавлен')
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`)
    },
  })

  const deleteDocumentMutation = useMutation({
    mutationFn: (docId: string) =>
      apiClient.knowledgeBases.deleteDocument(id!, docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      toast.success('Документ удалён')
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`)
    },
  })

  const searchMutation = useMutation({
    mutationFn: ({ query, topK }: { query: string; topK: number }) =>
      apiClient.knowledgeBases.search(id!, query, topK),
    onSuccess: (data) => {
      setSearchResults(data.results)
    },
    onError: (error: Error) => {
      toast.error(`Ошибка поиска: ${error.message}`)
    },
  })

  const handleSearch = (query: string, topK: number) => {
    searchMutation.mutate({ query, topK })
  }

  const handleDeleteDocument = (docId: string, title: string) => {
    if (confirm(`Удалить документ "${title}"?`)) {
      deleteDocumentMutation.mutate(docId)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    )
  }

  if (error || !kb) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <div className="text-red-500">Ошибка загрузки базы знаний</div>
        <Button onClick={() => navigate('/knowledge-bases')}>
          Вернуться к списку
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/knowledge-bases"
          className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
        >
          ← Назад к списку
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{kb.name}</h1>
        {kb.description && (
          <p className="text-gray-600 mt-2">{kb.description}</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Информация о базе */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Статистика</h2>
          <div className="space-y-3">
            <div>
              <div className="text-sm text-gray-500">Документов</div>
              <div className="text-2xl font-bold">{kb.document_count}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Чанков</div>
              <div className="text-2xl font-bold">{kb.chunk_count}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Создана</div>
              <div className="font-medium">
                {new Date(kb.created_at).toLocaleDateString('ru-RU')}
              </div>
            </div>
          </div>
        </Card>

        {/* Поиск */}
        <div className="lg:col-span-2">
          <SearchPanel
            onSearch={handleSearch}
            results={searchResults}
            isSearching={searchMutation.isPending}
          />
        </div>
      </div>

      {/* Документы */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Документы</h2>
          <Button onClick={() => setIsAddModalOpen(true)}>
            Добавить документ
          </Button>
        </div>

        {!documents || documents.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            Документы не найдены. Добавьте первый документ.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Тип</th>
                <th>Чанков</th>
                <th>Индексирован</th>
                <th>Создан</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="font-medium">{doc.title}</td>
                  <td>{doc.source_type}</td>
                  <td>{doc.chunk_count}</td>
                  <td>
                    {doc.is_indexed ? (
                      <span className="text-green-600">✓ Да</span>
                    ) : (
                      <span className="text-gray-400">✗ Нет</span>
                    )}
                  </td>
                  <td>
                    {new Date(doc.created_at).toLocaleDateString('ru-RU')}
                  </td>
                  <td>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteDocument(doc.id, doc.title)}
                      disabled={deleteDocumentMutation.isPending}
                    >
                      Удалить
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <DocumentAddModal
        open={isAddModalOpen}
        onOpenChange={setIsAddModalOpen}
        onSubmit={(data) => addDocumentMutation.mutate(data)}
        isPending={addDocumentMutation.isPending}
      />
    </div>
  )
}
