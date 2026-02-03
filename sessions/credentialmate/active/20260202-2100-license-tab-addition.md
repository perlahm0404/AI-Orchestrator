# Session: Manual License Tab Addition to Google Sheets .INFO Files

**Date**: 2026-02-02
**Time Started**: 21:00
**Status**: In Progress - Phase 1
**Approach**: Option B - Work on copies first, replace originals after verification

---

## Provider Inventory

### Total Providers Across All Tabs: 85

| Tab Name | Provider Count | Credential Types |
|----------|----------------|------------------|
| Visana | 19 | NP (majority), MD, CNM |
| LabFinder | 11 | MD, NP, DO, PA |
| Trovo | 1 | NP |
| MedSpire | 1 | MD |
| StratusNeuro | 1 | MD |
| Innerwell | 1 | MD |
| Individuals | 51 | MD (majority), NP, DO, PA |
| **TOTAL** | **85** | Mixed |

---

## Phase 1: Create Example Copies

**Goal**: Create 2 working copies (one MD, one NP) with License tabs for user review

### Selected Examples

1. **MD Example**: Kristin Baier, MD
   - Tab: Individuals (row 5)
   - Folder: To be located
   - .INFO File: To be located
   - Notes: PARTIAL ONLY flag in Renewals List

2. **NP Example**: William Campbell, NP
   - Tab: Individuals (row 7)
   - Folder: To be located
   - .INFO File: To be located
   - Notes: "Renew Maryland; Virginia only" flag in Renewals List

---

## Safety Protocol Status

✅ **Step 0**: Backup requirement assessed
- Google Sheets are cloud-based with built-in version history
- Using "Make a Copy" approach (Option B) instead
- Original files will remain untouched until verification complete

✅ **Step 0.5**: Target providers identified
- Renewals List accessed: `1MpNNT731MCbIGtM53ayRMexXKwstaQLPfIsfcNz1GMw`
- 85 providers identified across 7 tabs
- Examples selected for Phase 1

---

## Next Steps

1. ✅ Locate Kristin Baier, MD .INFO file in Customers folder
2. ✅ Locate William Campbell, NP .INFO file in Customers folder
3. ⏳ Create working copy of Baier .INFO file
4. ⏳ Add License tab to Baier copy
5. ⏳ Create working copy of Campbell .INFO file
6. ⏳ Add License tab to Campbell copy
7. ⏳ Present both examples to user for approval
8. ⏳ WAIT for approval before proceeding to Phase 2

---

## Working Copies Tracking

| Provider | Original Doc ID | Working Copy Doc ID | Status |
|----------|----------------|---------------------|---------|
| Kristin Baier, MD | TBD | TBD | Not started |
| William Campbell, NP | TBD | TBD | Not started |

---

## License Tab Structure

### Column Headers (Row 1)
| Column | Header | Format |
|--------|--------|--------|
| A | State | Text |
| B | Number | Text |
| C | Issue Date | Date (YYYY-MM-DD) |
| D | Expiry Date | Date (YYYY-MM-DD) |
| E | Username | Text |
| F | Password | Text |
| G | PIN or ID # | Text |
| H | Notes | Text |

### Formatting Rules
- Row 1: Bold headers with light blue background (#CFE2F3)
- Freeze first row
- Date columns (C, D): Format as date (YYYY-MM-DD)
- All columns: Auto-resize to fit content
- Tab name: "License" (case-sensitive)
- Tab position: Second tab (after main INFO tab)

---

## Notes

- All work performed manually via browser automation
- No scripts or batch processing
- Each file reviewed individually
- Google Sheets version history provides rollback capability
- Working copies allow safe testing before replacing originals
