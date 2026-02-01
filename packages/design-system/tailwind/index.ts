/**
 * Tailwind Integration
 *
 * Presets, plugins, and utilities for Tailwind CSS.
 */

export * from './presets';
export { presets, type PresetName } from './presets';

// Re-export individual presets for convenience
export { cosmicPreset } from './presets/cosmic';
export { cyberpunkPreset } from './presets/cyberpunk';
export { neumorphicPreset } from './presets/neumorphic';
export { futuristicPreset } from './presets/futuristic';
