import { z } from 'zod';

export const jobSchema = z.object({
  topic: z.string().min(3, 'Topic must be at least 3 characters'),
  provider: z.string().optional(),
  model_id: z.string().optional(),
  analyst_model: z.string().optional(),
  architect_model: z.string().optional(),
  animator_model: z.string().optional(),
});

export type JobFormData = z.infer<typeof jobSchema>;
export type ProviderGroup = { provider: string; display_name?: string | null; models: string[] };
