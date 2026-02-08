# UI Scaffold

**Command**: `/ui-scaffold`

**Description**: Generate production-ready React components with Radix UI, Tailwind CSS, CVA variants, and built-in accessibility

## What This Does

Generates complete, production-ready UI components:

1. **Pattern-to-Component Mapping** - Describe what you need, get the right component structure
2. **TSX Templates** - TypeScript-first with full type definitions
3. **CVA Variants** - class-variance-authority for type-safe styling
4. **Accessibility Built-in** - ARIA, keyboard nav, focus management by default
5. **Storybook Stories** - Auto-generated stories for documentation

## Component Library Stack

```
Base: Radix UI Primitives
Styling: Tailwind CSS + CVA
Icons: Lucide React
Animation: Tailwind Animate + Framer Motion (optional)
Forms: React Hook Form + Zod
```

## Pattern-to-Component Mapping

Describe your use case, get the optimal component structure:

| Pattern | Components | Notes |
|---------|------------|-------|
| `data_table_filterable` | DataTable, TableFilters, Pagination | Virtualized for large sets |
| `form_wizard` | FormWizard, FormStep, FormProgress | Multi-step with validation |
| `status_dashboard` | StatCard, StatusGrid, AlertBanner | KPI display |
| `document_upload` | DropZone, FileList, UploadProgress | Drag-and-drop |
| `user_profile` | Avatar, ProfileCard, EditableField | Editable inline |
| `notification_center` | NotificationBell, NotificationList, NotificationItem | Real-time |
| `settings_panel` | SettingsNav, SettingsSection, Toggle | Grouped settings |
| `modal_form` | Dialog, FormContent, FormActions | Form inside modal |
| `command_palette` | CommandDialog, CommandList, CommandItem | Keyboard-first |
| `sidebar_nav` | Sidebar, NavGroup, NavItem | Collapsible |
| `breadcrumb_nav` | Breadcrumb, BreadcrumbItem, BreadcrumbSeparator | Hierarchy |
| `date_picker` | Calendar, DateInput, DateRange | With presets |
| `search_autocomplete` | SearchInput, SearchResults, SearchItem | Async search |
| `kanban_board` | KanbanBoard, KanbanColumn, KanbanCard | Drag-and-drop |
| `timeline` | Timeline, TimelineItem, TimelineConnector | Event sequence |

## Usage

```bash
# Scaffold from pattern
/ui-scaffold data_table_filterable

# Scaffold with customization
/ui-scaffold form_wizard --steps 4 --validation zod

# Scaffold single component
/ui-scaffold component Button --variants "primary,secondary,ghost,destructive"

# Scaffold with Storybook stories
/ui-scaffold data_table_filterable --with-stories

# Scaffold to specific directory
/ui-scaffold modal_form --output src/components/modals/

# List available patterns
/ui-scaffold list
```

## Output Structure

For `/ui-scaffold data_table_filterable`:

```
src/components/data-table/
├── index.ts                    # Barrel export
├── data-table.tsx             # Main component
├── data-table.types.ts        # TypeScript types
├── table-filters.tsx          # Filter controls
├── table-pagination.tsx       # Pagination
├── table-header.tsx           # Sortable headers
├── table-row.tsx              # Row component
├── use-data-table.ts          # Hook for state
└── data-table.stories.tsx     # Storybook stories
```

## Component Template: Button

Example of generated component structure:

```tsx
// button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Base styles
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <>
            <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            <span>Loading...</span>
          </>
        ) : (
          children
        )}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

## Complex Pattern: Form Wizard

```tsx
// form-wizard.tsx
import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface FormWizardStep {
  id: string
  title: string
  description?: string
  component: React.ComponentType<FormStepProps>
  validation?: () => Promise<boolean> | boolean
}

interface FormWizardProps {
  steps: FormWizardStep[]
  onComplete: (data: Record<string, unknown>) => void
  onCancel?: () => void
  className?: string
}

interface FormStepProps {
  data: Record<string, unknown>
  updateData: (updates: Record<string, unknown>) => void
  errors: Record<string, string>
}

