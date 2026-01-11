#!/usr/bin/env python3
"""
Generate Implementation Tasks for Duplicate Handling ADRs (007, 008, 009)

This script:
1. Extracts tasks from ADR-007 (Data Architecture)
2. Extracts tasks from ADR-008 (Service Architecture)
3. Extracts tasks from ADR-009 (UX/UI Design)
4. Registers all tasks with work queue
5. Generates migration files from ADR-007
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestration.adr_to_tasks import extract_tasks_from_adr, register_tasks_with_queue
from tasks.work_queue import WorkQueue


def generate_tasks_from_adrs():
    """Generate tasks from ADR-007, 008, 009."""

    # Paths
    adr_dir = project_root / "adapters" / "credentialmate" / "plans" / "decisions"
    work_queue_path = project_root / "tasks" / "work_queue_credentialmate_features.json"

    # Load work queue
    queue = WorkQueue(features=[], sequence=0, fingerprints=[])

    # Load existing queue data if file exists
    if work_queue_path.exists():
        import json
        with open(work_queue_path, 'r') as f:
            data = json.load(f)
            queue.features = [task for task in data.get('features', [])]
            queue.sequence = data.get('sequence', 0)
            queue.fingerprints = data.get('fingerprints', [])

    # ADRs to process
    adrs = [
        ("ADR-007", "duplicate-handling-data-architecture"),
        ("ADR-008", "duplicate-handling-service-architecture"),
        ("ADR-009", "duplicate-handling-user-experience"),
    ]

    all_created_ids = []

    for adr_num, adr_slug in adrs:
        adr_path = adr_dir / f"{adr_num}-{adr_slug}.md"

        print(f"\n{'='*60}")
        print(f"Processing {adr_num}: {adr_slug}")
        print(f"{'='*60}")

        # Extract tasks from ADR
        tasks = extract_tasks_from_adr(
            adr_path=adr_path,
            adr_number=adr_num,
            project="credentialmate"
        )

        print(f"Extracted {len(tasks)} tasks from {adr_num}")

        # Register with work queue
        created_ids = register_tasks_with_queue(
            tasks=tasks,
            adr_number=adr_num,
            work_queue=queue,
            project_root=project_root
        )

        all_created_ids.extend(created_ids)

        print(f"Registered {len(created_ids)} tasks")
        for task_id in created_ids:
            task = next(t for t in queue.features if t.id == task_id)
            print(f"  - {task_id}: {task.description[:60]}...")

    # Save queue
    queue.save(work_queue_path)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total tasks created: {len(all_created_ids)}")
    print(f"Work queue saved to: {work_queue_path}")

    return all_created_ids


def generate_migration_files():
    """Generate migration files from ADR-007 schema changes."""

    migrations_dir = Path("/Users/tmac/1_REPOS/credentialmate/apps/backend-api/alembic/versions")

    # Timestamp for migration files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    migrations = [
        {
            "name": f"{timestamp}_01_add_renewal_chain_tracking",
            "description": "Add renewal chain tracking to licenses and CME activities",
            "content": """\"\"\"Add renewal chain tracking

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # Add renewal chain tracking to licenses
    op.add_column('licenses', sa.Column('renewal_chain_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('licenses', sa.Column('previous_version_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_licenses_previous_version', 'licenses', 'licenses',
                          ['previous_version_id'], ['id'])

    # Add missing duplicate_match_type to CME activities
    op.add_column('cme_activities', sa.Column('duplicate_match_type', sa.String(length=20), nullable=True))
    op.add_column('cme_activities', sa.Column('duplicate_detected_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # Add entry_method and entry_context (if not exists)
    # Check if columns exist first to make migration idempotent
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    licenses_columns = [col['name'] for col in inspector.get_columns('licenses')]
    if 'entry_method' not in licenses_columns:
        op.add_column('licenses', sa.Column('entry_method', sa.String(length=50), nullable=True))
    if 'entry_context' not in licenses_columns:
        op.add_column('licenses', sa.Column('entry_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    cme_columns = [col['name'] for col in inspector.get_columns('cme_activities')]
    if 'entry_method' not in cme_columns:
        op.add_column('cme_activities', sa.Column('entry_method', sa.String(length=50), nullable=True))
    if 'entry_context' not in cme_columns:
        op.add_column('cme_activities', sa.Column('entry_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove renewal chain tracking
    op.drop_constraint('fk_licenses_previous_version', 'licenses', type_='foreignkey')
    op.drop_column('licenses', 'previous_version_id')
    op.drop_column('licenses', 'renewal_chain_id')

    # Remove CME duplicate fields
    op.drop_column('cme_activities', 'duplicate_detected_at')
    op.drop_column('cme_activities', 'duplicate_match_type')

    # Note: Not removing entry_method/entry_context in downgrade to be safe
    # These may be used by other features
"""
        },
        {
            "name": f"{timestamp}_02_add_duplicate_detection_indexes",
            "description": "Add performance indexes for duplicate detection queries",
            "content": """\"\"\"Add duplicate detection indexes

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

\"\"\"
from alembic import op

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # Index 1: Fast duplicate detection queries (currently table scans)
    op.create_index(
        'ix_licenses_dup_detect',
        'licenses',
        ['provider_id', 'state', 'license_number', 'organization_id', 'is_deleted'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'ix_dea_dup_detect',
        'dea_registrations',
        ['dea_number', 'expiration_date', 'is_deleted'],
        unique=False,
        postgresql_concurrently=True
    )

    op.create_index(
        'ix_csr_dup_detect',
        'controlled_substance_registrations',
        ['provider_id', 'state', 'registration_number', 'organization_id', 'is_deleted'],
        unique=False,
        postgresql_concurrently=True
    )

    # Index 2: CME certificate lookup (high QPS endpoint)
    op.create_index(
        'ix_cme_cert_lookup',
        'cme_activities',
        ['certificate_number', 'provider_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='certificate_number IS NOT NULL AND is_deleted = false'
    )

    # Index 3: Fast calculable (non-duplicate) record queries
    op.create_index(
        'ix_licenses_calculable',
        'licenses',
        ['provider_id', 'organization_id', 'expiration_date'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='is_deleted = false AND exclude_from_calculations = false'
    )

    op.create_index(
        'ix_cme_calculable_credits',
        'cme_activities',
        ['provider_id', 'completion_date', 'credits_earned'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='is_deleted = false AND exclude_from_calculations = false'
    )

    # Index 4: Duplicate group queries
    op.create_index(
        'ix_licenses_duplicate_group',
        'licenses',
        ['duplicate_group_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='duplicate_group_id IS NOT NULL'
    )

    op.create_index(
        'ix_dea_duplicate_group',
        'dea_registrations',
        ['duplicate_group_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='duplicate_group_id IS NOT NULL'
    )

    op.create_index(
        'ix_csr_duplicate_group',
        'controlled_substance_registrations',
        ['duplicate_group_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='duplicate_group_id IS NOT NULL'
    )

    op.create_index(
        'ix_cme_duplicate_group',
        'cme_activities',
        ['duplicate_group_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='duplicate_group_id IS NOT NULL'
    )

    # Index 5: Renewal chain lookups
    op.create_index(
        'ix_licenses_renewal_chain',
        'licenses',
        ['renewal_chain_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='renewal_chain_id IS NOT NULL'
    )


def downgrade():
    # Drop all indexes
    op.drop_index('ix_licenses_renewal_chain', table_name='licenses')
    op.drop_index('ix_cme_duplicate_group', table_name='cme_activities')
    op.drop_index('ix_csr_duplicate_group', table_name='controlled_substance_registrations')
    op.drop_index('ix_dea_duplicate_group', table_name='dea_registrations')
    op.drop_index('ix_licenses_duplicate_group', table_name='licenses')
    op.drop_index('ix_cme_calculable_credits', table_name='cme_activities')
    op.drop_index('ix_licenses_calculable', table_name='licenses')
    op.drop_index('ix_cme_cert_lookup', table_name='cme_activities')
    op.drop_index('ix_csr_dup_detect', table_name='controlled_substance_registrations')
    op.drop_index('ix_dea_dup_detect', table_name='dea_registrations')
    op.drop_index('ix_licenses_dup_detect', table_name='licenses')
"""
        },
        {
            "name": f"{timestamp}_03_add_cross_org_indexes",
            "description": "Add cross-org duplicate detection indexes and audit table",
            "content": """\"\"\"Add cross-org duplicate detection

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # Cross-org license lookup (superuser queries)
    op.create_index(
        'ix_licenses_cross_org_lookup',
        'licenses',
        ['state', 'license_number', 'expiration_date'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where='is_deleted = false',
        postgresql_include=['provider_id', 'organization_id', 'duplicate_group_id']
    )

    # Cross-org audit log
    op.create_table(
        'cross_org_access_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('credential_type', sa.String(length=50), nullable=False),
        sa.Column('search_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('accessed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_cross_org_access_log_user', 'cross_org_access_log', ['user_id', 'accessed_at'])
    op.create_index('idx_cross_org_access_log_type', 'cross_org_access_log', ['credential_type', 'accessed_at'])

    # Add scope column to duplicate_events
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    duplicate_events_columns = [col['name'] for col in inspector.get_columns('duplicate_events')]
    if 'scope' not in duplicate_events_columns:
        op.add_column('duplicate_events', sa.Column('scope', sa.String(length=20), server_default='organization', nullable=False))

    op.create_index(
        'idx_duplicate_events_cross_org',
        'duplicate_events',
        ['scope', 'created_at'],
        unique=False,
        postgresql_where="scope = 'cross_org'"
    )


def downgrade():
    op.drop_index('idx_duplicate_events_cross_org', table_name='duplicate_events')
    op.drop_column('duplicate_events', 'scope')
    op.drop_index('idx_cross_org_access_log_type', table_name='cross_org_access_log')
    op.drop_index('idx_cross_org_access_log_user', table_name='cross_org_access_log')
    op.drop_table('cross_org_access_log')
    op.drop_index('ix_licenses_cross_org_lookup', table_name='licenses')
"""
        },
        {
            "name": f"{timestamp}_04_add_file_dedup_fields",
            "description": "Add file deduplication tracking fields to documents table",
            "content": """\"\"\"Add file deduplication fields

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # Add deduplication tracking to documents
    op.add_column('documents', sa.Column('dedup_source_id', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('dedup_reason', sa.String(length=50), nullable=True))

    op.create_foreign_key('fk_documents_dedup_source', 'documents', 'documents',
                          ['dedup_source_id'], ['id'])

    # Index for hash-based deduplication queries
    op.create_index(
        'ix_documents_hash_lookup',
        'documents',
        ['sha256_hash', 'organization_id', 'is_deleted'],
        unique=False,
        postgresql_concurrently=True
    )

    # Index for filename+size fallback
    op.create_index(
        'ix_documents_filename_size',
        'documents',
        ['original_filename', 'file_size_bytes', 'created_at', 'organization_id'],
        unique=False,
        postgresql_concurrently=True,
        postgresql_where="created_at > NOW() - INTERVAL '30 days'"
    )


def downgrade():
    op.drop_index('ix_documents_filename_size', table_name='documents')
    op.drop_index('ix_documents_hash_lookup', table_name='documents')
    op.drop_constraint('fk_documents_dedup_source', 'documents', type_='foreignkey')
    op.drop_column('documents', 'dedup_reason')
    op.drop_column('documents', 'dedup_source_id')
"""
        },
        {
            "name": f"{timestamp}_05_backfill_duplicate_metadata",
            "description": "Backfill existing records with duplicate metadata",
            "content": """\"\"\"Backfill duplicate metadata

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {create_date}

\"\"\"
from alembic import op

# revision identifiers
revision = '{revision_id}'
down_revision = '{down_revision}'
branch_labels = None
depends_on = None


def upgrade():
    # Set entry_method based on data_source (best guess for legacy data)
    op.execute(\"\"\"
        UPDATE licenses SET entry_method = CASE
            WHEN data_source = 'manual_entry' THEN 'web_form'
            WHEN data_source = 'document_upload' THEN 'ai_extraction'
            WHEN data_source = 'verified_external' THEN 'api_webhook'
            WHEN data_source = 'migration' THEN 'cli_script'
            ELSE 'legacy_import'
        END
        WHERE entry_method IS NULL
    \"\"\")

    op.execute(\"\"\"
        UPDATE cme_activities SET entry_method = CASE
            WHEN data_source = 'manual_entry' THEN 'web_form'
            WHEN data_source = 'document_upload' THEN 'ai_extraction'
            WHEN data_source = 'verified_external' THEN 'api_webhook'
            WHEN data_source = 'migration' THEN 'cli_script'
            ELSE 'legacy_import'
        END
        WHERE entry_method IS NULL
    \"\"\")

    # Generate duplicate_group_id for existing duplicates
    op.execute(\"\"\"
        WITH duplicate_groups AS (
            SELECT
                MIN(id) as primary_id,
                ARRAY_AGG(id ORDER BY created_at) as all_ids,
                gen_random_uuid() as group_id
            FROM licenses
            WHERE is_deleted = false
            GROUP BY provider_id, state, license_number, organization_id
            HAVING COUNT(*) > 1
        )
        UPDATE licenses l
        SET
            duplicate_group_id = dg.group_id,
            is_primary_record = (l.id = dg.primary_id),
            duplicate_detected_at = NOW()
        FROM duplicate_groups dg
        WHERE l.id = ANY(dg.all_ids)
    \"\"\")

    # Backfill duplicate_match_type for CME activities
    op.execute(\"\"\"
        UPDATE cme_activities
        SET duplicate_match_type = 'perfect'
        WHERE duplicate_group_id IS NOT NULL
        AND is_primary_record = false
    \"\"\")

    # Link renewal chains (heuristic: same license number, sequential expiration dates)
    op.execute(\"\"\"
        WITH renewal_chains AS (
            SELECT
                id,
                LAG(id) OVER (
                    PARTITION BY provider_id, state, license_number
                    ORDER BY expiration_date
                ) as prev_id,
                gen_random_uuid() OVER (
                    PARTITION BY provider_id, state, license_number
                ) as chain_id
            FROM licenses
            WHERE is_deleted = false
        )
        UPDATE licenses l
        SET
            renewal_chain_id = rc.chain_id,
            previous_version_id = rc.prev_id
        FROM renewal_chains rc
        WHERE l.id = rc.id
    \"\"\")


def downgrade():
    # Reset backfilled fields
    op.execute(\"\"\"
        UPDATE licenses SET
            entry_method = NULL,
            duplicate_group_id = NULL,
            is_primary_record = NULL,
            duplicate_detected_at = NULL,
            renewal_chain_id = NULL,
            previous_version_id = NULL
        WHERE entry_method IN ('web_form', 'ai_extraction', 'api_webhook', 'cli_script', 'legacy_import')
    \"\"\")

    op.execute(\"\"\"
        UPDATE cme_activities SET
            entry_method = NULL,
            duplicate_match_type = NULL
        WHERE entry_method IN ('web_form', 'ai_extraction', 'api_webhook', 'cli_script', 'legacy_import')
    \"\"\")
"""
        }
    ]

    print(f"\n{'='*60}")
    print(f"GENERATING MIGRATION FILES")
    print(f"{'='*60}")

    for migration in migrations:
        filepath = migrations_dir / f"{migration['name']}.py"

        # Write migration file
        filepath.write_text(migration['content'])

        print(f"Created: {filepath.name}")
        print(f"  Description: {migration['description']}")

    print(f"\nMigrations saved to: {migrations_dir}")
    print(f"\nNOTE: You need to update revision IDs before running migrations:")
    print(f"  1. Generate revision ID: alembic revision")
    print(f"  2. Replace {{revision_id}} and {{down_revision}} placeholders")
    print(f"  3. Replace {{create_date}} with current timestamp")


if __name__ == "__main__":
    print("="*60)
    print("DUPLICATE HANDLING IMPLEMENTATION TASK GENERATOR")
    print("="*60)
    print()

    # Step 1: Generate tasks from ADRs
    print("STEP 1: Extracting tasks from ADRs 007, 008, 009...")
    task_ids = generate_tasks_from_adrs()

    # Step 2: Generate migration files
    print("\n\nSTEP 2: Generating migration files from ADR-007...")
    generate_migration_files()

    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"\nNext steps:")
    print(f"  1. Review generated tasks in work_queue_credentialmate_features.json")
    print(f"  2. Update migration file revision IDs")
    print(f"  3. Review and approve ADR-007, 008, 009")
    print(f"  4. Run migrations: cd credentialmate && alembic upgrade head")
    print(f"  5. Start autonomous loop: python autonomous_loop.py --project credentialmate")
