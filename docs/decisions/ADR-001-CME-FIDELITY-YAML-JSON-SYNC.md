# ADR-001: CME Rule Fidelity - YAML to JSON Sync Patterns

**Date:** 2026-01-13
**Status:** Accepted
**Context:** CredentialMate CME Rules Engine
**Deciders:** tmac, Claude (Opus 4.5)

---

## Summary

Established patterns for maintaining fidelity between FSMB PDF source documents, YAML SSOT files, and JSON rule packs in the CME compliance system. This ADR documents the resolution of critical data accuracy issues discovered in the FL-M (Florida MD) rule pack.

---

## Context

The CME rules engine uses a three-tier data architecture:
1. **FSMB PDF** - Authoritative source (Federation of State Medical Boards)
2. **YAML SSOT** - `fsmb_ground_truth_2025_v2.yaml` (structured extraction)
3. **JSON Rule Packs** - `CME-{STATE}-2025.json` (runtime format)

**Problem Discovered:**
- FL-M JSON showed 40h total hours
- FSMB PDF states: "38 hours NOT including 2-hour medical errors"
- This means medical errors are a SEPARATE requirement, not part of the 38h base
- 61 tests were failing due to sync issues between YAML and JSON

**Impact:**
- Providers shown incorrect compliance requirements
- Legal liability for incorrect guidance
- Compliance calculations potentially wrong

---

## Decision

### 1. Total Hours with Separate Requirements

When FSMB specifies "X hours NOT including Y topic":
- Set `total_hours.value = X` (base requirement)
- Set `counts_toward_total: false` on topic Y rule
- Document clearly in notes

**Example (FL-M):**
```json
{
  "requirement": {
    "type": "total_hours",
    "value": 38,  // Base, NOT including medical errors
    "period_years": 2
  }
}

{
  "requirement": {
    "type": "topic_hours",
    "topic": "medical_errors_prevention",
    "value": 2,
    "period_years": 2
  },
  "counts_toward_total": false  // SEPARATE requirement
}
```

### 2. Rollover Schema Normalization

When FSMB doesn't specify rollover policy:
- YAML: `rollover.allowed: null` (unspecified)
- JSON: `allows_rollover: false` (default)
- **These are semantically equivalent** - conservative interpretation

**Test Logic:**
```python
yaml_normalized = yaml_rollover if yaml_rollover is not None else False
json_normalized = json_rollover if json_rollover is not None else False
assert yaml_normalized == json_normalized
```

### 3. No-CME States Handling

For states with no substantial CME requirement (IN, MT, NY, SD):
- `total_hours.value = 0`
- `total_hours.period_years = 1` (placeholder)
- `renewal_cycle.period_years = 2` (actual license cycle)

**These are different concepts - don't compare them for no-CME states.**

### 4. Category Requirements Explicit Encoding

States requiring 100% Category 1 must have:
```json
"category_requirements": {
  "accepted_categories": ["AMA_Category_1"],
  "minimums": {"ama_category_1_minimum": <total_hours>},
  "exclusive": true
}
```

---

## Consequences

### Positive
- FL-M now shows correct 38h base + 2h separate
- 865 sync tests pass (was 804/865)
- Clear patterns for future state additions
- Reduced legal liability risk

### Negative
- Requires manual review for "NOT including" patterns in other states
- Test complexity increased for edge cases

### Neutral
- No performance impact
- No API changes required

---

## Implementation

**Commit:** `80ca75e9`
**Branch:** CME-Update
**Files Changed:**
1. `CME-FL-M-2025.json` - Total hours 40→38, counts_toward_total added
2. `CME-NC-2025.json` - Category requirements fixed
3. `fsmb_ground_truth_2025_v2.yaml` - FL-M topics added
4. `test_yaml_to_json_sync.py` - Normalization logic added

---

## Verification

```bash
cd /Users/tmac/1_REPOS/credentialmate
python -m pytest apps/rules-engine/rules_engine/tests/accuracy/test_yaml_to_json_sync.py -v
# Result: 865 passed, 0 failed
```

---

## Related Documents

### CredentialMate
- `sessions/SESSION-20260113-CME-FIDELITY-FIX.md`
- `docs/20-ris/resolutions/RIS-008-cme-fidelity-fl-m-total-hours.md`
- `docs/03-kb/references/KB-011-CME-YAML-JSON-SYNC-FIDELITY.md`
- `AI-Team-Plans/decisions/ADR-008-cme-response-schema-counts-toward-total.md`
- `AI-Team-Plans/decisions/ADR-009-populate-gap-metadata-in-service-responses.md`

### AI Orchestrator
- This ADR serves as cross-project learning for multi-source data sync patterns

---

## Applicability to AI Orchestrator

This pattern applies to any system with:
1. Authoritative source documents (PDF, regulations)
2. Structured intermediate format (YAML SSOT)
3. Runtime format (JSON rule packs)
4. Calculated outputs (compliance status)

**Key Learning:** When source says "X NOT including Y", the Y component needs explicit tracking (`counts_toward_total: false`) rather than implicit inclusion in X.

---

## Tags

`cme`, `data-sync`, `yaml`, `json`, `fsmb`, `compliance`, `credentialmate`, `rules-engine`
