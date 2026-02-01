# Design System Scripts

Python scripts for generating and managing design system assets.

## Scripts

### generate_assets.py

Generates themed visual assets using Google Gemini's AI image generation.

```bash
# Generate all assets for all themes
python generate_assets.py --all

# Generate backgrounds for cosmic theme
python generate_assets.py --theme cosmic --type backgrounds

# Dry run to preview prompts
python generate_assets.py --all --dry-run

# Update asset manifest
python generate_assets.py --manifest
```

**Requirements:**
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable
- `google-generativeai` package

### ux_pilot_converter.py

Converts UX Pilot "Deep Design" exports into React TypeScript components.

```bash
# Convert a single export file
python ux_pilot_converter.py --input ./exports/card.json --output ./components

# Process all exports in a directory
python ux_pilot_converter.py --input ./exports/ --output ./components

# Generate for a specific theme
python ux_pilot_converter.py --input ./export.json --theme cyberpunk

# Create a sample export for testing
python ux_pilot_converter.py --sample
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export GOOGLE_API_KEY="your-api-key"
```

## Asset Structure

Generated assets are organized by type and theme:

```
assets/
├── backgrounds/
│   ├── cosmic/
│   │   ├── hero.png
│   │   ├── section.png
│   │   ├── card.png
│   │   └── subtle.png
│   ├── cyberpunk/
│   ├── neumorphic/
│   └── futuristic/
├── icons/
│   ├── cosmic/
│   │   ├── dashboard.svg
│   │   ├── settings.svg
│   │   └── ...
│   └── ...
├── illustrations/
│   └── ...
└── manifest.json
```

## Theme Configurations

Each theme has specific visual characteristics:

| Theme | Style | Colors | Mood |
|-------|-------|--------|------|
| Cosmic | Deep space, galaxies | Purple, blue, dark | Ethereal, expansive |
| Cyberpunk | Neon, circuits | Pink, cyan, black | Edgy, electric |
| Neumorphic | Soft 3D | Gray, blue, white | Calm, professional |
| Futuristic | Clean geometry | Blue, white, slate | Sophisticated, minimal |
