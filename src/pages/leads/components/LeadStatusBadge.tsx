import { Badge } from '@new-voice/ui'
import type { LeadStatus } from '@new-voice/types'

interface LeadStatusBadgeProps {
  status: LeadStatus
}

const statusConfig: Record<
  LeadStatus,
  { label: string; variant: 'default' | 'success' | 'warning' | 'error' }
> = {
  new: { label: 'Новый', variant: 'default' },
  contacted: { label: 'Связались', variant: 'warning' },
  converted: { label: 'Конвертирован', variant: 'success' },
  rejected: { label: 'Отклонён', variant: 'error' },
}

export function LeadStatusBadge({ status }: LeadStatusBadgeProps) {
  const config = statusConfig[status]

  return <Badge variant={config.variant}>{config.label}</Badge>
}
