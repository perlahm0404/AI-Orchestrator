import { defineConfig } from 'tsup';

export default defineConfig({
  entry: {
    index: 'index.ts',
    'tokens/index': 'tokens/index.ts',
    'tokens/colors/cosmic': 'tokens/colors/cosmic.ts',
    'tokens/colors/cyberpunk': 'tokens/colors/cyberpunk.ts',
    'tokens/colors/neumorphic': 'tokens/colors/neumorphic.ts',
    'tokens/colors/futuristic': 'tokens/colors/futuristic.ts',
    'tailwind/index': 'tailwind/index.ts',
    'tailwind/presets/cosmic': 'tailwind/presets/cosmic.ts',
    'tailwind/presets/cyberpunk': 'tailwind/presets/cyberpunk.ts',
    'tailwind/presets/neumorphic': 'tailwind/presets/neumorphic.ts',
    'tailwind/presets/futuristic': 'tailwind/presets/futuristic.ts',
    'lib/index': 'lib/index.ts',
  },
  format: ['cjs', 'esm'],
  dts: true,
  clean: true,
  sourcemap: true,
  splitting: false,
  treeshake: true,
  external: ['react', 'react-dom', 'tailwindcss', 'framer-motion'],
  esbuildOptions(options) {
    options.banner = {
      js: '"use client";',
    };
  },
});
