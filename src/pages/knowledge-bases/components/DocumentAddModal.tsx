import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Input, Textarea, Dialog } from '@new-voice/ui'
import { documentCreateSchema, type DocumentCreateInput } from '../../../schemas/knowledge-base-schemas'

interface DocumentAddModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (data: DocumentCreateInput) => void
  isPending: boolean
}

export function DocumentAddModal({
  open,
  onOpenChange,
  onSubmit,
  isPending,
}: DocumentAddModalProps) {
  const form = useForm<DocumentCreateInput>({
    resolver: zodResolver(documentCreateSchema),
    defaultValues: {
      title: '',
      content: '',
      source_type: 'text',
    },
  })

  const handleSubmit = (data: DocumentCreateInput) => {
    onSubmit(data)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-4">Добавить документ</h2>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Название *
            </label>
            <Input
              {...form.register('title')}
              placeholder="Название документа"
            />
            {form.formState.errors.title && (
              <p className="text-sm text-red-500 mt-1">
                {form.formState.errors.title.message}
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Содержимое *
            </label>
            <Textarea
              {...form.register('content')}
              rows={10}
              placeholder="Введите текст документа..."
            />
            {form.formState.errors.content && (
              <p className="text-sm text-red-500 mt-1">
                {form.formState.errors.content.message}
              </p>
            )}
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Отмена
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Добавление...' : 'Добавить'}
            </Button>
          </div>
        </form>
      </div>
    </Dialog>
  )
}
