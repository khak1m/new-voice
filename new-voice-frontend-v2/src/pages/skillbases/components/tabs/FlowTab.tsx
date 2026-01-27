import type { FlowConfig } from '@new-voice/types'
import { Textarea } from '@new-voice/ui'

interface FlowTabProps {
  config?: FlowConfig
  isEditing?: boolean
  onChange?: (config: FlowConfig) => void
}

export function FlowTab({ config, isEditing = false, onChange }: FlowTabProps) {
  const handleArrayChange = (
    field: 'greeting_phrases' | 'conversation_plan',
    index: number,
    value: string
  ) => {
    if (!onChange || !config) return
    const newArray = [...(config[field] || [])]
    newArray[index] = value
    onChange({ ...config, [field]: newArray })
  }

  const handleAddArrayItem = (field: 'greeting_phrases' | 'conversation_plan') => {
    if (!onChange || !config) return
    onChange({ ...config, [field]: [...(config[field] || []), ''] })
  }

  const handleRemoveArrayItem = (field: 'greeting_phrases' | 'conversation_plan', index: number) => {
    if (!onChange || !config) return
    const newArray = (config[field] || []).filter((_, i) => i !== index)
    onChange({ ...config, [field]: newArray })
  }

  if (!config) {
    return <div className="text-gray-500">No flow configuration available</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Flow Configuration</h3>
        <p className="text-sm text-gray-600 mb-6">
          Define the conversation flow and greeting phrases
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Greeting Phrases *
        </label>
        <p className="text-xs text-gray-500 mb-3">
          Add multiple greeting phrases that the agent can use to start conversations
        </p>
        <div className="space-y-2">
          {(config.greeting_phrases || []).map((phrase, index) => (
            <div key={index} className="flex gap-2">
              <Textarea
                value={phrase}
                onChange={(e) => handleArrayChange('greeting_phrases', index, e.target.value)}
                placeholder="Enter a greeting phrase"
                rows={2}
                disabled={!isEditing}
              />
              {isEditing && (
                <button
                  type="button"
                  onClick={() => handleRemoveArrayItem('greeting_phrases', index)}
                  className="px-3 py-2 text-red-600 hover:text-red-700 self-start"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          {isEditing && (
            <button
              type="button"
              onClick={() => handleAddArrayItem('greeting_phrases')}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Greeting Phrase
            </button>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Conversation Plan *
        </label>
        <p className="text-xs text-gray-500 mb-3">
          Define the steps and flow of the conversation
        </p>
        <div className="space-y-2">
          {(config.conversation_plan || []).map((step, index) => (
            <div key={index} className="flex gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-700">Step {index + 1}</span>
                </div>
                <Textarea
                  value={step}
                  onChange={(e) => handleArrayChange('conversation_plan', index, e.target.value)}
                  placeholder="Describe this conversation step"
                  rows={3}
                  disabled={!isEditing}
                />
              </div>
              {isEditing && (
                <button
                  type="button"
                  onClick={() => handleRemoveArrayItem('conversation_plan', index)}
                  className="px-3 py-2 text-red-600 hover:text-red-700 self-start"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          {isEditing && (
            <button
              type="button"
              onClick={() => handleAddArrayItem('conversation_plan')}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Conversation Step
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
