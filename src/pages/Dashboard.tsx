import { Link } from 'react-router-dom'
import { Card } from '@new-voice/ui'

export function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
      
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Link to="/skillbases">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Skillbases</h3>
              <p className="text-gray-600">Manage your AI voice agents</p>
            </div>
          </Card>
        </Link>

        <Card className="opacity-50">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Campaigns</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
        </Card>

        <Card className="opacity-50">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Analytics</h3>
            <p className="text-gray-600">Coming soon...</p>
          </div>
        </Card>
      </div>
    </div>
  )
}
