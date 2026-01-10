# NextEra Provider Import Plan

## Status: COMPLETED

**Executed**: 2026-01-08
**Result**: SUCCESS

## Overview

**Source**: 378 Excel files in `/Users/tmac/BlueShift_Provider_List/LEADS/INFO_Files_Organized/`
**Target**: CredentialMate PostgreSQL database
**Organization**: NextEra (ID: 4)

## Final Import Results

| Metric | Count |
|--------|-------|
| **Providers imported** | 368 |
| **Licenses imported** | 2,747 |
| **With real NPI** | 224 |
| **With temp NPI (TEMP*)** | 144 |
| **Skipped (duplicates)** | 3 |
| **Errors** | 2 |
| **Templates skipped** | 5 |

### Top States by License Count

| State | Licenses |
|-------|----------|
| CA | 171 |
| FL | 147 |
| NY | 145 |
| TX | 134 |
| WA | 105 |
| MD | 103 |
| IL | 95 |
| NJ | 95 |
| PA | 94 |
| OH | 86 |

---

---

## Source Data Summary

| Metric | Value |
|--------|-------|
| Total Files | 378 |
| Complete Records | 287 (75.9%) |
| Missing Contact Info | 91 (24.1%) |
| Format | Excel (.xlsx), vertical key-value |

### Data Fields Available

**Core Provider Info**:
- Full Legal Name (first, last, credentials)
- NPI (10-digit)
- Email, Phone, Address
- Specialty
- SSN (XXX-XX-XXXX)
- Date of Birth (YYYY-MM-DD)

**Credentials**:
- State Medical Licenses (state, number, issue/expiration dates)
- Board Certifications
- DEA numbers (if present)

**Additional Data** (not mapped to current schema):
- Education history
- Employment history
- FCVS credentials
- Credit card info (DO NOT IMPORT)
- Portal passwords (DO NOT IMPORT)

---

## Target Schema Mapping

### Organizations Table

```sql
INSERT INTO organizations (name, slug, status, subscription_tier, max_providers)
VALUES ('NextEra', 'nextera', 'active', 'enterprise', 500);
```

### Providers Table

| Excel Field | Database Column | Notes |
|-------------|-----------------|-------|
| Full Legal Name | `first_name`, `last_name` | Parse name, strip credentials |
| Name suffix (MD, DO, etc.) | `suffix` | Extract from name |
| NPI number | `npi` | Required, unique |
| Real email address | `email` | Optional |
| Phone number | `phone` | Optional |
| Specialty | `specialty` | Optional |
| Full SSN | `ssn` | Encrypted, sensitive |
| Date of birth | `date_of_birth` | Encrypted, sensitive |

### Licenses Table

| Excel Field | Database Column | Notes |
|-------------|-----------------|-------|
| State | `state` | 2-letter code |
| License number | `license_number` | Indexed |
| Issue date | `issue_date` | Optional |
| Expiration date | `expiration_date` | Required |
| License type | `license_type` | MD, DO, NP, PA, etc. |
| - | `status` | Default: 'active' |
| - | `data_source` | Set to 'bulk_import' |

### DEA Registrations (if present in Excel)

| Excel Field | Database Column |
|-------------|-----------------|
| DEA number | `dea_number` |
| State | `state` |
| Expiration | `expiration_date` |

---

## Implementation Plan

### Phase 1: Setup & Validation

**Step 1.1: Create NextEra Organization**
```sql
-- Run once in CredentialMate database
INSERT INTO organizations (name, slug, status, subscription_tier, max_providers, created_at, updated_at)
VALUES ('NextEra', 'nextera', 'active', 'enterprise', 500, NOW(), NOW())
RETURNING id;
-- Store this ID for all provider imports
```

**Step 1.2: Create Import Script Structure**
```
/Users/tmac/credentialmate/infra/scripts/
├── import_nextera_providers.py   # Main import script
├── excel_parser.py               # Parse Excel key-value format
└── field_mapping.py              # Field mapping configuration
```

### Phase 2: Excel Parser Development

**Step 2.1: Parse Vertical Key-Value Format**

The Excel files use a vertical layout:
- Column A: Field labels
- Column B: Field values
- Columns C-H: Multi-part data (education, employment, licenses)

```python
# Key row mappings (approximate, may vary by file)
FIELD_MAPPINGS = {
    'Full Legal Name': 'full_name',
    'NPI number': 'npi',
    'Real email address': 'email',
    'Phone number': 'phone',
    'Specialty': 'specialty',
    'Full SSN': 'ssn',
    'Date of birth': 'dob',
    'Board certification': 'board_cert',
}

# License table section (typically rows ~900+)
# Format: State | License # | Issue Date | Exp Date | Username | Password | PIN
```

