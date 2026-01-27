import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './layouts/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { SkillbasesList } from './pages/skillbases/SkillbasesList'
import { SkillbaseDetail } from './pages/skillbases/SkillbaseDetail'
import { CampaignsList } from './pages/campaigns/CampaignsList'
import { CampaignDetail } from './pages/campaigns/CampaignDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="skillbases" element={<SkillbasesList />} />
          <Route path="skillbases/:id" element={<SkillbaseDetail />} />
          <Route path="campaigns" element={<CampaignsList />} />
          <Route path="campaigns/:id" element={<CampaignDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
