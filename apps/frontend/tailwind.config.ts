import { colors, spacing, typography, radius, sizes } from './src/lib/tokens';

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors,
      spacing,
      fontSize: typography,
      borderRadius: radius,
      minHeight: sizes,
      maxHeight: sizes,
      minWidth: sizes,
      maxWidth: sizes,
    },
  },
  plugins: [],
};
