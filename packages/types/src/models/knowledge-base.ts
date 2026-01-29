export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  company_id: string
  document_count: number
  chunk_count: number
  created_at: string
}

export interface Document {
  id: string
  title: string
  source_type: string
  chunk_count: number
  is_indexed: boolean
  created_at: string
}

export interface SearchResult {
  content: string
  score: number
  title: string
}

export interface SearchResponse {
  results: SearchResult[]
  query: string
}
