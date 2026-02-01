'use client';

import { ThemeProvider } from '@ai-orchestrator/design-system';
import { type ReactNode } from 'react';

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider defaultTheme="cosmic">
      {children}
    </ThemeProvider>
  );
}
