# System Configuration - AI Orchestrator

**Last Updated**: 2026-01-10
**Purpose**: Documents all system-level changes made for AI Orchestrator functionality

> **Important**: All configurations listed here persist across reboots and are permanent until manually removed.

---

## 🚀 Mission Control Desktop Folder

**Location**: `~/Desktop/Mission-Control/`

**What it contains**:
```
Mission-Control/
├── CATALOG.md           → ~/Workspace/docs-hub/CATALOG.md → AI_Orchestrator/CATALOG.md
├── STATE.md             → ~/Workspace/docs-hub/STATE.md → AI_Orchestrator/STATE.md
├── ROADMAP.md           → ~/Workspace/docs-hub/ROADMAP.md → AI_Orchestrator/ROADMAP.md
├── USER-PREFERENCES.md  → ~/Workspace/docs-hub/USER-PREFERENCES.md
├── DECISIONS.md         → ~/Workspace/docs-hub/DECISIONS.md
└── latest-session.md    → ~/Workspace/docs-hub/latest-session.md
```

**Persistence**: ✅ Symlinks persist across reboots
**Backup**: If deleted, recreate with commands in [DESKTOP-PINNING.md](./DESKTOP-PINNING.md)

---

## 📝 Default App for .md Files

**Current Setting**: All `.md` files open in ObsidianOpener → Obsidian

**How to check**:
```bash
duti -x md
```

Expected output:
```
ObsidianOpener
/Users/tmac/Applications/ObsidianOpener.app
com.tmac.obsidianopener
```

**Persistence**: ✅ Stored in `~/Library/Preferences/com.apple.LaunchServices/`

**To restore if lost**:
```bash
duti -s com.tmac.obsidianopener .md all
duti -s com.tmac.obsidianopener net.daringfireball.markdown all
```

**To change back to Obsidian directly**:
```bash
duti -s md.obsidian .md all
```

**To change to VS Code**:
```bash
duti -s com.microsoft.VSCode .md all
```

---

## 🛠️ Created Applications

### ObsidianOpener.app

**Location**: `~/Applications/ObsidianOpener.app/`

**Purpose**: Wrapper app that opens .md files in Obsidian AND brings window to front

**Structure**:
```
ObsidianOpener.app/
├── Contents/
│   ├── Info.plist          (Bundle metadata)
│   ├── MacOS/
│   │   └── obsidian-opener (Executable script)
│   └── Resources/          (Empty)
```

**Bundle ID**: `com.tmac.obsidianopener`

**Persistence**: ✅ App bundle persists across reboots

**To verify it's registered**:
```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -dump | grep obsidianopener
```

**To re-register if needed**:
```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f ~/Applications/ObsidianOpener.app
```

---

## 📜 Created Scripts

### 1. Library Scripts (macOS standard location)

**Location**: `~/Library/Scripts/`

| Script | Purpose |
|--------|---------|
| `open-in-obsidian.sh` | Opens file in Obsidian with activation |
| `obsidian-opener.sh` | Multi-file handler with activation |

**Persistence**: ✅ Files persist across reboots

### 2. User Bin Scripts (terminal commands)

**Location**: `~/bin/`

**Prerequisites**: `~/bin` must be in your PATH. Check with:
```bash
echo $PATH | grep -o "$HOME/bin"
```

If not in PATH, add to `~/.zshrc`:
```bash
export PATH="$HOME/bin:$PATH"
```

| Script | Purpose | Usage |
|--------|---------|-------|
| `obs` | Activate Obsidian window | `obs` |
| `obsidian-open` | Open file + activate | `obsidian-open file.md` |
| `obsidian-activate` | Bring Obsidian to front | `obsidian-activate` |

**Persistence**: ✅ Files persist across reboots
**PATH requirement**: ⚠️  `~/bin` must be in PATH (see above)

---

## 🔧 Installed Tools

### duti (Default App Manager)

