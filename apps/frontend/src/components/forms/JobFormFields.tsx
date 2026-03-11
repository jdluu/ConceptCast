import { UseFormRegister } from 'react-hook-form';
import { JobFormData, ProviderGroup } from './JobFormTypes';

const selectStyles =
  "w-full bg-background/50 border border-surface-border rounded-xl px-4 py-3 text-foreground focus:ring-2 focus:ring-council-active/50 focus:border-council-active outline-none appearance-none cursor-pointer hover:border-council-active/50 transition-all shadow-sm bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2224%22%20height%3D%2224%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%233b82f6%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E')] bg-[length:1.25rem] bg-[right_1rem_center] bg-no-repeat";

const Label = ({ htmlFor, children }: { htmlFor: string; children: React.ReactNode }) => (
  <label
    htmlFor={htmlFor}
    className="block text-tiny font-bold tracking-[0.2em] text-text-muted uppercase"
  >
    {children}
  </label>
);

/**
 * Form field for selecting the target audience knowledge level.
 */
export const AudienceField = ({ register }: { register: UseFormRegister<JobFormData> }) => (
  <div className="space-y-2">
    <Label htmlFor="target_audience">
      Target Audience
    </Label>
    <select {...register('target_audience')} id="target_audience" className={selectStyles}>
      <option value="5-year-old">5-year-old</option>
      <option value="High School Student">High School Student</option>
      <option value="University Student">University Student</option>
      <option value="Expert">Expert</option>
      <option value="General Audience">General Audience</option>
    </select>
  </div>
);

/**
 * Form fields for selecting the AI provider and specific model ID.
 * Dynamically updates model options based on the selected provider.
 */
export const ModelSelectionFields = ({
  register,
  selectedProvider,
  realProvidersOnly,
}: {
  register: UseFormRegister<JobFormData>;
  selectedProvider: string | undefined;
  realProvidersOnly: ProviderGroup[];
}) => {
  const models = realProvidersOnly.find((p) => p.provider === selectedProvider)?.models ?? [];

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="provider">
          AI Provider
        </Label>
        <select {...register('provider')} id="provider" className={selectStyles}>
          {realProvidersOnly.map((providerGroup) => (
            <option key={providerGroup.provider} value={providerGroup.provider}>
              {providerGroup.display_name ??
                providerGroup.provider.charAt(0).toUpperCase() + providerGroup.provider.slice(1)}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="model_id">
          Intelligence Model
        </Label>
        <select
          {...register('model_id')}
          id="model_id"
          className={selectStyles}
          disabled={!selectedProvider}
        >
          {models.map((model: string) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

/**
 * Form fields for video quality settings (resolution and frame rate).
 */
export const QualityFields = ({ register }: { register: UseFormRegister<JobFormData> }) => (
  <div className="space-y-6">
    <div className="space-y-2">
      <Label htmlFor="resolution">
        Resolution
      </Label>

      <select {...register('resolution')} id="resolution" className={selectStyles}>
        <option value="720p">720p (HD)</option>
        <option value="1080p">1080p (Full HD)</option>
      </select>
    </div>

    <div className="space-y-2">
      <Label htmlFor="frame_rate">
        Temporal Smoothness
      </Label>

      <select
        {...register('frame_rate', { valueAsNumber: true })}
        id="frame_rate"
        className={selectStyles}
      >
        <option value={30}>30 FPS Standard</option>
        <option value={60}>60 FPS Premium</option>
      </select>
    </div>
  </div>
);
