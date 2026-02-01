#!/usr/bin/env python3
"""
UX Pilot Component Converter

Converts exported UX Pilot components into React/TypeScript components
that integrate with the AI Orchestrator design system.

UX Pilot "Deep Design" mode exports components as:
- Figma designs (JSON export)
- HTML/CSS snippets
- Design tokens (JSON)

This script processes those exports and generates:
- React TypeScript components
- Tailwind CSS classes
- Framer Motion animation variants
- Storybook stories

Usage:
    python ux_pilot_converter.py --input ./exports/ux-pilot --output ./components
    python ux_pilot_converter.py --input ./card-export.json --component Card
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DesignToken:
    """Represents a design token from UX Pilot export."""
    name: str
    value: str
    type: str  # color, spacing, typography, shadow, etc.
    theme: Optional[str] = None


@dataclass
class ComponentSpec:
    """Specification for a React component."""
    name: str
    display_name: str
    description: str
    props: dict[str, Any] = field(default_factory=dict)
    variants: list[str] = field(default_factory=list)
    styles: dict[str, str] = field(default_factory=dict)
    animations: dict[str, Any] = field(default_factory=dict)
    children: bool = True
    ref_forwarding: bool = True


# CSS to Tailwind mapping
CSS_TO_TAILWIND: dict[str, dict[str, str]] = {
    "display": {"flex": "flex", "grid": "grid", "block": "block", "inline": "inline"},
    "flex-direction": {"row": "flex-row", "column": "flex-col"},
    "justify-content": {
        "center": "justify-center",
        "space-between": "justify-between",
        "flex-start": "justify-start",
        "flex-end": "justify-end",
    },
    "align-items": {
        "center": "items-center",
        "flex-start": "items-start",
        "flex-end": "items-end",
        "stretch": "items-stretch",
    },
    "border-radius": {
        "4px": "rounded",
        "8px": "rounded-lg",
        "12px": "rounded-xl",
        "16px": "rounded-2xl",
        "9999px": "rounded-full",
    },
    "font-weight": {
        "400": "font-normal",
        "500": "font-medium",
        "600": "font-semibold",
        "700": "font-bold",
    },
}


def css_value_to_tailwind(property_name: str, value: str) -> Optional[str]:
    """Convert a CSS property-value pair to Tailwind class."""
    if property_name in CSS_TO_TAILWIND:
        return CSS_TO_TAILWIND[property_name].get(value)

    # Handle spacing values
    if property_name in ("padding", "margin", "gap"):
        px_match = re.match(r"(\d+)px", value)
        if px_match:
            px = int(px_match.group(1))
            # Convert px to Tailwind spacing units (4px = 1 unit)
            unit = px // 4
            prefix = {"padding": "p", "margin": "m", "gap": "gap"}[property_name]
            return f"{prefix}-{unit}"

    # Handle colors (simplified - would need actual color mapping)
    if property_name in ("color", "background-color", "border-color"):
        if value.startswith("#") or value.startswith("rgb"):
            # Would map to design system colors
            return None

    return None


def parse_ux_pilot_export(file_path: Path) -> dict[str, Any]:
    """Parse a UX Pilot export file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Export file not found: {file_path}")

    with open(file_path) as file_handle:
        data: dict[str, Any] = json.load(file_handle)

    logger.info(f"Parsed UX Pilot export: {file_path.name}")
    return data


def extract_design_tokens(export_data: dict[str, Any]) -> list[DesignToken]:
    """Extract design tokens from UX Pilot export."""
    tokens = []

    # Handle different export formats
    if "tokens" in export_data:
        for token_data in export_data["tokens"]:
            tokens.append(DesignToken(
                name=token_data.get("name", ""),
                value=token_data.get("value", ""),
                type=token_data.get("type", "unknown"),
                theme=token_data.get("theme"),
            ))
    elif "designTokens" in export_data:
        for category, values in export_data["designTokens"].items():
            if isinstance(values, dict):
                for name, value in values.items():
                    tokens.append(DesignToken(
                        name=f"{category}-{name}",
                        value=str(value),
                        type=category,
                    ))

    logger.info(f"Extracted {len(tokens)} design tokens")
    return tokens


