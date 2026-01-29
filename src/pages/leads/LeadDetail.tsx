import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { apiClient } from '@new-voice/api-client'
import { Button, Card, Select, Textarea } from '@new-voice/ui'
import { LeadStatusBadge } from './components/LeadStatusBadge'
import { leadUpdateSchema, type LeadUpdateInput } from '../../schemas/lead-schemas'
import { toast } from 'sonner'

export function LeadDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['leads', id],
    queryFn: () => apiClient.leads.get(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: LeadUpdateInput) => apiClient.leads.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Лид обновлён')
    },
    onError: (error: Error) => {
      toast.error(`Ошибка: ${error.message}`)
    },
  })

  const form = useForm<LeadUpdateInput>({
    resolver: zodResolver(leadUpdateSchema),
    values: {
      status: lead?.status,
      notes: lead?.notes || '',
    },
  })

  const onSubmit = (data: LeadUpdateInput) => {
    updateMutation.mutate(data)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Загрузка...</div>
      </div>
    )
  }

  if (error || !lead) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <div className="text-red-500">Ошибка загрузки лида</div>
        <Button onClick={() => navigate('/leads')}>Вернуться к списку</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            to="/leads"
            className="text-sm text-gray-500 hover:text-gray-700 mb-2 inline-block"
          >
            ← Назад к списку
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">
            {lead.name || 'Лид без имени'}
          </h1>
        </div>
        <LeadStatusBadge status={lead.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Основная информация */}
        <Card className="lg:col-span-2 p-6">
          <h2 className="text-xl font-semibold mb-4">Информация о лиде</h2>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Имя</div>
                <div className="font-medium">{lead.name || '—'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Телефон</div>
                <div className="font-medium">{lead.phone || '—'}</div>
              </div>
            </div>

            <div>
              <div className="text-sm text-gray-500">Email</div>
              <div className="font-medium">{lead.email || '—'}</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Создан</div>
                <div className="font-medium">
                  {new Date(lead.created_at).toLocaleString('ru-RU')}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Обновлён</div>
                <div className="font-medium">
                  {new Date(lead.updated_at).toLocaleString('ru-RU')}
                </div>
              </div>
            </div>

            {lead.call_id && (
              <div>
                <div className="text-sm text-gray-500 mb-2">Связанный звонок</div>
                <Link to={`/calls/${lead.call_id}`}>
                  <Button variant="outline" size="sm">
                    Посмотреть звонок
                  </Button>
                </Link>
              </div>
            )}

            {lead.data && Object.keys(lead.data).length > 0 && (
              <div>
                <div className="text-sm text-gray-500 mb-2">Дополнительные данные</div>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-auto">
                  {JSON.stringify(lead.data, null, 2)}
                </pre>
              </div>
            )}

            <div>
              <div className="text-sm text-gray-500 mb-1">Webhook отправлен</div>
              <div className="font-medium">
                {lead.webhook_sent ? '✅ Да' : '❌ Нет'}
              </div>
            </div>
          </div>
        </Card>

        {/* Форма редактирования */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Редактирование</h2>
          
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Статус
              </label>
              <Select
                {...form.register('status')}
                value={form.watch('status')}
                onValueChange={(value) => form.setValue('status', value as any)}
              >
                <option value="new">Новый</option>
                <option value="contacted">Связались</option>
                <option value="converted">Конвертирован</option>
                <option value="rejected">Отклонён</option>
              </Select>
              {form.formState.errors.status && (
                <p className="text-sm text-red-500 mt-1">
                  {form.formState.errors.status.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Заметки
              </label>
              <Textarea
                {...form.register('notes')}
                rows={6}
                placeholder="Добавьте заметки о лиде..."
              />
              {form.formState.errors.notes && (
                <p className="text-sm text-red-500 mt-1">
                  {form.formState.errors.notes.message}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? 'Сохранение...' : 'Сохранить изменения'}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  )
}