**Step 2.2: Name Parsing Logic**
```python
def parse_provider_name(full_name: str) -> dict:
    """
    Parse "John Michael Doe, MD" into components
    Returns: {first_name, middle_name, last_name, suffix}
    """
    # Handle credentials: MD, DO, NP, PA, LMFT, etc.
    credential_pattern = r',?\s*(MD|DO|NP|PA|LMFT|PhD|APRN|RN|FNP-C|DNP)$'
    # Split name, extract suffix
```

### Phase 3: Data Import Script

**Step 3.1: Main Import Script**

Location: `/Users/tmac/credentialmate/infra/scripts/import_nextera_providers.py`

```python
#!/usr/bin/env python3
"""
Import NextEra providers from BlueShift Excel files to CredentialMate.

Usage:
    python import_nextera_providers.py --dry-run    # Preview only
    python import_nextera_providers.py              # Execute import
"""

import os
import openpyxl
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import models
from src.contexts.provider.models.provider import Provider
from src.contexts.provider.models.license import License
from src.contexts.organization.models.organization import Organization

SOURCE_DIR = '/Users/tmac/BlueShift_Provider_List/LEADS/INFO_Files_Organized'
NEXTERA_ORG_ID = None  # Set after org creation

def parse_excel_file(filepath: str) -> dict:
    """Parse vertical key-value Excel file into dict"""
    # Implementation details...
    pass

def create_provider(session, org_id: int, data: dict) -> Provider:
    """Create provider record with validation"""
    # Check for duplicate NPI
    existing = session.query(Provider).filter_by(npi=data['npi']).first()
    if existing:
        print(f"SKIP: Provider with NPI {data['npi']} already exists")
        return None

    provider = Provider(
        organization_id=org_id,
        npi=data['npi'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data.get('email'),
        phone=data.get('phone'),
        specialty=data.get('specialty'),
        ssn=data.get('ssn'),  # Will be encrypted by model
        date_of_birth=data.get('dob'),  # Will be encrypted
        is_deleted=False,
        npi_correction_count=0,
        npi_correction_history='[]'
    )
    session.add(provider)
    return provider

def create_licenses(session, org_id: int, provider_id: int, licenses: list):
    """Create license records for provider"""
    for lic in licenses:
        license = License(
            organization_id=org_id,
            provider_id=provider_id,
            state=lic['state'].upper(),
            license_number=lic['license_number'],
            license_type=lic.get('license_type', 'MD'),
            status='active',
            issue_date=lic.get('issue_date'),
            expiration_date=lic['expiration_date'],
            data_source='bulk_import',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(license)

def main(dry_run: bool = False):
    # Database connection
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get or create NextEra org
    org = session.query(Organization).filter_by(slug='nextera').first()
    if not org:
        print("ERROR: NextEra organization not found. Create it first.")
        return

    # Process each Excel file
    source_path = Path(SOURCE_DIR)
    files = list(source_path.glob('*.xlsx'))

    stats = {'success': 0, 'skipped': 0, 'errors': 0}

    for filepath in files:
        try:
            data = parse_excel_file(str(filepath))

            if dry_run:
                print(f"[DRY RUN] Would import: {data.get('full_name')} (NPI: {data.get('npi')})")
                continue

            provider = create_provider(session, org.id, data)
            if provider:
                session.flush()  # Get provider.id
                create_licenses(session, org.id, provider.id, data.get('licenses', []))
                stats['success'] += 1
            else:
                stats['skipped'] += 1

        except Exception as e:
            print(f"ERROR processing {filepath.name}: {e}")
            stats['errors'] += 1

    if not dry_run:
        session.commit()

    print(f"\nImport complete: {stats}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    main(dry_run=args.dry_run)
```

### Phase 4: Data Quality Handling

**Step 4.1: Handle Incomplete Records**

| Status | Count | Action |
|--------|-------|--------|
| [COMPLETE] | 287 | Import with all fields |
| [NO_EMAIL] | 38 | Import, email=NULL |
| [NO_PHONE] | 4 | Import, phone=NULL |
| [NO_PHONE-NO_EMAIL] | 4 | Import, both NULL |
| [NO_PHONE-NO_ADDRESS] | 4 | Import, skip address |
| [NO_EMAIL-NO_ADDRESS] | 2 | Import, skip both |
| [NO_PHONE-NO_EMAIL-NO_ADDRESS] | 39 | Review: may be inactive |