def extract_component_spec(
    export_data: dict[str, Any],
    component_name: str
) -> ComponentSpec:
    """Extract component specification from UX Pilot export."""
    # Find component in export
    component_data = None
    if "components" in export_data:
        for comp in export_data["components"]:
            if comp.get("name") == component_name:
                component_data = comp
                break

    if not component_data:
        component_data = export_data

    # Extract specification
    spec = ComponentSpec(
        name=component_name,
        display_name=component_data.get("displayName", component_name),
        description=component_data.get("description", f"A {component_name} component"),
        props=component_data.get("props", {}),
        variants=component_data.get("variants", []),
        styles=component_data.get("styles", {}),
        animations=component_data.get("animations", {}),
        children=component_data.get("hasChildren", True),
        ref_forwarding=component_data.get("refForwarding", True),
    )

    return spec


def generate_react_component(spec: ComponentSpec, theme: str = "cosmic") -> str:
    """Generate a React TypeScript component from specification."""

    # Build props interface
    props_lines = []
    for prop_name, prop_info in spec.props.items():
        prop_type = prop_info.get("type", "string")
        optional = "?" if not prop_info.get("required", False) else ""
        props_lines.append(f"  {prop_name}{optional}: {prop_type};")

    if spec.children:
        props_lines.append("  children?: React.ReactNode;")
    props_lines.append("  className?: string;")

    props_interface = "\n".join(props_lines)

    # Build variant classes
    variant_classes = {}
    for variant in spec.variants:
        variant_classes[variant] = f"variant-{variant}"

    # Build Tailwind classes from styles
    tailwind_classes = []
    for prop, value in spec.styles.items():
        tw_class = css_value_to_tailwind(prop, value)
        if tw_class:
            tailwind_classes.append(tw_class)

    base_classes = " ".join(tailwind_classes) if tailwind_classes else "p-4 rounded-lg"

    # Build Framer Motion variants
    animation_variants = ""
    if spec.animations:
        animation_variants = f"""
const motionVariants = {{
  initial: {{ opacity: 0, y: 10 }},
  animate: {{ opacity: 1, y: 0 }},
  exit: {{ opacity: 0, y: -10 }},
  hover: {{ scale: 1.02 }},
  tap: {{ scale: 0.98 }},
}};
"""

    # Generate component code
    component_code = f'''/**
 * {spec.display_name}
 *
 * {spec.description}
 *
 * @generated from UX Pilot export
 * @theme {theme}
 */

'use client';

import {{ forwardRef }} from 'react';
import {{ motion, type HTMLMotionProps }} from 'framer-motion';
import {{ cn }} from '@ai-orchestrator/design-system';

interface {spec.name}Props extends Omit<HTMLMotionProps<'div'>, 'children'> {{
{props_interface}
}}
{animation_variants}
const {spec.name} = forwardRef<HTMLDivElement, {spec.name}Props>(
  ({{ className, children, ...props }}, ref) => {{
    return (
      <motion.div
        ref={{ref}}
        className={{cn(
          '{base_classes}',
          'bg-background-card border border-border',
          'transition-all duration-200',
          className
        )}}
        variants={{motionVariants}}
        initial="initial"
        animate="animate"
        whileHover="hover"
        whileTap="tap"
        {{...props}}
      >
        {{children}}
      </motion.div>
    );
  }}
);

{spec.name}.displayName = '{spec.name}';

export {{ {spec.name} }};
export type {{ {spec.name}Props }};
'''

    return component_code


def generate_storybook_story(spec: ComponentSpec) -> str:
    """Generate a Storybook story for the component."""

    story_code = f'''import type {{ Meta, StoryObj }} from '@storybook/react';
import {{ {spec.name} }} from './{spec.name}';

const meta: Meta<typeof {spec.name}> = {{
  title: 'Components/{spec.name}',
  component: {spec.name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
  argTypes: {{
    // Add argTypes based on props
  }},
}};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {{
  args: {{
    children: 'Example content',
  }},
}};

export const WithVariants: Story = {{
  render: () => (
    <div className="flex gap-4">
      <{spec.name}>Variant Example</{spec.name}>
    </div>
  ),
}};
'''

    return story_code


