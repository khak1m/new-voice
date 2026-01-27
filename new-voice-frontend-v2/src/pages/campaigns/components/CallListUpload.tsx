import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Dialog, Button } from '@new-voice/ui'
import toast from 'react-hot-toast'
import { apiClient } from '@new-voice/api-client'

interface CallListUploadProps {
  campaignId: string
  onClose: () => void
}

export function CallListUpload({ campaignId, onClose }: CallListUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post(
        `/campaigns/${campaignId}/call-list`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns', campaignId] })
      toast.success(`Successfully uploaded ${data.created} contacts`)
      if (data.errors && data.errors.length > 0) {
        toast.error(`${data.errors.length} errors occurred during upload`)
      }
      onClose()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload call list')
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = () => {
    if (file) {
      uploadMutation.mutate(file)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-lg w-full">
        <h2 className="text-xl font-bold mb-4">Upload Call List</h2>

        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-4">
            Upload a CSV or Excel file with contact information. The file must contain a <strong>phone_number</strong> column.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
            <h3 className="font-semibold text-sm mb-2">Required Columns:</h3>
            <ul className="text-sm text-gray-700 list-disc list-inside">
              <li><strong>phone_number</strong> - Contact phone number (required)</li>
            </ul>
            
            <h3 className="font-semibold text-sm mt-3 mb-2">Optional Columns:</h3>
            <ul className="text-sm text-gray-700 list-disc list-inside">
              <li><strong>name</strong> or <strong>contact_name</strong> - Contact name</li>
              <li>Any additional columns will be saved as contact data</li>
            </ul>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer inline-flex flex-col items-center"
            >
              <svg
                className="w-12 h-12 text-gray-400 mb-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <span className="text-sm text-gray-600">
                {file ? file.name : 'Click to select a file'}
              </span>
              <span className="text-xs text-gray-500 mt-1">
                CSV, XLSX, or XLS (max 10MB)
              </span>
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!file || uploadMutation.isPending}
          >
            {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
