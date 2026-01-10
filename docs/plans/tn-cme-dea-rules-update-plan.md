# Tennessee CME/DEA Rules Update Plan

**Date**: 2026-01-08
**Source**: `/Users/tmac/Downloads/tn_cme_dea_rules.json`
**Target Files**:
- `/Users/tmac/credentialmate/apps/rules-engine/rules_engine/src/rule_packs/CME-TN-M-2025.json`
- `/Users/tmac/credentialmate/apps/rules-engine/rules_engine/src/rule_packs/CME-TN-O-2025.json`
- Schema: `/Users/tmac/credentialmate/apps/rules-engine/rules_engine/schemas/rule_pack.schema.json`

---

## Executive Summary

The new rules JSON contains **7 significant gaps** compared to the existing CredentialMate implementation, plus several enhancements. Most critical is the **missing DEA MATE Act requirement** (federal law) and **missing specialty exemptions**.

---

## Detailed Diff Analysis

### 1. CRITICAL: Rollover Policy Conflict

| Aspect | New JSON | Existing | Verdict |
|--------|----------|----------|---------|
| Rollover | Not mentioned; implies no rollover | `allows_rollover: true` | **VERIFY** |

**New JSON says**: "24 months immediately preceding state license renewal date" (sliding window, no rollover implied)

**Action**: Verify with TN Board regulations. If no rollover, update to `allows_rollover: false`.

---

### 2. CRITICAL: Missing DEA MATE Act Requirement

| Aspect | New JSON | Existing |
|--------|----------|----------|
| DEA MATE Rule | `DEA-MATE-8H-ONCE` - 8 hours one-time | **COMPLETELY MISSING** |

**Details from new JSON**:
```json
{
  "id": "DEA-MATE-8H-ONCE",
  "hours_required": 8,
  "frequency": "ONCE_PER_LIFETIME",
  "trigger": "Before first DEA registration renewal after June 27, 2023",
  "applies_to": ["MD", "DO", "NP", "PA", "Other_DEA_Registered_Prescribers"]
}
```

**Impact**: Federal law compliance gap. All DEA registrants must complete this.

**Action**: Add new rule to both TN-M and TN-O packs (and potentially a separate federal rules pack).

---

### 3. CRITICAL: Missing Specialty Exemptions

| Aspect | New JSON | Existing |
|--------|----------|----------|
| Controlled substance CME exemption | Board-certified specialists exempt | No exemptions |

**Exempt specialties** (from 2-hour controlled substance CME):
- Pain_Management
- Anesthesiology
- Physical_Medicine_and_Rehabilitation
- Neurology
- Rheumatology

**Current implementation**: Uses `requires_dea_registration: true` but no exemption logic.

**Action**:
1. Extend schema to support `exemptions` array
2. Add `specialties_excluded` to controlled substance rules

---

### 4. MEDIUM: Credit Category Expansion

| Aspect | New JSON (MD) | Existing (MD) |
|--------|---------------|---------------|
| Accepted credits | AMA_PRA_Category_1, AAFP_Prescribed, AOA_Prescribed | AMA_Category_1 only |

**Impact**: Current system may reject valid AAFP/AOA credits for MD physicians.

**Action**: Update `fsmb_board_metadata.category_requirements.accepted_categories` in TN-M rule pack.

---

### 5. MEDIUM: Content Tag Requirements

| Aspect | New JSON | Existing |
|--------|----------|----------|
| Controlled substance CME tags | `TN_SPECIFIC`, `CONTROLLED_SUBSTANCE_PRESCRIBING`, `TN_DOH_OPIOID_GUIDELINES` | Just topic name |

**Impact**: Current system doesn't validate that CME is TN-specific.

**Action**:
1. Extend schema to support `required_content_tags`
2. Update compliance service to check tags

---

### 6. LOW: Residency/Fellowship Credit

| Aspect | New JSON | Existing |
|--------|----------|----------|
| ACGME training credit | 20 hours/year max, up to 40 hours | Not supported |

**Details**:
```json
{
  "id": "TN-RES-20-PER-YEAR",
  "max_hours_per_year": 20,
  "note": "Does not satisfy the TN-specific 2-hour controlled substance requirement"
}
```

**Action**: Add as special situation handling in compliance service.

---

### 7. LOW: Reinstatement Requirements

| Aspect | New JSON | Existing |
|--------|----------|----------|
| Reinstatement from expired | 20 hrs/12 mo, max 80 hrs | Not tracked |
| Reinstatement from retired/inactive | 20 hrs/12 mo, max 40 hrs | Not tracked |

**Action**: Add reinstatement rules to schema and rule packs (separate requirement type).

---

### 8. LOW: Penalty Tracking

| Aspect | New JSON | Existing |
|--------|----------|----------|
| Penalties | $100/hr shortfall, makeup + 10 extra, public discipline | Not tracked |

**Action**: Out of scope for MVP; consider for future compliance dashboard.

---

## Schema Changes Required

### 1. Add `exemptions` to rule pack schema

