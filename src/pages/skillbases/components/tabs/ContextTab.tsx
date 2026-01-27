import type { ContextConfig } from '@new-voice/types'
import { Input, Textarea } from '@new-voice/ui'
import { NativeSelect } from '../../../../components/NativeSelect'

interface ContextTabProps {
  config?: ContextConfig
  isEditing?: boolean
  onChange?: (config: ContextConfig) => void
}

export function ContextTab({ config, isEditing = false, onChange }: ContextTabProps) {
  const handleChange = (field: keyof ContextConfig, value: any) => {
    if (!onChange || !config) return
    onChange({ ...config, [field]: value })
  }

  const handleArrayChange = (field: 'rules' | 'facts', index: number, value: string) => {
    if (!onChange || !config) return
    const newArray = [...(config[field] || [])]
    newArray[index] = value
    onChange({ ...config, [field]: newArray })
  }

  const handleAddArrayItem = (field: 'rules' | 'facts') => {
    if (!onChange || !config) return
    onChange({ ...config, [field]: [...(config[field] || []), ''] })
  }

  const handleRemoveArrayItem = (field: 'rules' | 'facts', index: number) => {
    if (!onChange || !config) return
    const newArray = (config[field] || []).filter((_, i) => i !== index)
    onChange({ ...config, [field]: newArray })
  }

  if (!config) {
    return <div className="text-gray-500">No context configuration available</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Context Configuration</h3>
        <p className="text-sm text-gray-600 mb-6">
          Define the role, style, and behavior rules for your AI agent
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Role *</label>
          <Input
            value={config.role || ''}
            onChange={(e) => handleChange('role', e.target.value)}
            placeholder="e.g., Customer Support Agent"
            disabled={!isEditing}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Style *</label>
          <Input
            value={config.style || ''}
            onChange={(e) => handleChange('style', e.target.value)}
            placeholder="e.g., Professional and friendly"
            disabled={!isEditing}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Language *</label>
          <NativeSelect
            value={config.language || 'ru'}
            onChange={(e) => handleChange('language', e.target.value)}
            disabled={!isEditing}
          >
            <option value="ru">Russian</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
          </NativeSelect>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Call Duration (seconds) *
          </label>
          <Input
            type="number"
            value={config.max_call_duration || 300}
            onChange={(e) => handleChange('max_call_duration', parseInt(e.target.value))}
            min={30}
            max={3600}
            disabled={!isEditing}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Voice ID *</label>
        <Input
          value={config.voice_id || ''}
          onChange={(e) => handleChange('voice_id', e.target.value)}
          placeholder="Enter voice ID"
          disabled={!isEditing}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Rules</label>
        <div className="space-y-2">
          {(config.rules || []).map((rule, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={rule}
                onChange={(e) => handleArrayChange('rules', index, e.target.value)}
                placeholder="Enter a rule"
                disabled={!isEditing}
              />
              {isEditing && (
                <button
                  type="button"
                  onClick={() => handleRemoveArrayItem('rules', index)}
                  className="px-3 py-2 text-red-600 hover:text-red-700"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          {isEditing && (
            <button
              type="button"
              onClick={() => handleAddArrayItem('rules')}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Rule
            </button>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Facts</label>
        <div className="space-y-2">
          {(config.facts || []).map((fact, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={fact}
                onChange={(e) => handleArrayChange('facts', index, e.target.value)}
                placeholder="Enter a fact"
                disabled={!isEditing}
              />
              {isEditing && (
                <button
                  type="button"
                  onClick={() => handleRemoveArrayItem('facts', index)}
                  className="px-3 py-2 text-red-600 hover:text-red-700"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          {isEditing && (
            <button
              type="button"
              onClick={() => handleAddArrayItem('facts')}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Fact
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
