# ADR Index

**Last Updated**: {{TIMESTAMP}}
**Total ADRs**: {{TOTAL_COUNT}}
**Auto-Updated By**: Coordinator

---

## Summary

| Status | Count |
|--------|-------|
| Approved | {{APPROVED_COUNT}} |
| Draft | {{DRAFT_COUNT}} |
| Superseded | {{SUPERSEDED_COUNT}} |

---

## All ADRs

| # | Title | Status | Advisor | Date |
|---|-------|--------|---------|------|
{{ADR_LIST}}

---

## By Tag

| Tag | ADRs |
|-----|------|
{{TAG_INDEX}}

---

## By Domain

| Domain | ADRs |
|--------|------|
{{DOMAIN_INDEX}}

---

## By File Path

| Pattern | ADRs |
|---------|------|
{{PATH_INDEX}}

---

## Recently Updated

| ADR | Title | Updated | Change |
|-----|-------|---------|--------|
{{RECENT_UPDATES}}

---

<!--
SYSTEM SECTION - DO NOT EDIT
Used for fast lookups by Advisors
-->

```yaml
_system:
  version: "3.0"
  last_rebuild: "{{REBUILD_TIMESTAMP}}"
  tag_cache:
    {{TAG_CACHE_YAML}}
  domain_cache:
    {{DOMAIN_CACHE_YAML}}
  path_cache:
    {{PATH_CACHE_YAML}}
```
