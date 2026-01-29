import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiClient } from '@new-voice/api-client'
import { Button, Card, Input, Select, Table } from '@new-voice/ui'
import { LeadStatusBadge } from './components/LeadStatusBadge'
import type { LeadStatus } from '@new-voice/types'

export function LeadsList() {
  const [statusFilter, setStatusFilter] = useState<LeadStatus | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)
  const limit = 20

  const { data, isLoading, error } = useQuery({
    queryKey: ['leads', { status: statusFilter, skip: page * limit, limit }],
    queryFn: async () => {
      const response = await apiClient.leads.list({
        status: statusFilter === 'all' ? undefined : statusFilter,
        skip: page * limit,
        limit,
      })
      return response.data
    },
  })

  const handleExport = async () => {
    try {
      const response = await apiClient.leads.export()
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `leads-${new Date().toISOString()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  const filteredLeads = data?.items.filter((lead) => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      lead.name?.toLowerCase().includes(query) ||
      lead.phone?.toLowerCase().includes(query) ||
      lead.email?.toLowerCase().includes(query)
    )
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Лиды</h1>
        <Button onClick={handleExport} variant="outline">
          Экспорт CSV
        </Button>
      </div>

      <Card className="p-6">
        <div className="flex gap-4 mb-6">
          <Input
            placeholder="Поиск по имени, телефону, email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1"
          />
          <Select
            value={statusFilter}
            onValueChange={(value) => setStatusFilter(value as LeadStatus | 'all')}
          >
            <option value="all">Все статусы</option>
            <option value="new">Новый</option>
            <option value="contacted">Связались</option>
            <option value="converted">Конвертирован</option>
            <option value="rejected">Отклонён</option>
          </Select>
        </div>

        {isLoading && (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        )}

        {error && (
          <div className="text-center py-12 text-red-500">
            Ошибка загрузки: {error.message}
          </div>
        )}

        {!isLoading && !error && filteredLeads && (
          <>
            <Table>
              <thead>
                <tr>
                  <th>Имя</th>
                  <th>Телефон</th>
                  <th>Email</th>
                  <th>Статус</th>
                  <th>Создан</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-500">
                      Лиды не найдены
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((lead) => (
                    <tr key={lead.id}>
                      <td>{lead.name || '—'}</td>
                      <td>{lead.phone || '—'}</td>
                      <td>{lead.email || '—'}</td>
                      <td>
                        <LeadStatusBadge status={lead.status} />
                      </td>
                      <td>
                        {new Date(lead.created_at).toLocaleDateString('ru-RU')}
                      </td>
                      <td>
                        <Link to={`/leads/${lead.id}`}>
                          <Button variant="ghost" size="sm">
                            Подробнее
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>

            {data && data.total > limit && (
              <div className="flex items-center justify-between mt-6">
                <div className="text-sm text-gray-500">
                  Показано {page * limit + 1}-
                  {Math.min((page + 1) * limit, data.total)} из {data.total}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Назад
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={(page + 1) * limit >= data.total}
                  >
                    Вперёд
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  )
}
