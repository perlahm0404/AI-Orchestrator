import type { Config } from 'tailwindcss';
import { cosmicPreset } from '@ai-orchestrator/design-system/tailwind';

const config: Config = {
  presets: [cosmicPreset],
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
    // Include design system components
    '../../packages/design-system/**/*.{js,ts,jsx,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Dashboard-specific extensions
      width: {
        'sidebar': '280px',
        'sidebar-collapsed': '80px',
      },
      height: {
        'header': '64px',
      },
      zIndex: {
        'sidebar': '40',
        'header': '50',
        'modal': '100',
      },
    },
  },
  plugins: [],
};

export default config;
