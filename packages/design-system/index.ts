/**
 * AI Orchestrator Design System
 *
 * Multi-theme design system with Cosmic, Cyberpunk, Neumorphic, and Futuristic styles.
 *
 * @example
 * ```tsx
 * import { ThemeProvider, useTheme, cn } from '@ai-orchestrator/design-system';
 * import { cosmicPreset } from '@ai-orchestrator/design-system/tailwind';
 *
 * // In your app
 * function App() {
 *   return (
 *     <ThemeProvider defaultTheme="cosmic">
 *       <YourApp />
 *     </ThemeProvider>
 *   );
 * }
 *
 * // In a component
 * function Button({ className, ...props }) {
 *   const { theme } = useTheme();
 *   return (
 *     <button
 *       className={cn(
 *         'px-4 py-2 rounded-lg bg-primary-500 text-white',
 *         className
 *       )}
 *       {...props}
 *     />
 *   );
 * }
 * ```
 */

// Tokens
export * from './tokens';

// Library utilities
export * from './lib';

// Tailwind integration
export * from './tailwind';

// Version
export const VERSION = '0.1.0';
