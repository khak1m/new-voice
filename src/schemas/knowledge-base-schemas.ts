import { z } from 'zod'

export const knowledgeBaseCreateSchema = z.object({
  name: z.string().min(1, 'Название обязательно').max(255),
  description: z.string().optional(),
  company_id: z.string(),
})

export const documentCreateSchema = z.object({
  title: z.string().min(1, 'Название обязательно').max(500),
  content: z.string().min(1, 'Содержимое обязательно'),
  source_type: z.string().default('text'),
})

export const searchSchema = z.object({
  query: z.string().min(1, 'Запрос обязателен'),
  top_k: z.number().min(1).max(10).default(3),
})

export type KnowledgeBaseCreateInput = z.infer<typeof knowledgeBaseCreateSchema>
export type DocumentCreateInput = z.infer<typeof documentCreateSchema>
export type SearchInput = z.infer<typeof searchSchema>