def process_export(
    input_path: Path,
    output_dir: Path,
    component_name: Optional[str] = None,
    theme: str = "cosmic"
) -> list[Path]:
    """Process a UX Pilot export and generate components."""
    generated_files = []

    # Parse export
    export_data = parse_ux_pilot_export(input_path)

    # Extract design tokens
    tokens = extract_design_tokens(export_data)
    if tokens:
        tokens_path = output_dir / "tokens.json"
        tokens_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tokens_path, "w") as tokens_file:
            json.dump(
                [{"name": t.name, "value": t.value, "type": t.type} for t in tokens],
                tokens_file,
                indent=2
            )
        generated_files.append(tokens_path)
        logger.info(f"Generated: {tokens_path}")

    # Determine components to generate
    if component_name:
        component_names = [component_name]
    elif "components" in export_data:
        component_names = [c["name"] for c in export_data["components"]]
    else:
        # Use filename as component name
        component_names = [input_path.stem.replace("-", "").title()]

    # Generate each component
    for name in component_names:
        spec = extract_component_spec(export_data, name)

        # Generate React component
        component_code = generate_react_component(spec, theme)
        component_path = output_dir / f"{name}.tsx"
        component_path.write_text(component_code)
        generated_files.append(component_path)
        logger.info(f"Generated: {component_path}")

        # Generate Storybook story
        story_code = generate_storybook_story(spec)
        story_path = output_dir / f"{name}.stories.tsx"
        story_path.write_text(story_code)
        generated_files.append(story_path)
        logger.info(f"Generated: {story_path}")

    return generated_files


def create_sample_export() -> dict[str, Any]:
    """Create a sample UX Pilot export for testing."""
    return {
        "exportVersion": "1.0",
        "source": "UX Pilot Deep Design",
        "components": [
            {
                "name": "FeatureCard",
                "displayName": "Feature Card",
                "description": "A card component for displaying features with icon, title, and description",
                "props": {
                    "title": {"type": "string", "required": True},
                    "description": {"type": "string", "required": False},
                    "icon": {"type": "React.ReactNode", "required": False},
                    "variant": {"type": "'default' | 'highlighted' | 'muted'", "required": False},
                },
                "variants": ["default", "highlighted", "muted"],
                "styles": {
                    "display": "flex",
                    "flex-direction": "column",
                    "padding": "24px",
                    "border-radius": "16px",
                    "gap": "16px",
                },
                "animations": {
                    "entrance": "fadeInUp",
                    "hover": "scaleUp",
                },
                "hasChildren": True,
                "refForwarding": True,
            }
        ],
        "designTokens": {
            "colors": {
                "primary": "#8b5cf6",
                "secondary": "#3b82f6",
                "background": "#0a0a1a",
            },
            "spacing": {
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
            },
            "borderRadius": {
                "sm": "4px",
                "md": "8px",
                "lg": "16px",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert UX Pilot exports to React components"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to UX Pilot export file or directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./components"),
        help="Output directory for generated components"
    )
    parser.add_argument(
        "--component",
        type=str,
        help="Specific component name to generate"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="cosmic",
        choices=["cosmic", "cyberpunk", "neumorphic", "futuristic"],
        help="Theme to use for component styling"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Create a sample export file for testing"
    )

    args = parser.parse_args()

    if args.sample:
        sample = create_sample_export()
        sample_path = Path("./sample-ux-pilot-export.json")
        with open(sample_path, "w") as sample_file:
            json.dump(sample, sample_file, indent=2)
        logger.info(f"Created sample export: {sample_path}")
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    # Process input
    if args.input.is_file():
        generated = process_export(
            args.input,
            args.output,
            args.component,
            args.theme
        )
    elif args.input.is_dir():
        generated = []
        for export_file in args.input.glob("*.json"):
            generated.extend(process_export(
                export_file,
                args.output,
                args.component,
                args.theme
            ))
    else:
        logger.error(f"Input path not found: {args.input}")
        sys.exit(1)

    logger.info(f"\nGenerated {len(generated)} files")
    for generated_file in generated:
        logger.info(f"  - {generated_file}")


if __name__ == "__main__":
    main()
