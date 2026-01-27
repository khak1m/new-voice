import type { KnowledgeBaseConfig } from '@new-voice/types'
import { Input, Badge } from '@new-voice/ui'

interface KnowledgeBaseTabProps {
  config?: KnowledgeBaseConfig
  isEditing?: boolean
  onChange?: (config: KnowledgeBaseConfig) => void
}

export function KnowledgeBaseTab({ config, isEditing = false, onChange }: KnowledgeBaseTabProps) {
  const handleAddDocument = () => {
    if (!onChange || !config) return
    const documentId = prompt('Enter document ID:')
    if (documentId) {
      onChange({
        ...config,
        document_ids: [...(config.document_ids || []), documentId],
      })
    }
  }

  const handleRemoveDocument = (index: number) => {
    if (!onChange || !config) return
    const newDocuments = (config.document_ids || []).filter((_, i) => i !== index)
    onChange({ ...config, document_ids: newDocuments })
  }

  if (!config) {
    return <div className="text-gray-500">No knowledge base configuration available</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Knowledge Base Configuration</h3>
        <p className="text-sm text-gray-600 mb-6">
          Manage documents that the agent can reference during conversations
        </p>
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <label className="block text-sm font-medium text-gray-700">Connected Documents</label>
          {isEditing && (
            <button
              type="button"
              onClick={handleAddDocument}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              + Add Document
            </button>
          )}
        </div>

        {(!config.document_ids || config.document_ids.length === 0) ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-gray-500 mb-2">No documents connected</p>
            {isEditing && (
              <p className="text-sm text-gray-400">Click "Add Document" to connect a document</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {config.document_ids.map((docId, index) => (
              <div
                key={index}
                className="flex items-center justify-between border border-gray-200 rounded-lg p-4 bg-white"
              >
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-8 w-8 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">Document {index + 1}</p>
                    <p className="text-xs text-gray-500 font-mono">{docId}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Badge variant="success">Connected</Badge>
                  {isEditing && (
                    <button
                      type="button"
                      onClick={() => handleRemoveDocument(index)}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">About Knowledge Base</h4>
        <p className="text-sm text-blue-700">
          Documents in the knowledge base are used by the agent to provide accurate and contextual
          responses. The agent will search through these documents to find relevant information
          during conversations.
        </p>
      </div>
    </div>
  )
}
