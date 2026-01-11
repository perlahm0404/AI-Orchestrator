# Obsidian Default App Configuration

**Last Updated**: 2026-01-10
**Status**: ✅ Active

---

## What Was Configured

All `.md` (Markdown) files on your Mac now open in Obsidian by default.

### Global Settings Applied

| File Type | Default App | Previous |
|-----------|-------------|----------|
| `.md` files | Obsidian | (varies) |
| `.txt` files | TextEdit | TextEdit (unchanged) |

### Command Used

```bash
# Installed duti (default app manager)
brew install duti

# Set Obsidian as default for .md files
duti -s md.obsidian .md all
duti -s md.obsidian net.daringfireball.markdown all

# Kept TextEdit as default for .txt files
duti -s com.apple.TextEdit .txt all
```

---

## How It Works

**When you double-click any .md file**:
- Finder opens it in Obsidian
- Works system-wide (Desktop, Downloads, anywhere)
- Applies to all .md files, including Mission Control symlinks

**If you need to open in a different app**:
- Right-click → "Open With" → Choose app
- This is a one-time override
- Default stays Obsidian

---

## Mission Control Integration

This makes Mission Control even better:

```
~/Desktop/Mission-Control/
├── CATALOG.md           ← Double-click → Opens in Obsidian ✅
├── STATE.md             ← Double-click → Opens in Obsidian ✅
├── ROADMAP.md           ← Double-click → Opens in Obsidian ✅
├── USER-PREFERENCES.md  ← Double-click → Opens in Obsidian ✅
├── DECISIONS.md         ← Double-click → Opens in Obsidian ✅
└── latest-session.md    ← Double-click → Opens in Obsidian ✅
```

All files automatically open in your Obsidian vault!

---

## Verification

Check current default apps:

```bash
# Check .md files
duti -x md

# Check .txt files
duti -x txt

# List all your custom defaults
duti -l
```

Expected output for .md:
```
Obsidian
/Applications/Obsidian.app
md.obsidian
```

---

## Changing Back (If Needed)

To restore VS Code (or another app) as default for .md files:

```bash
# For VS Code
duti -s com.microsoft.VSCode .md all

# For TextEdit
duti -s com.apple.TextEdit .md all

# For Typora
duti -s abnerworks.Typora .md all
```

To find an app's bundle ID:
```bash
osascript -e 'id of app "App Name"'
```

---

## What About Other File Types?

You can set defaults for any file type:

```bash
# Python files → VS Code
duti -s com.microsoft.VSCode .py all

# JSON files → VS Code
duti -s com.microsoft.VSCode .json all

# PDF files → Preview
duti -s com.apple.Preview .pdf all
```

---

## Tools Installed

- **duti** (v1.5.4) - Command-line utility for setting default apps
  - Installed via: `brew install duti`
  - Location: `/opt/homebrew/bin/duti`
  - Docs: https://github.com/moretension/duti

---

## Related Files

- `.desktop-pins.json` - Mission Control protection registry
- `USER-PREFERENCES.md` - Working preferences (includes Mission Control section)
- `DESKTOP-PINNING.md` - Mission Control documentation

---

**Maintained by**: System configuration
**Tool**: duti
**Scope**: Global (all .md files on Mac)
