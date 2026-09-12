import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronUp, Cpu, Send } from 'lucide-react';
import { toast } from 'sonner';
import { getAvailableModels, type JobRequest } from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useJobStore } from '@/lib/store/useJobStore';

type Option = { value: string; label: string };

function DropupSelect({
  id,
  label,
  icon,
  value,
  options,
  isOpen,
  disabled = false,
  onOpenChange,
  onChange,
}: {
  id: string;
  label: string;
  icon: React.ReactNode;
  value: string;
  options: Option[];
  isOpen: boolean;
  disabled?: boolean;
  onOpenChange: (next: boolean) => void;
  onChange: (next: string) => void;
}) {
  const selected = options.find((opt) => opt.value === value);

  return (
    <div className="relative">
      <button
        type="button"
        id={id}
        disabled={disabled}
        aria-label={label}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => {
          if (!disabled) onOpenChange(!isOpen);
        }}
        className="border-surface-border bg-surface/70 text-text-muted hover:text-foreground focus-visible:ring-council-active/40 flex w-full items-center justify-between gap-2 rounded-xl border px-3 py-2 text-xs font-semibold transition-colors outline-none disabled:cursor-not-allowed disabled:opacity-50"
      >
        <span className="flex min-w-0 items-center gap-2">
          {icon}
          <span className="truncate">{selected?.label ?? label}</span>
        </span>
        <ChevronUp className={`h-3.5 w-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && !disabled && (
        <div className="border-surface-border bg-surface absolute bottom-full left-0 z-20 mb-2 w-full overflow-hidden rounded-xl border shadow-xl">
          <ul role="listbox" aria-labelledby={id} className="max-h-56 overflow-y-auto py-1">
            {options.map((opt) => (
              <li key={opt.value}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(opt.value);
                    onOpenChange(false);
                  }}
                  className={`w-full px-3 py-2 text-left text-sm transition-colors ${
                    value === opt.value
                      ? 'bg-council-active/10 text-council-active'
                      : 'text-foreground hover:bg-surface-border/60'
                  }`}
                >
                  {opt.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function ChatLaunchForm() {
  const rootRef = useRef<HTMLFormElement>(null);
  const { developerMode } = useDeveloperMode();
  const { createJob, isSubmitting } = useJobStore();
  const [topic, setTopic] = useState('');
  const [openMenu, setOpenMenu] = useState<'provider' | 'model' | null>(null);

  const { data } = useQuery({
    queryKey: ['models'],
    queryFn: getAvailableModels,
    staleTime: 1000 * 60 * 5,
  });

  const availableGroups = data?.available ?? [];
  const filteredGroups = developerMode
    ? availableGroups
    : availableGroups.filter((group) => group.provider !== 'mock');

  const hasAnyProvider = filteredGroups.length > 0;

  const providerOptions = useMemo<Option[]>(
    () =>
      filteredGroups.map((group) => ({
        value: group.provider,
        label:
          group.display_name ??
          group.provider.charAt(0).toUpperCase() + group.provider.slice(1).toLowerCase(),
      })),
    [filteredGroups],
  );

  const [provider, setProvider] = useState('');
  const [modelId, setModelId] = useState('');

  useEffect(() => {
    if (!providerOptions.length) {
      setProvider('');
      setModelId('');
      return;
    }

    if (!providerOptions.some((opt) => opt.value === provider)) {
      const nextProvider = providerOptions[0].value;
      setProvider(nextProvider);
      const nextModels =
        filteredGroups.find((group) => group.provider === nextProvider)?.models ?? [];
      setModelId(nextModels[0] ?? '');
    }
  }, [providerOptions, provider, filteredGroups]);

  useEffect(() => {
    if (!provider) return;
    const models = filteredGroups.find((group) => group.provider === provider)?.models ?? [];
    if (!models.length) {
      setModelId('');
      return;
    }
    if (!models.includes(modelId)) {
      setModelId(models[0]);
    }
  }, [provider, modelId, filteredGroups]);

  useEffect(() => {
    const onClickOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpenMenu(null);
      }
    };
    window.addEventListener('mousedown', onClickOutside);
    return () => window.removeEventListener('mousedown', onClickOutside);
  }, []);

  const modelOptions = useMemo<Option[]>(() => {
    const models = filteredGroups.find((group) => group.provider === provider)?.models ?? [];
    return models.map((model) => ({ value: model, label: model }));
  }, [filteredGroups, provider]);

  const submitDisabled =
    isSubmitting || !hasAnyProvider || !provider || !modelId || topic.trim().length < 3;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmedTopic = topic.trim();

    if (trimmedTopic.length < 3) {
      toast.error('Please enter a topic with at least 3 characters.');
      return;
    }

    if (!provider || !modelId) {
      toast.error('Please select a provider and model.');
      return;
    }

    const request: JobRequest = {
      topic: trimmedTopic,
      provider,
      model_id: modelId,
    };

    try {
      await createJob(request);
    } catch (error) {
      console.error('Failed to create job from chat launch form:', error);
      toast.error('Unable to start generation. Please check your backend connection.');
    }
  };

  return (
    <section className="mx-auto flex min-h-[72vh] w-full max-w-5xl flex-col items-center justify-center px-4">
      <div className="mb-10 max-w-2xl space-y-4 text-center">
        <h1 className="text-foreground text-3xl font-bold tracking-tight sm:text-4xl">
          Build educational videos from a single prompt
        </h1>
        <p className="text-text-muted text-sm sm:text-base">
          ConceptCast coordinates specialist AI agents to plan a curriculum, design a storyboard,
          generate Manim code, and render a final explainer video.
        </p>
      </div>

      <form
        ref={rootRef}
        onSubmit={onSubmit}
        className="border-surface-border bg-surface/60 w-full max-w-3xl rounded-2xl border p-4 shadow-2xl backdrop-blur-sm sm:p-5"
      >
        <div className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <DropupSelect
            id="provider-menu"
            label="Provider"
            icon={<Cpu className="h-3.5 w-3.5" />}
            value={provider}
            options={providerOptions}
            isOpen={openMenu === 'provider'}
            disabled={!providerOptions.length || isSubmitting}
            onOpenChange={(next) => setOpenMenu(next ? 'provider' : null)}
            onChange={(nextProvider) => {
              setProvider(nextProvider);
              const nextModels =
                filteredGroups.find((group) => group.provider === nextProvider)?.models ?? [];
              setModelId(nextModels[0] ?? '');
            }}
          />

          <DropupSelect
            id="model-menu"
            label="Model"
            icon={<Cpu className="h-3.5 w-3.5" />}
            value={modelId}
            options={modelOptions}
            isOpen={openMenu === 'model'}
            disabled={!modelOptions.length || isSubmitting}
            onOpenChange={(next) => setOpenMenu(next ? 'model' : null)}
            onChange={setModelId}
          />
        </div>

        <div className="border-surface-border bg-background/70 focus-within:border-council-active/40 flex items-end gap-2 rounded-xl border px-3 py-2">
          <textarea
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Type a topic to generate a lesson video..."
            rows={2}
            className="text-foreground placeholder:text-text-muted max-h-44 min-h-[2.5rem] w-full resize-y bg-transparent py-1 text-sm outline-none"
          />
          <button
            type="submit"
            disabled={submitDisabled}
            className="bg-council-active hover:bg-council-active/90 disabled:bg-surface-border flex h-10 w-10 items-center justify-center rounded-lg text-white transition-colors disabled:cursor-not-allowed disabled:text-gray-400"
            aria-label="Start generation"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        {!hasAnyProvider && (
          <p className="text-warning mt-3 text-xs">
            No live providers are configured. Add provider keys in your environment (or use
            Developer mode for mock runs).
          </p>
        )}
      </form>
    </section>
  );
}
