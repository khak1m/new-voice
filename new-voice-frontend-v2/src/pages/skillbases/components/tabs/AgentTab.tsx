import type { AgentConfig } from '@new-voice/types'
import { Input, Textarea } from '@new-voice/ui'
import { NativeSelect } from '../../../../components/NativeSelect'

interface AgentTabProps {
  config?: AgentConfig
  isEditing?: boolean
  onChange?: (config: AgentConfig) => void
}

export function AgentTab({ config, isEditing = false, onChange }: AgentTabProps) {
  const handleFieldChange = (index: number, field: 'name' | 'instruction', value: string) => {
    if (!onChange || !config) return
    const newFields = [...(config.lead_transfer_fields || [])]
    newFields[index] = { ...newFields[index], [field]: value }
    onChange({ ...config, lead_transfer_fields: newFields })
  }

  const handleAddField = () => {
    if (!onChange || !config) return
    onChange({
      ...config,
      lead_transfer_fields: [...(config.lead_transfer_fields || []), { name: '', instruction: '' }],
    })
  }

  const handleRemoveField = (index: number) => {
    if (!onChange || !config) return
    const newFields = (config.lead_transfer_fields || []).filter((_, i) => i !== index)
    onChange({ ...config, lead_transfer_fields: newFields })
  }

  const handleClosingMessageChange = (field: 'type' | 'prompt' | 'template', value: any) => {
    if (!onChange || !config) return
    onChange({
      ...config,
      closing_message: {
        ...config.closing_message,
        [field]: value,
      },
    })
  }

  if (!config) {
    return <div className="text-gray-500">No agent configuration available</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Agent Configuration</h3>
        <p className="text-sm text-gray-600 mb-6">
          Configure lead transfer fields and closing messages
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Lead Transfer Fields
        </label>
        <p className="text-xs text-gray-500 mb-3">
          Define which fields should be collected and transferred for leads
        </p>
        <div className="space-y-4">
          {(config.lead_transfer_fields || []).map((field, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <span className="text-sm font-medium text-gray-700">Field {index + 1}</span>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleRemoveField(index)}
                    className="text-sm text-red-600 hover:text-red-700"
                  >
                    Remove
                  </button>
                )}
              </div>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Field Name *
                  </label>
                  <Input
                    value={field.name}
                    onChange={(e) => handleFieldChange(index, 'name', e.target.value)}
                    placeholder="e.g., phone_number, email"
                    disabled={!isEditing}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Instruction *
                  </label>
                  <Textarea
                    value={field.instruction}
                    onChange={(e) => handleFieldChange(index, 'instruction', e.target.value)}
                    placeholder="How should the agent collect this field?"
                    rows={2}
                    disabled={!isEditing}
                  />
                </div>
              </div>
            </div>
          ))}
          {isEditing && (
            <button
              type="button"
              onClick={handleAddField}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Field
            </button>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Closing Message</label>
        <p className="text-xs text-gray-500 mb-3">
          Configure how the agent should end conversations
        </p>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Type *</label>
            <NativeSelect
              value={config.closing_message?.type || 'llm_prompt'}
              onChange={(e) =>
                handleClosingMessageChange('type', e.target.value as 'llm_prompt' | 'static_template')
              }
              disabled={!isEditing}
            >
              <option value="llm_prompt">LLM Prompt (Dynamic)</option>
              <option value="static_template">Static Template</option>
            </NativeSelect>
          </div>

          {config.closing_message?.type === 'llm_prompt' ? (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Prompt</label>
              <Textarea
                value={config.closing_message?.prompt || ''}
                onChange={(e) => handleClosingMessageChange('prompt', e.target.value)}
                placeholder="Enter the prompt for generating closing messages"
                rows={4}
                disabled={!isEditing}
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Template</label>
              <Textarea
                value={config.closing_message?.template || ''}
                onChange={(e) => handleClosingMessageChange('template', e.target.value)}
                placeholder="Enter the static closing message template"
                rows={4}
                disabled={!isEditing}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
