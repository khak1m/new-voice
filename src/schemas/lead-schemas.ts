import { z } from 'zod'

export const leadUpdateSchema = z.object({
  status: z.enum(['new', 'contacted', 'converted', 'rejected']).optional(),
  notes: z.string().optional(),
})

export type LeadUpdateInput = z.infer<typeof leadUpdateSchema>
