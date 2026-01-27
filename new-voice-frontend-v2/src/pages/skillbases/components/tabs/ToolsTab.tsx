import type { ToolConfig } from '@new-voice/types'
import { Badge } from '@new-voice/ui'

interface ToolsTabProps {
  config?: ToolConfig[]
  isEditing?: boolean
  onChange?: (config: ToolConfig[]) => void
}

const AVAILABLE_TOOLS: Array<{
  name: ToolConfig['name']
  label: string
  description: string
}> = [
  {
    name: 'transfer_call',
    label: 'Transfer Call',
    description: 'Transfer the call to another number or agent',
  },
  {
    name: 'end_call',
    label: 'End Call',
    description: 'End the current call',
  },
  {
    name: 'detect_language',
    label: 'Detect Language',
    description: 'Automatically detect the language being spoken',
  },
  {
    name: 'skip_turn',
    label: 'Skip Turn',
    description: 'Skip the current turn in conversation',
  },
  {
    name: 'transfer_to_agent',
    label: 'Transfer to Agent',
    description: 'Transfer to a human agent',
  },
  {
    name: 'dtmf_tone',
    label: 'DTMF Tone',
    description: 'Handle DTMF (touch-tone) input',
  },
]

export function ToolsTab({ config, isEditing = false, onChange }: ToolsTabProps) {
  const handleToggleTool = (toolName: ToolConfig['name']) => {
    if (!onChange || !config) return

    const existingTool = config.find((t) => t.name === toolName)

    if (existingTool) {
      // Toggle enabled state
      onChange(
        config.map((t) => (t.name === toolName ? { ...t, enabled: !t.enabled } : t))
      )
    } else {
      // Add new tool
      onChange([...config, { name: toolName, enabled: true, config: {} }])
    }
  }

  const getToolStatus = (toolName: ToolConfig['name']) => {
    const tool = config?.find((t) => t.name === toolName)
    return tool?.enabled ?? false
  }

  if (!config) {
    return <div className="text-gray-500">No tools configuration available</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Tools Configuration</h3>
        <p className="text-sm text-gray-600 mb-6">
          Enable or disable tools that the agent can use during conversations
        </p>
      </div>

      <div className="space-y-3">
        {AVAILABLE_TOOLS.map((tool) => {
          const isEnabled = getToolStatus(tool.name)

          return (
            <div
              key={tool.name}
              className={`border rounded-lg p-4 transition-colors ${
                isEnabled ? 'border-indigo-200 bg-indigo-50' : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="text-sm font-semibold text-gray-900">{tool.label}</h4>
                    <Badge variant={isEnabled ? 'success' : 'default'}>
                      {isEnabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">{tool.description}</p>
                </div>

                {isEditing && (
                  <button
                    type="button"
                    onClick={() => handleToggleTool(tool.name)}
                    className={`ml-4 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                      isEnabled ? 'bg-indigo-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        isEnabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {!isEditing && (
        <div className="text-sm text-gray-500 italic">
          Click "Edit" to enable or disable tools
        </div>
      )}
    </div>
  )
}
