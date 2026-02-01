/**
 * Color Token Exports
 *
 * All theme color palettes in one place.
 */

export { cosmic, type CosmicTheme } from './cosmic';
export { cyberpunk, type CyberpunkTheme } from './cyberpunk';
export { neumorphic, type NeumorphicTheme } from './neumorphic';
export { futuristic, type FuturisticTheme } from './futuristic';

import { cosmic } from './cosmic';
import { cyberpunk } from './cyberpunk';
import { neumorphic } from './neumorphic';
import { futuristic } from './futuristic';

export const themes = {
  cosmic,
  cyberpunk,
  neumorphic,
  futuristic,
} as const;

export type ThemeName = keyof typeof themes;
export type Theme = (typeof themes)[ThemeName];