**Step 4.2: NPI Validation**
```python
def validate_npi(npi: str) -> bool:
    """Validate NPI is exactly 10 digits"""
    if not npi:
        return False
    npi_clean = npi.strip().replace('-', '').replace(' ', '')
    return len(npi_clean) == 10 and npi_clean.isdigit()
```

**Step 4.3: Skip Sensitive Non-Essential Data**

DO NOT IMPORT:
- Portal passwords (security risk)
- Credit card information (PCI compliance)
- AMA/AOA credentials (not needed)
- FCVS passwords (not needed)

### Phase 5: Execution Plan

**Step 5.1: Pre-Import Checklist**
- [ ] Create NextEra organization in database
- [ ] Backup current database
- [ ] Run import with `--dry-run` first
- [ ] Review dry run output for errors
- [ ] Verify NPI uniqueness (no collisions with existing providers)

**Step 5.2: Import Execution**
```bash
# From credentialmate directory
cd /Users/tmac/credentialmate

# Set database URL
export DATABASE_URL="postgresql://..."

# Dry run first
python infra/scripts/import_nextera_providers.py --dry-run

# Execute import
python infra/scripts/import_nextera_providers.py

# Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM providers WHERE organization_id = (SELECT id FROM organizations WHERE slug = 'nextera');"
```

**Step 5.3: Post-Import Verification**
```sql
-- Verify provider count
SELECT COUNT(*) FROM providers p
JOIN organizations o ON p.organization_id = o.id
WHERE o.slug = 'nextera';

-- Verify license count
SELECT COUNT(*) FROM licenses l
JOIN organizations o ON l.organization_id = o.id
WHERE o.slug = 'nextera';

-- Check for any missing NPIs
SELECT first_name, last_name FROM providers
WHERE organization_id = (SELECT id FROM organizations WHERE slug = 'nextera')
AND npi IS NULL;
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Duplicate NPIs | Check before insert, skip duplicates |
| Invalid data formats | Validate before insert, log errors |
| Missing required fields | Set defaults, flag for review |
| SSN/DOB encryption | Use model's EncryptedString field |
| Large transaction | Process in batches of 50 |
| Data loss | Backup DB before import |

---

## Timeline & Tasks

1. **Create import script structure** - Parse Excel vertical format
2. **Implement field mapping** - Map Excel fields to DB columns
3. **Add validation logic** - NPI format, state codes, dates
4. **Create NextEra org** - Single SQL insert
5. **Dry run import** - Test with --dry-run flag
6. **Execute import** - Run against database
7. **Verify results** - SQL queries + spot checks

---

## Files to Create

| File | Purpose |
|------|---------|
| `import_nextera_providers.py` | Main import script |
| `excel_parser.py` | Parse vertical key-value Excel |
| `field_mapping.py` | Field mapping configuration |

---

## Security Considerations

- SSN and DOB are automatically encrypted by CredentialMate's `EncryptedString` field type
- Portal passwords are NOT imported (security risk)
- Credit card data is NOT imported (PCI compliance)
- Import script should be run with least-privilege database credentials
- Audit logging will capture import operations via `created_by_id`

---

## Expected Outcome (Updated After Dry Run)

| Metric | Actual |
|--------|--------|
| Files with valid NPI | **229** |
| Providers importable | **229** |
| Email coverage | **100%** |
| License coverage | **95.6%** (219/229 have licenses) |
| Total licenses | **~890** |
| Avg licenses per provider | **3.9** |
| Files without NPI (cannot import) | **148** |
| Template files (skipped) | **5** |

### Files Without NPI

148 files lack NPI numbers and cannot be imported to CredentialMate (NPI is required unique identifier). Options:
1. **Manual lookup** - Use provider name to find NPI via NPPES registry
2. **Skip** - Import only the 229 with NPI, add others later via UI
3. **Generate temp NPI** - Not recommended (violates data integrity)

---

## Import Script Location

```
/Users/tmac/credentialmate/infra/scripts/import_nextera_from_excel.py
```

### Usage

```bash
# Dry run (preview only - works without DB)
python import_nextera_from_excel.py --dry-run

# Full import (requires DB connection via Docker)
docker compose exec backend python /app/infra/scripts/import_nextera_from_excel.py

# Import single file
python import_nextera_from_excel.py --file "Rama.xlsx" --dry-run
```