export function FormWizard({ steps, onComplete, onCancel, className }: FormWizardProps) {
  const [currentStep, setCurrentStep] = React.useState(0)
  const [data, setData] = React.useState<Record<string, unknown>>({})
  const [errors, setErrors] = React.useState<Record<string, string>>({})
  const [isValidating, setIsValidating] = React.useState(false)

  const step = steps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === steps.length - 1
  const progress = ((currentStep + 1) / steps.length) * 100

  const updateData = React.useCallback((updates: Record<string, unknown>) => {
    setData((prev) => ({ ...prev, ...updates }))
    // Clear errors for updated fields
    setErrors((prev) => {
      const next = { ...prev }
      Object.keys(updates).forEach((key) => delete next[key])
      return next
    })
  }, [])

  const handleNext = async () => {
    if (step.validation) {
      setIsValidating(true)
      try {
        const isValid = await step.validation()
        if (!isValid) {
          setIsValidating(false)
          return
        }
      } catch (error) {
        setIsValidating(false)
        return
      }
      setIsValidating(false)
    }

    if (isLastStep) {
      onComplete(data)
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handleBack = () => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1)
    }
  }

  const StepComponent = step.component

  return (
    <div className={cn("space-y-6", className)}>
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            Step {currentStep + 1} of {steps.length}
          </span>
          <span className="font-medium">{step.title}</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step indicators */}
      <nav aria-label="Progress steps" className="flex justify-center gap-2">
        {steps.map((s, index) => (
          <div
            key={s.id}
            className={cn(
              "h-2 w-2 rounded-full transition-colors",
              index === currentStep
                ? "bg-primary"
                : index < currentStep
                ? "bg-primary/50"
                : "bg-muted"
            )}
            aria-current={index === currentStep ? "step" : undefined}
          />
        ))}
      </nav>

      {/* Step content */}
      <div className="min-h-[300px]">
        <StepComponent data={data} updateData={updateData} errors={errors} />
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <div>
          {onCancel && (
            <Button variant="ghost" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          {!isFirstStep && (
            <Button variant="outline" onClick={handleBack}>
              Back
            </Button>
          )}
          <Button onClick={handleNext} disabled={isValidating}>
            {isValidating ? "Validating..." : isLastStep ? "Complete" : "Next"}
          </Button>
        </div>
      </div>
    </div>
  )
}
```

## Accessibility Features

Every scaffolded component includes:

### Keyboard Navigation
```tsx
// Built into all interactive components
onKeyDown={(e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault()
    handleAction()
  }
  if (e.key === "Escape") {
    handleClose()
  }
}}
```

### Focus Management
```tsx
// Auto-focus and focus trapping for modals
const firstFocusableRef = React.useRef<HTMLButtonElement>(null)

React.useEffect(() => {
  if (isOpen) {
    firstFocusableRef.current?.focus()
  }
}, [isOpen])
```

### ARIA Attributes
```tsx
// Proper labeling and state
<button
  aria-expanded={isOpen}
  aria-controls="dropdown-content"
  aria-haspopup="listbox"
  aria-label={label}
/>
<div
  id="dropdown-content"
  role="listbox"
  aria-labelledby="dropdown-trigger"
/>
```

### Screen Reader Text
```tsx
// Visually hidden but accessible
<span className="sr-only">
  {itemCount} items selected
</span>
```

## Storybook Stories

Auto-generated with each scaffold:

```tsx
// button.stories.tsx
import type { Meta, StoryObj } from "@storybook/react"
import { Button } from "./button"

const meta: Meta<typeof Button> = {
  title: "Components/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "destructive", "outline", "secondary", "ghost", "link"],
    },
    size: {
      control: "select",
      options: ["default", "sm", "lg", "icon"],
    },
    loading: { control: "boolean" },
    disabled: { control: "boolean" },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {
  args: {
    children: "Button",
  },
}

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Button variant="default">Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
}

export const Loading: Story = {
  args: {
    children: "Submit",
    loading: true,
  },
}

export const Disabled: Story = {
  args: {
    children: "Disabled",
    disabled: true,
  },
}
```

## Integration with Design Direction

When used after `/ui-design`:

```bash
# Scaffold with design direction context
/ui-scaffold data_table_filterable --direction neo-corporate
```

Generates components that follow the established:
- Typography scale
- Color tokens
- Spacing system
- Border radius
- Shadow definitions
- Animation timing

## Quality Scoring

After scaffolding, components are auto-linted:

```
SCAFFOLD COMPLETE: data_table_filterable
────────────────────────────────────────

Files generated: 8
Lines of code: 847

Quality Score: 94/100
├── Accessibility: 100/100 ✓
├── Type Safety: 100/100 ✓
├── Design Tokens: 90/100 (2 warnings)
└── Performance: 85/100 (virtualization recommended)

Warnings:
- Line 45: Consider React.memo for TableRow
- Line 89: Large dataset may need virtualization
```

## Related

- `/ui-lint` - Validate generated components
- `/ui-design` - Establish design direction first
- `/code-review` - Full review of scaffolded code
- `aibrain ko search --tags component,react,accessibility`
