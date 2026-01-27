import { z } from 'zod'

// Create Campaign Schema
export const createCampaignSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long'),
  description: z.string().optional(),
  skillbase_id: z.string().min(1, 'Skillbase is required'),
  
  // Scheduling
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  daily_start_time: z.string().regex(/^\d{2}:\d{2}$/, 'Invalid time format (HH:MM)').default('09:00'),
  daily_end_time: z.string().regex(/^\d{2}:\d{2}$/, 'Invalid time format (HH:MM)').default('18:00'),
  timezone: z.string().default('UTC'),
  
  // Rate limiting
  max_concurrent_calls: z.number().min(1).max(100).default(5),
  calls_per_minute: z.number().min(1).max(100).default(10),
  max_retries: z.number().min(0).max(10).default(3),
  retry_delay_minutes: z.number().min(1).max(1440).default(30),
})

export type CreateCampaignInput = z.infer<typeof createCampaignSchema>

// Update Campaign Schema
export const updateCampaignSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name is too long').optional(),
  description: z.string().optional(),
  
  // Scheduling
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  daily_start_time: z.string().regex(/^\d{2}:\d{2}$/, 'Invalid time format (HH:MM)').optional(),
  daily_end_time: z.string().regex(/^\d{2}:\d{2}$/, 'Invalid time format (HH:MM)').optional(),
  timezone: z.string().optional(),
  
  // Rate limiting
  max_concurrent_calls: z.number().min(1).max(100).optional(),
  calls_per_minute: z.number().min(1).max(100).optional(),
  max_retries: z.number().min(0).max(10).optional(),
  retry_delay_minutes: z.number().min(1).max(1440).optional(),
})

export type UpdateCampaignInput = z.infer<typeof updateCampaignSchema>
