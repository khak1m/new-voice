export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  company_id: string
  documents?: Document[]
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  name: string
  size: number
  type: string
  uploaded_at: string
}
