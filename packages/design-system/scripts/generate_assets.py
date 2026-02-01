#!/usr/bin/env python3
"""
Gemini Asset Generation Pipeline

Generates themed visual assets (backgrounds, icons, illustrations) using Google Gemini.
Each theme has distinct visual characteristics:
- Cosmic: Deep space, galaxies, nebulae, stars
- Cyberpunk: Neon grids, circuit patterns, glowing edges
- Neumorphic: Soft gradients, subtle shadows, organic shapes
- Futuristic: Clean geometry, holographic, minimalist tech

Usage:
    python generate_assets.py --theme cosmic --type backgrounds
    python generate_assets.py --all
    python generate_assets.py --theme cyberpunk --type icons --count 5
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThemeName(Enum):
    COSMIC = "cosmic"
    CYBERPUNK = "cyberpunk"
    NEUMORPHIC = "neumorphic"
    FUTURISTIC = "futuristic"


class AssetType(Enum):
    BACKGROUNDS = "backgrounds"
    ICONS = "icons"
    ILLUSTRATIONS = "illustrations"


@dataclass
class ThemePromptConfig:
    """Configuration for generating themed prompts."""
    theme: ThemeName
    style_keywords: list[str]
    color_palette: list[str]
    mood: str
    technical_style: str


# Theme configurations with detailed prompt guidance
THEME_CONFIGS: dict[ThemeName, ThemePromptConfig] = {
    ThemeName.COSMIC: ThemePromptConfig(
        theme=ThemeName.COSMIC,
        style_keywords=[
            "deep space", "galaxy", "nebula", "starfield", "aurora",
            "cosmic dust", "interstellar", "celestial", "astral"
        ],
        color_palette=["#8b5cf6", "#3b82f6", "#0a0a1a", "#1e1b4b", "#c4b5fd"],
        mood="mysterious, expansive, ethereal, awe-inspiring",
        technical_style="high contrast, glowing elements, particle effects, dark background"
    ),
    ThemeName.CYBERPUNK: ThemePromptConfig(
        theme=ThemeName.CYBERPUNK,
        style_keywords=[
            "neon", "circuit board", "holographic", "digital grid", "glitch art",
            "tech noir", "dystopian city", "LED lights", "data streams"
        ],
        color_palette=["#ec4899", "#06b6d4", "#0a0a0a", "#1a1a1a", "#f472b6"],
        mood="edgy, electric, urban, intense, rebellious",
        technical_style="scanlines, chromatic aberration, high saturation, harsh lighting"
    ),
    ThemeName.NEUMORPHIC: ThemePromptConfig(
        theme=ThemeName.NEUMORPHIC,
        style_keywords=[
            "soft shadows", "embossed", "3D tactile", "matte finish", "organic curves",
            "subtle gradients", "clay-like", "smooth surfaces", "floating elements"
        ],
        color_palette=["#e0e5ec", "#a3b1c6", "#ffffff", "#0ea5e9", "#8b5cf6"],
        mood="calm, professional, clean, approachable, modern",
        technical_style="soft lighting, diffused shadows, monochromatic, subtle depth"
    ),
    ThemeName.FUTURISTIC: ThemePromptConfig(
        theme=ThemeName.FUTURISTIC,
        style_keywords=[
            "minimalist", "geometric", "holographic interface", "clean lines",
            "transparent layers", "floating UI", "gradient mesh", "tech elegance"
        ],
        color_palette=["#3b82f6", "#ffffff", "#0f172a", "#8b5cf6", "#e0e7ff"],
        mood="sophisticated, innovative, precise, forward-thinking",
        technical_style="clean edges, subtle animations implied, glass morphism, light mode"
    ),
}


# Asset-specific prompt templates
ASSET_TEMPLATES: dict[AssetType, dict[str, Any]] = {
    AssetType.BACKGROUNDS: {
        "count": 4,
        "variants": ["hero", "section", "card", "subtle"],
        "base_prompt": (
            "Create a seamless, tileable background pattern for a web application. "
            "The design should be subtle enough to not distract from content but "
            "visually interesting. Style: {style}. Colors: {colors}. Mood: {mood}. "
            "Technical requirements: {technical}. Variant type: {variant}."
        ),
        "size": (1920, 1080),
    },
    AssetType.ICONS: {
        "count": 8,
        "variants": ["dashboard", "settings", "users", "analytics", "tasks", "brain", "rocket", "shield"],
        "base_prompt": (
            "Design a simple, recognizable icon for '{variant}' concept. "
            "The icon should work at 24x24 and 48x48 pixels. "
            "Style: {style}. Primary color: {primary_color}. "
            "Clean, modern design with consistent stroke width. "
            "Mood: {mood}. No text or labels."
        ),
        "size": (256, 256),
    },
    AssetType.ILLUSTRATIONS: {
        "count": 4,
        "variants": ["hero", "empty-state", "success", "error"],
        "base_prompt": (
            "Create an illustration for a '{variant}' state in a web application. "
            "The illustration should be friendly and professional. "
            "Style: {style}. Colors: {colors}. Mood: {mood}. "
            "The illustration should work well on both light and dark backgrounds. "
            "Include subtle {theme_keywords} elements."
        ),
        "size": (800, 600),
    },
}


class GeminiAssetGenerator:
    """
    Generates visual assets using Google Gemini's image generation API.

    Note: This requires the google-generativeai package and a valid API key.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.output_dir = Path(__file__).parent.parent / "assets"
        self._client: Any = None

    def _init_client(self) -> None:
        """Initialize the Gemini client lazily."""
        if self._client is not None:
            return

        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable."
            )

        try:
            import google.generativeai as genai  # type: ignore[import-untyped]
            genai.configure(api_key=self.api_key)
            self._client = genai
            logger.info("Gemini client initialized successfully")
        except ImportError:
            raise ImportError(
                "google-generativeai package required. Install with: pip install google-generativeai"
            )

    def _build_prompt(
        self,
        theme: ThemeName,
        asset_type: AssetType,
        variant: str
    ) -> str:
        """Build a detailed prompt for asset generation."""
        config = THEME_CONFIGS[theme]
        template_info = ASSET_TEMPLATES[asset_type]
        base_prompt: str = template_info["base_prompt"]

        prompt: str = base_prompt.format(
            style=", ".join(config.style_keywords[:4]),
            colors=", ".join(config.color_palette[:3]),
            primary_color=config.color_palette[0],
            mood=config.mood,
            technical=config.technical_style,
            variant=variant,
            theme_keywords=", ".join(config.style_keywords[:2]),
        )

        return prompt

    async def generate_asset(
        self,
        theme: ThemeName,
        asset_type: AssetType,
        variant: str,
        dry_run: bool = False
    ) -> Optional[Path]:
        """
        Generate a single asset using Gemini.

        Args:
            theme: The theme to generate for
            asset_type: Type of asset (backgrounds, icons, illustrations)
            variant: Specific variant name
            dry_run: If True, only print the prompt without generating

        Returns:
            Path to the generated asset, or None if dry_run
        """
        prompt = self._build_prompt(theme, asset_type, variant)
        output_path = self.output_dir / asset_type.value / theme.value / f"{variant}.png"

        logger.info(f"Generating {theme.value}/{asset_type.value}/{variant}")

        if dry_run:
            logger.info(f"  Prompt: {prompt[:200]}...")
            logger.info(f"  Output: {output_path}")
            return None

        self._init_client()

        try:
            # Use Gemini's image generation (Imagen 3)
            # Note: API structure may vary based on google-generativeai version
            model = self._client.GenerativeModel('gemini-1.5-flash')

            # For image generation, we'd use Imagen 3 via Vertex AI
            # This is a placeholder for the actual implementation
            logger.warning(
                "Image generation requires Vertex AI Imagen 3. "
                "Using text generation to create SVG placeholder instead."
            )

            # Generate SVG placeholder using text model
            svg_prompt = f"""Generate a simple SVG code for: {prompt}

The SVG should:
- Be exactly 200x200 viewBox
- Use these colors: {', '.join(THEME_CONFIGS[theme].color_palette[:3])}
- Be minimal and clean
- Include the theme name '{theme.value}' subtly incorporated

Return ONLY valid SVG code, nothing else. Start with <svg and end with </svg>."""

            response = model.generate_content(svg_prompt)
            svg_content = response.text.strip()

            # Extract SVG from response if wrapped in code blocks
            if "```" in svg_content:
                lines = svg_content.split("\n")
                svg_lines = []
                in_svg = False
                for line in lines:
                    if line.strip().startswith("<svg"):
                        in_svg = True
                    if in_svg:
                        svg_lines.append(line)
                    if "</svg>" in line:
                        break
                svg_content = "\n".join(svg_lines)

            # Save SVG
            output_path = output_path.with_suffix(".svg")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(svg_content)

            logger.info(f"  Generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"  Failed to generate: {e}")
            return None

    async def generate_theme_assets(
        self,
        theme: ThemeName,
        asset_type: Optional[AssetType] = None,
        dry_run: bool = False
    ) -> list[Path]:
        """Generate all assets for a theme."""
        results = []

        types_to_generate = [asset_type] if asset_type else list(AssetType)

        for atype in types_to_generate:
            template_info = ASSET_TEMPLATES[atype]
            variants = template_info["variants"]

            for variant in variants:
                result = await self.generate_asset(theme, atype, variant, dry_run)
                if result:
                    results.append(result)

        return results

    async def generate_all(self, dry_run: bool = False) -> dict[str, list[Path]]:
        """Generate all assets for all themes."""
        all_results = {}

        for theme in ThemeName:
            logger.info(f"\n{'='*50}")
            logger.info(f"Generating assets for theme: {theme.value}")
            logger.info(f"{'='*50}")

            results = await self.generate_theme_assets(theme, dry_run=dry_run)
            all_results[theme.value] = results

        return all_results


def create_manifest(output_dir: Path) -> None:
    """Create a manifest.json file listing all generated assets."""
    manifest: dict[str, Any] = {
        "version": "1.0.0",
        "generated": True,
        "themes": {}
    }

    for theme in ThemeName:
        theme_assets: dict[str, list[str]] = {"backgrounds": [], "icons": [], "illustrations": []}

        for asset_type in AssetType:
            type_dir = output_dir / asset_type.value / theme.value
            if type_dir.exists():
                files = [f.name for f in type_dir.iterdir() if f.is_file()]
                theme_assets[asset_type.value] = sorted(files)

        manifest["themes"][theme.value] = theme_assets

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Created manifest: {manifest_path}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate themed visual assets using Google Gemini"
    )
    parser.add_argument(
        "--theme",
        type=str,
        choices=[t.value for t in ThemeName],
        help="Theme to generate assets for"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=[t.value for t in AssetType],
        help="Type of assets to generate"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all assets for all themes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without generating images"
    )
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="Create/update the asset manifest"
    )

    args = parser.parse_args()

    generator = GeminiAssetGenerator()

    if args.manifest:
        create_manifest(generator.output_dir)
        return

    if args.all:
        await generator.generate_all(dry_run=args.dry_run)
    elif args.theme:
        theme = ThemeName(args.theme)
        asset_type = AssetType(args.type) if args.type else None
        await generator.generate_theme_assets(theme, asset_type, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)

    # Create manifest after generation
    if not args.dry_run:
        create_manifest(generator.output_dir)


if __name__ == "__main__":
    asyncio.run(main())
