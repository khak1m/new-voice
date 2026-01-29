import { Link } from 'react-router-dom'
import { Card } from '@new-voice/ui'

interface StatCardProps {
  title: string
  value: number | string
  description?: string
  link?: string
  icon?: React.ReactNode
  loading?: boolean
}

export function StatCard({ title, value, description, link, icon, loading }: StatCardProps) {
  const content = (
    <Card className={`p-6 ${link ? 'hover:shadow-lg transition-shadow cursor-pointer' : ''}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          {loading ? (
            <div className="mt-2 h-8 w-20 bg-gray-200 animate-pulse rounded"></div>
          ) : (
            <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          )}
          {description && (
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          )}
        </div>
        {icon && (
          <div className="ml-4 flex-shrink-0">
            <div className="rounded-lg bg-indigo-50 p-3 text-indigo-600">
              {icon}
            </div>
          </div>
        )}
      </div>
    </Card>
  )

  if (link) {
    return <Link to={link}>{content}</Link>
  }

  return content
}
