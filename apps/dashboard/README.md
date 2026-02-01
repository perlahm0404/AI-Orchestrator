# AI Orchestrator Dashboard

Web-based monitoring and management dashboard for the AI Orchestrator system.

## Features

- **Agent Monitoring**: Real-time status of all AI agents
- **Task Management**: View and manage work queue
- **Knowledge Objects**: Browse institutional memory
- **Theme Switching**: 4 distinct visual styles (Cosmic, Cyberpunk, Neumorphic, Futuristic)

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (recommended) or npm

### Installation

```bash
# From the dashboard directory
pnpm install

# Or from monorepo root
pnpm install --filter @ai-orchestrator/dashboard
```

### Development

```bash
# Start development server on port 3100
pnpm dev

# Open http://localhost:3100
```

### Build

```bash
pnpm build
pnpm start
```

## Project Structure

```
apps/dashboard/
├── app/
│   ├── layout.tsx      # Root layout with theme provider
│   ├── page.tsx        # Dashboard home
│   ├── agents/         # Agent monitoring
│   ├── tasks/          # Task queue management
│   ├── knowledge/      # Knowledge Objects browser
│   └── settings/       # Configuration
├── components/
│   ├── layout/         # Sidebar, Header, ThemeSwitcher
│   ├── agents/         # Agent-specific components
│   ├── tasks/          # Task-specific components
│   └── ui/             # Shared UI components
├── lib/
│   └── api.ts          # API client for backend
└── public/
    └── assets/         # Static assets
```

## Theme System

The dashboard uses the `@ai-orchestrator/design-system` package for theming:

```tsx
import { useTheme } from '@ai-orchestrator/design-system';

function MyComponent() {
  const { theme, setTheme } = useTheme();

  return (
    <button onClick={() => setTheme('cyberpunk')}>
      Switch to Cyberpunk
    </button>
  );
}
```

Available themes:
- **Cosmic** (default): Deep space with galaxy vibes
- **Cyberpunk**: Neon-lit urban future
- **Neumorphic**: Soft, tactile 3D design
- **Futuristic**: Clean, minimal tech

## API Integration

The dashboard communicates with the Python orchestrator backend:

```typescript
import { agentsApi, tasksApi, knowledgeApi } from '@/lib/api';

// Fetch agents
const agents = await agentsApi.list();

// Create a task
const task = await tasksApi.create({
  title: 'Fix bug',
  description: 'Details...',
  priority: 'P1',
  project: 'karematch',
});
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## License

MIT
