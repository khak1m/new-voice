// Export base axios client
export { apiClient as axiosClient } from './client'

// Export all individual clients
export * from './clients'

// Import and re-export unified API client
import { apiClient as axios } from './client'
import { skillbasesClient } from './clients/skillbases'
import { campaignsClient } from './clients/campaigns'
import { callsClient } from './clients/calls'
import { leadsClient } from './clients/leads'
import { knowledgeBasesClient } from './clients/knowledge-bases'
import { companiesClient } from './clients/companies'
import { analyticsClient } from './clients/analytics'
import { dashboardClient } from './clients/dashboard'
import { ttsClient } from './clients/tts'

export const apiClient = Object.assign(axios, {
  skillbases: skillbasesClient,
  campaigns: campaignsClient,
  calls: callsClient,
  leads: leadsClient,
  knowledgeBases: knowledgeBasesClient,
  companies: companiesClient,
  analytics: analyticsClient,
  dashboard: dashboardClient,
  tts: ttsClient,
})
