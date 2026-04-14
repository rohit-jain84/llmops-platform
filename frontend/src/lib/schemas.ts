import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
})

export const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  role: z.enum(['admin', 'engineer', 'evaluator']).default('engineer'),
})

export const promptTemplateSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
})

export const promptVersionSchema = z.object({
  content: z.string().min(1),
  model_config_data: z.record(z.unknown()).optional(),
  tag: z.string().optional(),
  commit_message: z.string().optional(),
})

export const experimentSchema = z.object({
  application_id: z.string().uuid(),
  name: z.string().min(1).max(255),
  variants: z.array(z.object({
    prompt_version_id: z.string().uuid(),
    traffic_pct: z.number().int().min(0).max(100),
    label: z.string().min(1),
  })).min(2).refine(
    (variants) => variants.reduce((sum, v) => sum + v.traffic_pct, 0) === 100,
    { message: 'Traffic percentages must sum to 100' }
  ),
})

export const evalDatasetSchema = z.object({
  application_id: z.string().uuid(),
  name: z.string().min(1).max(255),
  dataset_type: z.enum(['golden', 'adversarial', 'custom']).default('golden'),
  description: z.string().optional(),
})

export const budgetAlertSchema = z.object({
  application_id: z.string().uuid(),
  budget_usd: z.number().positive(),
  period: z.enum(['daily', 'weekly', 'monthly']).default('monthly'),
  alert_pct: z.array(z.number().int().min(1).max(100)).default([80, 100]),
})

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type PromptTemplateInput = z.infer<typeof promptTemplateSchema>
export type PromptVersionInput = z.infer<typeof promptVersionSchema>
export type ExperimentInput = z.infer<typeof experimentSchema>
export type EvalDatasetInput = z.infer<typeof evalDatasetSchema>
export type BudgetAlertInput = z.infer<typeof budgetAlertSchema>
