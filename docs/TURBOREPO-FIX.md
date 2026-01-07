# Turborepo Support for Bug Discovery System

**Date**: 2026-01-06
**Version**: v5.2.1
**Status**: ✅ Production Ready

## Problem Statement

The bug discovery system (`aibrain discover-bugs`) hung indefinitely when scanning Turborepo monorepo projects like KareMatch. The scan never completed, making the system unusable for monorepos.

## Root Cause Analysis

### Issue 1: Nested Argument Passing

**Problem**: Turborepo requires special argument handling for nested commands.

```bash
# What the scanner tried (FAILS):
npm run lint -- --format=json

# What actually happens:
npm → calls → turbo run lint --format=json
                    ↑
                    Turbo interprets --format=json as ITS OWN flag

# Error:
ERROR  unexpected argument '--format' found
  tip: to pass '--format' as a value, use '-- --format'
```

**Why it fails**:
- `npm run lint` executes `turbo run lint` (from package.json)
- The first `--` passes args from npm → turbo
- Turbo then needs ANOTHER `--` to pass args to ESLint
- Correct syntax would be: `npm run lint -- -- --format=json` (confusing!)

### Issue 2: Vitest Verbose Output

**Problem**: Vitest with `--reporter=json` generates massive log output (hundreds of JSON log lines per test).

```json
{"level":30,"time":1767728050580,"workflow_name":"findMatchingTherapists",...}
{"level":30,"time":1767728050581,"workflow_name":"findMatchingTherapists",...}
// ... hundreds more log lines ...
[{"filePath":"test.ts","messages":[...]}]  // Actual JSON at the end
```

This made parsing difficult and output files enormous.

## Solution

### 1. Automatic Turborepo Detection

```python
# discovery/scanner.py (lines 89-92)
self.uses_turborepo = (project_path / "turbo.json").exists()
if self.uses_turborepo:
    print("📦 Turborepo detected - using direct tool invocation")
```

**Benefits**:
- No configuration needed
- Works automatically for all Turborepo projects
- Falls back to npm scripts for standard projects

### 2. Direct Tool Invocation

```python
# discovery/scanner.py (lines 179-206)
if self.uses_turborepo:
    # Turborepo projects: bypass npm scripts, call tools directly
    commands = {
        'lint': ['npx', 'eslint', '.', '--format=json'],
        'typecheck': ['npx', 'tsc', '--noEmit'],
        'test': ['npx', 'vitest', 'run', '--reporter=json', '--outputFile=.vitest-results.json'],
        'guardrails': ['rg', '@ts-ignore|...', '--json', '--type', 'typescript'],
    }
else:
    # Standard npm projects: use npm scripts
    commands = {
        'lint': ['npm', 'run', 'lint', '--', '--format=json'],
        'typecheck': ['npm', 'run', 'check'],
        'test': ['npm', 'test', '--', '--reporter=json'],
        'guardrails': ['rg', ...],
    }
```

**Why this works**:
- `npx eslint .` calls ESLint directly (no Turbo involved)
- `npx tsc --noEmit` calls TypeScript directly
- `npx vitest run` calls Vitest directly
- Arguments pass through correctly

### 3. Vitest Output File

```python
# discovery/scanner.py (lines 223-243)
if source == 'test' and self.uses_turborepo and self.language == 'typescript':
    # Read from the output file instead of stdout
    output_file = self.project_path / '.vitest-results.json'
    if output_file.exists():
        output = output_file.read_text()
        # Clean up the temporary file
        output_file.unlink()
    else:
        # Fallback to stdout/stderr if file wasn't created
        output = result.stdout + result.stderr
```

**Benefits**:
- Clean JSON (no interleaved log messages)
- Faster parsing (no need to filter logs)
- File automatically cleaned up after reading

### 4. Enhanced JSON Extraction

```python
# discovery/parsers/eslint.py (lines 83-95)
try:
    json_start = json_output.index('[')
    json_output = json_output[json_start:]

    decoder = json.JSONDecoder()
    data, end_idx = decoder.raw_decode(json_output)
except (ValueError, json.JSONDecodeError) as e:
    print(f"⚠️  Failed to parse ESLint JSON: {e}")
    return []
```

**Benefits**:
- Filters out non-JSON warnings/logs before the array
- Uses `raw_decode()` to stop at first complete JSON object
- Handles mixed output gracefully

## Performance Results

### Before Fix

```
aibrain discover-bugs --project karematch
# ... hangs indefinitely, never completes ...
# User has to Ctrl+C to kill
```

### After Fix