**Installed via**: Homebrew
**Location**: `/opt/homebrew/bin/duti`
**Version**: 1.5.4

**Purpose**: Set default applications for file types

**Common commands**:
```bash
# Check default app for .md files
duti -x md

# List all custom defaults
duti -l

# Set new default
duti -s BUNDLE_ID .EXTENSION all
```

**Persistence**: ✅ Installed via Homebrew, persists across reboots

**To verify installation**:
```bash
which duti
duti --version
```

**To reinstall if missing**:
```bash
brew install duti
```

---

## 📂 Obsidian Vault Integration

### docs-hub Vault Files

**Location**: `~/Workspace/docs-hub/`

**Symlinks created**:
```bash
docs-hub/CATALOG.md → /Users/tmac/1_REPOS/AI_Orchestrator/CATALOG.md
docs-hub/STATE.md → /Users/tmac/1_REPOS/AI_Orchestrator/STATE.md
docs-hub/ROADMAP.md → /Users/tmac/1_REPOS/AI_Orchestrator/ROADMAP.md
docs-hub/USER-PREFERENCES.md → /Users/tmac/1_REPOS/AI_Orchestrator/USER-PREFERENCES.md
docs-hub/DECISIONS.md → /Users/tmac/1_REPOS/AI_Orchestrator/DECISIONS.md
docs-hub/latest-session.md → /Users/tmac/1_REPOS/AI_Orchestrator/sessions/latest.md
```

**Persistence**: ✅ Symlinks persist across reboots

**Why vault integration?**:
- Obsidian only fully supports files inside vaults
- Enables graph view, wikilinks, vault search
- Files still live in git repo, vault just has symlinks

---

## 🗂️ Repository Files

**Location**: `/Users/tmac/1_REPOS/AI_Orchestrator/`

**Files created** (tracked in git):

| File | Purpose |
|------|---------|
| `.desktop-pins.json` | Registry of Mission Control protection |
| `DESKTOP-PINNING.md` | Mission Control documentation |
| `CATALOG.md` | Master documentation index (with frontmatter) |
| `USER-PREFERENCES.md` | Working preferences (with Mission Control section) |
| `ROADMAP.md` | Future features roadmap |
| `.obsidian-defaults.md` | Documents Obsidian default app setup |
| `SYSTEM-CONFIGURATION.md` | This file |

**Persistence**: ✅ Tracked in git, synced across machines

---

## 🔄 What Happens on Reboot?

### ✅ PERSISTS (No action needed)

- Mission Control folder and all symlinks
- Default app setting (ObsidianOpener for .md files)
- ObsidianOpener.app application
- All scripts in `~/Library/Scripts/` and `~/bin/`
- duti tool (Homebrew installation)
- Obsidian vault symlinks
- Git repo files

### ⚠️  MAY NEED REFRESH (Rare)

**Launch Services cache**:
- If Finder doesn't recognize ObsidianOpener after reboot
- Fix: `killall Finder` or re-register app

**PATH for ~/bin**:
- If `obs` command not found in terminal
- Fix: Ensure `export PATH="$HOME/bin:$PATH"` in `~/.zshrc`

### ❌ DOES NOT PERSIST

- Running processes (Obsidian, terminal sessions)
- Environment variables set in current terminal
- Aliases typed in terminal (unless in `~/.zshrc`)

---

## 🆘 Troubleshooting

### .md Files Don't Open in Obsidian

**Check default app**:
```bash
duti -x md
```

**Reset to ObsidianOpener**:
```bash
duti -s com.tmac.obsidianopener .md all
```

**Reset to Obsidian directly**:
```bash
duti -s md.obsidian .md all
```

### ObsidianOpener App Not Found

**Check if app exists**:
```bash
ls -la ~/Applications/ObsidianOpener.app/
```

**Re-register with system**:
```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f ~/Applications/ObsidianOpener.app
killall Finder
```

