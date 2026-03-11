import { z } from 'zod';

export const jobSchema = z.object({
  topic: z.string().min(3, 'Topic must be at least 3 characters'),
  target_audience: z.string().optional(),
  provider: z.string().optional(),
  model_id: z.string().optional(),
  resolution: z.enum(['720p', '1080p']),
  frame_rate: z.union([z.literal(30), z.literal(60)]),
});

export type JobFormData = z.infer<typeof jobSchema>;
export type ProviderGroup = { provider: string; display_name?: string | null; models: string[] };