```
aibrain discover-bugs --project karematch

📦 Turborepo detected - using direct tool invocation
🔍 Scanning lint... Found 3256 issues
🔍 Scanning typecheck... Found 39 issues
🔍 Scanning test... Found 126 issues
🔍 Scanning guardrails... Found 0 issues

✅ Scan completed in 27.2s
Total errors found: 3421
✅ Generated 389 tasks (P0: 0, P1: 3, P2: 386)
```

### Metrics

| Metric | Before Fix | After Fix | Improvement |
|--------|-----------|-----------|-------------|
| **Scan completion** | Hung (never finished) | ✅ 27 seconds | **From ∞ to 27s** |
| **Lint errors** | 0 (command failed) | ✅ 3,256 | **Working** |
| **Type errors** | 0 (command failed) | ✅ 39 | **Working** |
| **Test failures** | 0 (command failed) | ✅ 126 | **Working** |
| **Tasks generated** | 0 | ✅ 389 | **Working** |

## Implementation Details

### Files Modified

1. **discovery/scanner.py** (~50 lines changed)
   - Lines 89-92: Turborepo detection
   - Lines 179-206: Conditional command selection
   - Lines 223-243: Vitest output file handling

2. **discovery/parsers/eslint.py** (~15 lines changed)
   - Lines 83-95: Enhanced JSON extraction

### Backward Compatibility

✅ **Fully backward compatible** with standard npm projects:
- Detection is automatic (checks for `turbo.json`)
- Falls back to npm scripts if not a Turborepo project
- No configuration changes required
- Works with both monorepos and single-package projects

### Testing

**Tested with**:
- ✅ KareMatch (Turborepo monorepo, 24 workspaces)
- ✅ Standard npm project (via else branch)
- ✅ All 4 scanners (lint, typecheck, test, guardrails)
- ✅ Full end-to-end flow (scan → baseline → task generation)

## Alternative Solutions Considered

### Option B: Double `--` for Turbo
```bash
npm run lint -- -- --format=json
```

**Rejected because**:
- Confusing syntax (triple arguments)
- Still slow (runs through Turbo overhead)
- Complex output parsing (multiple package results)

### Option C: Workspace-Specific Scanning
```python
for workspace in workspaces:
    run_eslint(workspace)
```

**Rejected because**:
- More complex implementation
- Slower (no Turbo caching benefits)
- Requires workspace discovery logic

## Recommended Usage

### Standard Workflow

```bash
# First run: Create baseline
aibrain discover-bugs --project karematch

# Subsequent runs: Detect new bugs
aibrain discover-bugs --project karematch

# Dry run (preview tasks)
aibrain discover-bugs --project karematch --dry-run

# Specific sources only
aibrain discover-bugs --project karematch --sources lint,typecheck
```

### For Other Projects

The fix works automatically for any project structure:
- **Turborepo monorepos**: Uses direct tool invocation
- **Standard npm projects**: Uses npm scripts
- **No configuration needed**: Detection is automatic

## Troubleshooting

### If scan still hangs

1. **Check for `turbo.json`**: System should print "📦 Turborepo detected"
2. **Check tool availability**: Ensure `npx eslint`, `npx tsc`, `npx vitest` are available
3. **Check timeout**: Default is 10 minutes (600s), increase if needed in `scanner.py` line 220

### If JSON parsing fails

1. **Check ESLint output**: Run `npx eslint . --format=json` manually
2. **Look for warnings**: Some warnings may appear before JSON array
3. **Enhanced parser handles**: Non-JSON prefix automatically filtered

## Future Improvements

### Potential Enhancements

1. **Workspace-aware scanning** (if needed at scale)
   - Scan each workspace individually
   - Parallelize across workspaces
   - Requires: Workspace discovery + coordination logic

2. **Turbo cache integration** (if caching is valuable)
   - Use Turbo's cache for faster re-scans
   - Requires: Understanding when cache is valid

3. **Progress indicators** (nice-to-have)
   - Show progress during long scans
   - Requires: Streaming output parsing

## References

- [CLAUDE.md](../CLAUDE.md#automated-bug-discovery-system-v52) - Updated documentation
- [STATE.md](../STATE.md#automated-bug-discovery-system-v52---2026-01-06) - Implementation status
- [discovery/scanner.py](../discovery/scanner.py) - Implementation code
- [discovery/parsers/eslint.py](../discovery/parsers/eslint.py) - Enhanced JSON parser

## Conclusion

The Turborepo fix enables bug discovery to work seamlessly with monorepo projects:
- ✅ **Automatic detection** - No configuration needed
- ✅ **Fast scans** - 27s for full scan (vs hung indefinitely)
- ✅ **Backward compatible** - Works with standard npm projects
- ✅ **Production ready** - Tested with real monorepo (KareMatch)

The system now works for **both monorepos and standard projects**, making it universally applicable.
