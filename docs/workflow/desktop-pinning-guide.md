# Mission Control - Desktop Command Center 🚀

**Quick Reference for AI Orchestrator's protected documentation hub**

---

## What is Mission Control?

**Location**: `~/Desktop/Mission-Control/`

**Purpose**: Single folder containing symlinks to all critical AI Orchestrator documentation. Protected from cleanup, archiving, and reorganization.

**Why Mission Control?** (NASA-inspired naming)
- Central command center for all operations
- Always accessible, never cluttered
- One folder to protect instead of individual files
- Clean desktop, organized access

---

## Current Contents

| File | Priority | Purpose |
|------|----------|---------|
| **CATALOG.md** | 🔴 1 | Master documentation index - start here |
| **STATE.md** | 🔴 1 | Current implementation status |
| **ROADMAP.md** | 🟡 2 | Future features roadmap |
| **USER-PREFERENCES.md** | 🟡 2 | tmac's working preferences |
| **DECISIONS.md** | 🟡 2 | Build decisions with rationale |
| **latest-session.md** | 🟢 3 | Most recent session handoff |
| **README.md** | 📘 Info | Folder documentation |

---

## Priority Levels

| Level | Icon | Meaning | Cleanup Policy |
|-------|------|---------|----------------|
| **1** | 🔴 | Critical | NEVER remove, archive, or move |
| **2** | 🟡 | High | Require explicit approval to modify |
| **3** | 🟢 | Reference | Can update, but keep in folder |

---

## AI Agent Instructions

**⚠️ CRITICAL PROTECTION RULES ⚠️**

Before ANY cleanup, archive, or reorganization operation:

1. **Check path**: Does it contain `~/Desktop/Mission-Control/`?
   - **If YES**: STOP. Do NOT proceed.
   - **If NO**: Proceed with normal checks.

2. **Check `.desktop-pins.json`**: Is folder/file listed?
   - **If YES**: STOP. Do NOT proceed.
   - **If NO**: Proceed with normal checks.

3. **Check YAML frontmatter**: Does file have `protect-from-cleanup: true`?
   - **If YES**: STOP. Do NOT proceed.
   - **If NO**: Safe to cleanup.

**Absolute Rules**:
- NEVER delete `~/Desktop/Mission-Control/`
- NEVER move `~/Desktop/Mission-Control/`
- NEVER archive `~/Desktop/Mission-Control/`
- NEVER remove files from Mission-Control folder
- NEVER rename Mission-Control folder

**Only tmac can override these rules.**

---

## How It Works

### 1. Protected Folder

Mission-Control is tracked in `.desktop-pins.json`:

```json
{
  "mission_control": {
    "folder": "~/Desktop/Mission-Control",
    "priority": 1,
    "protect_from_cleanup": true,
    "reason": "Central command center for AI Orchestrator"
  }
}
```

### 2. Symlinks (Not Copies)

All files in Mission-Control are symlinks to the source repo:

```
Mission-Control/CATALOG.md  →  AI_Orchestrator/CATALOG.md
                               ↓
                            (same file)
```

**Benefit**: Edit in Mission-Control OR repo, changes sync automatically.

### 3. YAML Frontmatter

Critical files also have frontmatter protection:

```yaml
---
pin-to-desktop: true
protect-from-cleanup: true
desktop-priority: 1
tags: [catalog, index, pinned]
---
```

---

## Adding Files to Mission Control

### Quick Add

```bash
cd /Users/tmac/1_REPOS/AI_Orchestrator
ln -sf "$(pwd)/NEW_FILE.md" ~/Desktop/Mission-Control/NEW_FILE.md
```

### Full Process

1. **Create symlink**:
   ```bash
   cd /Users/tmac/1_REPOS/AI_Orchestrator
   ln -sf "$(pwd)/NEW_FILE.md" ~/Desktop/Mission-Control/NEW_FILE.md
   ```

2. **Update `.desktop-pins.json`**:
   ```json
   {
     "name": "NEW_FILE.md",
     "source": "/Users/tmac/1_REPOS/AI_Orchestrator/NEW_FILE.md",
     "priority": 2,
     "purpose": "Description of why this file is in Mission Control"
   }
   ```

3. **Optional - Add frontmatter** to source file:
   ```yaml
   ---
   pin-to-desktop: true
   protect-from-cleanup: true
   desktop-priority: 2
   ---
   ```

4. **Verify**:
   ```bash
   ls -la ~/Desktop/Mission-Control/NEW_FILE.md
   ```

---

## Quick Commands

### View Mission Control Contents

```bash
ls -la ~/Desktop/Mission-Control/
```

### Check Broken Symlinks

```bash
find ~/Desktop/Mission-Control/ -type l ! -exec test -e {} \; -print
```

### View Protection Registry

```bash
cat .desktop-pins.json | jq '.mission_control'
```

### Verify File Source

```bash
readlink ~/Desktop/Mission-Control/CATALOG.md
```

---

## Obsidian Integration

Mission-Control is separate from Obsidian vault integration:

| Integration | Path | Purpose |
|-------------|------|---------|
| **Mission-Control** | `~/Desktop/Mission-Control/` | macOS desktop access |
| **Obsidian** | `~/Workspace/docs-hub/CATALOG.md` | Vault integration |

Both point to same source files in AI_Orchestrator repo.

---

## Troubleshooting

### Broken Symlink

```bash
# Remove broken link
rm ~/Desktop/Mission-Control/broken-file.md

# Recreate
cd /Users/tmac/1_REPOS/AI_Orchestrator
ln -sf "$(pwd)/FILE.md" ~/Desktop/Mission-Control/FILE.md
```

### Mission-Control Folder Deleted

```bash
# Recreate entire folder
cd /Users/tmac/1_REPOS/AI_Orchestrator
mkdir -p ~/Desktop/Mission-Control

# Recreate all symlinks
ln -sf "$(pwd)/CATALOG.md" ~/Desktop/Mission-Control/CATALOG.md
ln -sf "$(pwd)/STATE.md" ~/Desktop/Mission-Control/STATE.md
ln -sf "$(pwd)/ROADMAP.md" ~/Desktop/Mission-Control/ROADMAP.md
ln -sf "$(pwd)/USER-PREFERENCES.md" ~/Desktop/Mission-Control/USER-PREFERENCES.md
ln -sf "$(pwd)/DECISIONS.md" ~/Desktop/Mission-Control/DECISIONS.md
ln -sf "$(pwd)/sessions/latest.md" ~/Desktop/Mission-Control/latest-session.md
```

---

## Related Files

- `.desktop-pins.json` - Protection registry
- `USER-PREFERENCES.md` - Documents Mission Control system
- `~/Desktop/Mission-Control/README.md` - Folder documentation

---

## Why This System?

**Problem**: Critical navigation files scattered across desktop, at risk during cleanup.

**Solution**: Mission Control - single protected folder with:
1. **Folder-level protection** - One rule protects all files
2. **Symlinks** - No duplicates, always in sync
3. **Clear naming** - "Mission Control" signals importance
4. **Registry tracking** - `.desktop-pins.json` for automation

**Result**: Clean desktop, protected files, AI agent compliance.

---

**Last Updated**: 2026-01-10
**Version**: 2.0 (Mission Control)
