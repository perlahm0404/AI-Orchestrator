/**
 * Tailwind Preset Exports
 *
 * All theme presets for Tailwind CSS.
 */

export { cosmicPreset, default as cosmic } from './cosmic';
export { cyberpunkPreset, default as cyberpunk } from './cyberpunk';
export { neumorphicPreset, default as neumorphic } from './neumorphic';
export { futuristicPreset, default as futuristic } from './futuristic';

import { cosmicPreset } from './cosmic';
import { cyberpunkPreset } from './cyberpunk';
import { neumorphicPreset } from './neumorphic';
import { futuristicPreset } from './futuristic';

export const presets = {
  cosmic: cosmicPreset,
  cyberpunk: cyberpunkPreset,
  neumorphic: neumorphicPreset,
  futuristic: futuristicPreset,
} as const;

export type PresetName = keyof typeof presets;
