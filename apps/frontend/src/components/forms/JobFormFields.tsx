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
 * Advanced form fields for selecting specific models for each council agent.
 */
export const AgentModelSelectionFields = ({
  register,
  providers,
}: {
  register: UseFormRegister<JobFormData>;
  providers: ProviderGroup[];
}) => {
  // Flatten all models from all providers for the selection
  const allModels = providers.flatMap((p) => p.models);
  const uniqueModels = Array.from(new Set(allModels)).toSorted();

  const AgentSelect = ({ id, label }: { id: keyof JobFormData; label: string }) => (
    <div className="space-y-2">
      <Label htmlFor={id as string}>{label}</Label>
      <select {...register(id as any)} id={id as string} className={selectStyles}>
        <option value="">Default (Global Model)</option>
        {uniqueModels.map((model) => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <AgentSelect id="analyst_model" label="Analyst Agent" />
      <AgentSelect id="validator_model" label="Validator Agent" />
      <AgentSelect id="architect_model" label="Architect Agent" />
      <AgentSelect id="animator_model" label="Animator Agent" />
    </div>
  );
};
