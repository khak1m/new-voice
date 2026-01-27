import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { skillbasesClient } from '@new-voice/api-client'
import type { Skillbase, SkillbaseConfig } from '@new-voice/types'
import { Card, Button } from '@new-voice/ui'
import { ContextTab } from './tabs/ContextTab'
import { FlowTab } from './tabs/FlowTab'
import { AgentTab } from './tabs/AgentTab'
import { ToolsTab } from './tabs/ToolsTab'
import { KnowledgeBaseTab } from './tabs/KnowledgeBaseTab'
import toast from 'react-hot-toast'

interface SkillbaseConfiguratorProps {
  skillbase: Skillbase
  isEditing?: boolean
  onSaveComplete?: () => void
}

export function SkillbaseConfigurator({
  skillbase,
  isEditing = false,
  onSaveComplete,
}: SkillbaseConfiguratorProps) {
  const [activeTab, setActiveTab] = useState('context')
  const [config, setConfig] = useState<SkillbaseConfig | undefined>(skillbase.config)
  const [hasChanges, setHasChanges] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    setConfig(skillbase.config)
    setHasChanges(false)
  }, [skillbase.config, isEditing])

  const saveMutation = useMutation({
    mutationFn: () => skillbasesClient.updateConfig(skillbase.id, config!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skillbase', skillbase.id] })
      toast.success('Configuration saved successfully')
      setHasChanges(false)
      onSaveComplete?.()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to save configuration')
    },
  })

  const handleConfigChange = (tabKey: keyof SkillbaseConfig, value: any) => {
    setConfig((prev) => ({
      ...prev!,
      [tabKey]: value,
    }))
    setHasChanges(true)
  }

  const handleSave = () => {
    if (!config) {
      toast.error('No configuration to save')
      return
    }
    saveMutation.mutate()
  }

  const handleCancel = () => {
    setConfig(skillbase.config)
    setHasChanges(false)
    onSaveComplete?.()
  }

  const tabs = [
    { id: 'context', name: 'Context', component: ContextTab, configKey: 'context' as const },
    { id: 'flow', name: 'Flow', component: FlowTab, configKey: 'flow' as const },
    { id: 'agent', name: 'Agent', component: AgentTab, configKey: 'agent' as const },
    { id: 'tools', name: 'Tools', component: ToolsTab, configKey: 'tools' as const },
    {
      id: 'knowledge',
      name: 'Knowledge Base',
      component: KnowledgeBaseTab,
      configKey: 'knowledge_base' as const,
    },
  ]

  const activeTabData = tabs.find((t) => t.id === activeTab)
  const ActiveComponent = activeTabData?.component

  return (
    <div>
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {isEditing && hasChanges && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex justify-between items-center">
          <span className="text-sm text-yellow-800">You have unsaved changes</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCancel}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </div>
      )}

        <Card>
        <div className="p-6">
          {ActiveComponent && activeTabData && config && (
            <ActiveComponent
              config={config[activeTabData.configKey] as any}
              isEditing={isEditing}
              onChange={(value: any) => handleConfigChange(activeTabData.configKey, value)}
              // Pass voice settings to FlowTab for TTS preview
              {...(activeTabData.id === 'flow' && {
                voiceId: config.context?.voice_id,
                language: config.context?.language || 'ru',
              })}
            />
          )}
          {!config && (
            <div className="text-center py-12 text-gray-500">
              No configuration available. Click Edit to create one.
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