```json
"exemptions": {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "exemption_id": { "type": "string" },
      "applies_to_rule_id": { "type": "string" },
      "condition": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },
          "in_any": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

### 2. Add `required_content_tags` to Requirement

```json
"required_content_tags": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Content tags that must be present on CME activity"
}
```

### 3. Add `special_situations` to rule pack

```json
"special_situations": {
  "type": "object",
  "properties": {
    "residency_fellowship_credit": { "$ref": "#/definitions/ResidencyCredit" },
    "reinstatement_requirements": { "$ref": "#/definitions/ReinstatementRules" }
  }
}
```

### 4. Add one-time requirement support

Already exists in schema (`period_years: 0` = one-time), but verify compliance service handles it.

---

## Implementation Plan

### Phase 1: Critical Fixes (Priority P0)

1. **Add DEA MATE Act rule** to both TN rule packs
   - Files: `CME-TN-M-2025.json`, `CME-TN-O-2025.json`
   - Add new rule with `requirement.type: "one_time"`

2. **Add specialty exemptions** for controlled substance CME
   - Update `applicability.specialties_excluded` in existing rules
   - Or add new `exemptions` array

3. **Verify and fix rollover policy**
   - Research TN Board regulations
   - Update `allows_rollover` if incorrect

### Phase 2: Data Quality (Priority P1)

4. **Expand credit categories** for MD
   - Add AAFP_Prescribed, AOA_Prescribed to accepted categories

5. **Update citations** with exact regulation references
   - Tenn. Comp. R. & Regs. 0880-02-.19 (MD controlled substance)
   - Tenn. Comp. R. & Regs. 1050-02-.12 (DO controlled substance)

### Phase 3: Schema Extensions (Priority P2)

6. **Extend schema** for content tags
   - Add `required_content_tags` to Requirement definition

7. **Add exemption support** to schema
   - Add `exemptions` array at rule pack level

### Phase 4: Enhanced Features (Priority P3)

8. **Residency/fellowship credit handling**
   - Add special situation rules
   - Update compliance service

9. **Reinstatement requirements**
   - Add reinstatement rule type
   - Track license status transitions

---

## Updated Rule Pack Structure (TN-M Example)

```json
{
  "rule_pack_id": "CME-TN-M-2026",
  "version": "2.0.0",
  "effective_date": "2026-01-01",
  "renewal_cycle": {
    "period_years": 2,
    "allows_rollover": false,  // VERIFY
    "window_definition": "24 months immediately preceding renewal"
  },
  "rules": [
    {
      "rule_id": "TN-M-CME-TOTAL-HOURS",
      "requirement": {
        "type": "total_hours",
        "value": 40,
        "period_years": 2
      },
      "category_requirement": {
        "accepted_categories": ["AMA_PRA_Category_1", "AAFP_Prescribed", "AOA_Prescribed"]
      }
    },
    {
      "rule_id": "TN-M-CME-CONTROLLED-SUBSTANCE",
      "requirement": {
        "type": "topic_hours",
        "topic": "controlled_substance_prescribing",
        "value": 2,
        "period_years": 2,
        "required_content_tags": ["TN_SPECIFIC", "TN_DOH_OPIOID_GUIDELINES"]
      },
      "applicability": {
        "requires_dea_registration": true,
        "specialties_excluded": [
          "Pain_Management", "Anesthesiology",
          "Physical_Medicine_and_Rehabilitation",
          "Neurology", "Rheumatology"
        ]
      },
      "citation": "Tenn. Comp. R. & Regs. 0880-02-.19"
    },
    {
      "rule_id": "DEA-MATE-8H-ONCE",
      "description": "DEA MATE Act 8-hour one-time training requirement",
      "requirement": {
        "type": "one_time",
        "value": 8,
        "period_years": 0
      },
      "applicability": {
        "requires_dea_registration": true
      },
      "effective_date": "2023-06-27",
      "citation": "21 U.S.C. 823(g)(2)(G)(ii)",
      "notes": "Federal requirement. Must complete before first DEA renewal after June 27, 2023."
    }
  ],
  "exemptions": [
    {
      "exemption_id": "TN-EXEMPT-CONTROLLED-BOARD-CERT",
      "applies_to_rule_id": "TN-M-CME-CONTROLLED-SUBSTANCE",
      "condition": {
        "field": "specialty_board_certifications",
        "in_any": ["Pain_Management", "Anesthesiology", "Physical_Medicine_and_Rehabilitation", "Neurology", "Rheumatology"]
      }
    }
  ],
  "special_situations": {
    "residency_fellowship": {
      "id": "TN-RES-20-PER-YEAR",
      "max_hours_per_year": 20,
      "max_total_hours": 40,
      "condition": "is_in_acgme_training",
      "note": "Does not satisfy controlled substance requirement"
    }
  }
}
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `CME-TN-M-2025.json` | Add DEA MATE rule, update exemptions, expand credits |
| `CME-TN-O-2025.json` | Add DEA MATE rule, update exemptions |
| `rule_pack.schema.json` | Add exemptions, content_tags, special_situations |
| `cme_compliance_service.py` | Handle one-time requirements, exemptions, content tags |
| `rule_loader.py` | Load and validate new schema fields |

---

## Verification Checklist

- [ ] Confirm TN rollover policy with official source
- [ ] Validate DEA MATE Act effective date and trigger
- [ ] Verify exempt specialty list is complete
- [ ] Test compliance calculations with new rules
- [ ] Update API documentation for new fields
- [ ] Add migration for existing provider data

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incorrect rollover policy | False compliance status | Verify with TN Board before deploy |
| DEA MATE rule missing | Federal compliance gap | P0 priority fix |
| Specialty exemptions missing | Over-requiring CME | Add exemption logic |
| Credit category too narrow | Rejecting valid CME | Expand accepted categories |

---

## Next Steps

1. **Human review** of this plan
2. **Verify rollover policy** with authoritative TN source
3. **Implement Phase 1** (P0 critical fixes)
4. **Test** with sample provider data
5. **Deploy** to staging for validation
