import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { MainLayout } from './layouts/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { SkillbasesList } from './pages/skillbases/SkillbasesList'
import { SkillbaseDetail } from './pages/skillbases/SkillbaseDetail'
import { CampaignsList } from './pages/campaigns/CampaignsList'
import { CampaignDetail } from './pages/campaigns/CampaignDetail'
import { CallsList } from './pages/calls/CallsList'
import { CallDetail } from './pages/calls/CallDetail'
import { LeadsList } from './pages/leads/LeadsList'
import { LeadDetail } from './pages/leads/LeadDetail'

function App() {
  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="skillbases" element={<SkillbasesList />} />
            <Route path="skillbases/:id" element={<SkillbaseDetail />} />
            <Route path="campaigns" element={<CampaignsList />} />
            <Route path="campaigns/:id" element={<CampaignDetail />} />
            <Route path="calls" element={<CallsList />} />
            <Route path="calls/:id" element={<CallDetail />} />
            <Route path="leads" element={<LeadsList />} />
            <Route path="leads/:id" element={<LeadDetail />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
