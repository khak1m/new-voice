export interface ListResponse<T> {
  items: T[]
  total: number
}

export interface PaginationParams {
  skip?: number
  limit?: number
}

export interface ApiError {
  message: string
  code?: string
  details?: unknown
}
