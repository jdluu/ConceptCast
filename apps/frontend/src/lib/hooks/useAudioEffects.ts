import { useCallback } from 'react';
import { useAppSettings } from '@/lib/contexts/appSettings';

export function useAudioEffects() {
  const { settings } = useAppSettings();

  const playSound = useCallback(
    (type: 'success' | 'error' | 'info') => {
      if (!settings.enableSound) return;

      const frequencies = {
        success: [440, 880],
        error: [220, 110],
        info: [660],
      };

      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;
        const notes = frequencies[type];

        notes.forEach((freq, i) => {
          osc.frequency.setValueAtTime(freq, now + i * 0.1);
        });

        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);

        osc.start(now);
        osc.stop(now + 0.3);
      } catch (e) {
        console.warn('Audio effects not supported or blocked', e);
      }
    },
    [settings.enableSound],
  );

  return { playSound };
}