### Mission Control Folder Missing

**Recreate folder and symlinks**:
```bash
mkdir -p ~/Desktop/Mission-Control

cd /Users/tmac/1_REPOS/AI_Orchestrator

# Create symlinks to vault versions (which symlink to repo)
ln -sf ~/Workspace/docs-hub/CATALOG.md ~/Desktop/Mission-Control/CATALOG.md
ln -sf ~/Workspace/docs-hub/STATE.md ~/Desktop/Mission-Control/STATE.md
ln -sf ~/Workspace/docs-hub/ROADMAP.md ~/Desktop/Mission-Control/ROADMAP.md
ln -sf ~/Workspace/docs-hub/USER-PREFERENCES.md ~/Desktop/Mission-Control/USER-PREFERENCES.md
ln -sf ~/Workspace/docs-hub/DECISIONS.md ~/Desktop/Mission-Control/DECISIONS.md
ln -sf ~/Workspace/docs-hub/latest-session.md ~/Desktop/Mission-Control/latest-session.md
```

### Terminal Commands Not Found (obs, obsidian-activate)

**Check if scripts exist**:
```bash
ls -la ~/bin/obs*
```

**Check if ~/bin is in PATH**:
```bash
echo $PATH | grep "$HOME/bin"
```

**Add to PATH** (if missing):
```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Obsidian Doesn't Activate When Clicking Files

This is expected behavior. Use workarounds:

1. **⌘Tab** after clicking (fastest)
2. Type `obs` in terminal
3. Type `obsidian-activate` in terminal

---

## 🔐 Backup & Restore

### Backup These Locations

```bash
# System configurations
~/Applications/ObsidianOpener.app/
~/Library/Scripts/*.sh
~/bin/obs*

# Mission Control
~/Desktop/Mission-Control/

# Vault symlinks
~/Workspace/docs-hub/*.md

# Git repo (already version controlled)
/Users/tmac/1_REPOS/AI_Orchestrator/
```

### Restore on New Machine

1. **Clone repo**:
   ```bash
   git clone <repo-url> /Users/tmac/1_REPOS/AI_Orchestrator
   ```

2. **Run restoration script** (TODO: create this):
   ```bash
   cd /Users/tmac/1_REPOS/AI_Orchestrator
   ./scripts/restore-system-config.sh
   ```

3. **Manual steps**:
   - Install Homebrew (if not installed)
   - Install duti: `brew install duti`
   - Recreate ObsidianOpener.app (see DESKTOP-PINNING.md)
   - Create Mission Control symlinks (see above)
   - Set default app: `duti -s com.tmac.obsidianopener .md all`

---

## 📊 Quick Reference

### Check Everything is Working

```bash
# Mission Control exists?
ls ~/Desktop/Mission-Control/

# Default app correct?
duti -x md

# Scripts exist?
ls ~/bin/obs*

# ObsidianOpener registered?
open -a ObsidianOpener /tmp/test.md
```

### Useful Commands

```bash
# List all .md files with custom default app
find ~ -name "*.md" -maxdepth 3 -exec duti -x {} \; 2>/dev/null | sort -u

# Reset Finder cache
killall Finder

# Rebuild Launch Services database
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f ~/Applications/ObsidianOpener.app

# Activate Obsidian
obs

# Open file in Obsidian with activation
obsidian-open ~/Desktop/Mission-Control/CATALOG.md
```

---

## 🔗 Related Documentation

- [CATALOG.md](./CATALOG.md) - Master documentation index
- [DESKTOP-PINNING.md](./DESKTOP-PINNING.md) - Mission Control system details
- [USER-PREFERENCES.md](./USER-PREFERENCES.md) - Working preferences (includes Mission Control section)
- [.desktop-pins.json](./.desktop-pins.json) - Protection registry

---

**Last Updated**: 2026-01-10
**System**: macOS (tested on Sequoia 15.2)
**Maintainer**: tmac
