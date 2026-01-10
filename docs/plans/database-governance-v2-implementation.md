# Database Governance v2 - Autonomous Implementation Plan

**Date**: 2026-01-08
**Project**: credentialmate
**Work Queue**: `tasks/work_queue_database_governance.json`
**Total Tasks**: 10
**Estimated Effort**: 5-6 hours

## Executive Summary

On 2026-01-08, the CredentialMate database was deleted when Docker restarted with a fresh volume. The existing 5-layer governance system had pattern gaps that allowed the deletion. This plan closes those gaps and adds automatic backup/recovery.

## Current State Analysis

### What Works (89% Complete)

| Layer | Component | Status |
|-------|-----------|--------|
| 1 | Database Deletion Guardian Hook | Partial (missing patterns) |
| 2 | AI Review Agent | Complete |
| 3 | Human Approval Skill | Complete |
| 4 | Pre-Execution Validator | Complete |
| 5 | Audit Trail | Complete |

### Critical Gaps Identified

1. **Hook Pattern Gaps** (P0)
   - `psql -c "DELETE..."` - NOT DETECTED
   - `docker volume rm` - NOT DETECTED
   - `docker volume prune` - NOT DETECTED
   - `alembic downgrade-1` - NOT DETECTED (regex requires trailing space)

2. **No Automatic Backups** (P1)
   - Manual backup script exists but requires human trigger
   - No scheduled/automatic backup service

3. **No Safe Wrappers** (P2)
   - `docker compose down -v` can be run directly without safety checks

## Implementation Tasks

### Phase 1: P0 - Critical Hook Fixes (30-45 min)

#### HOOK-001: Add psql Direct Command Patterns
**File**: `.claude/hooks/scripts/database-deletion-guardian.py`
**Insert after line 56**:

```python
    # Direct psql command patterns (CRITICAL - added post-Jan-8-incident)
    (r'psql\s+.*-c\s+.*DELETE', 'psql -c DELETE'),
    (r'psql\s+.*-c\s+.*DROP', 'psql -c DROP'),
    (r'psql\s+.*-c\s+.*TRUNCATE', 'psql -c TRUNCATE'),
    (r'psql\s+.*--command.*DELETE', 'psql --command DELETE'),
    (r'psql\s+.*--command.*DROP', 'psql --command DROP'),
    (r'psql\s+.*--command.*TRUNCATE', 'psql --command TRUNCATE'),
    (r'psql\s+-f\s+', 'psql -f (file execution)'),
    (r'psql\s+<\s+', 'psql stdin redirection'),

    # Docker exec psql patterns
    (r'docker\s+exec.*psql.*DELETE', 'docker exec psql DELETE'),
    (r'docker\s+exec.*psql.*DROP', 'docker exec psql DROP'),
    (r'docker\s+exec.*psql.*TRUNCATE', 'docker exec psql TRUNCATE'),
```

#### HOOK-002: Add Docker Volume Deletion Patterns
**File**: `.claude/hooks/scripts/database-deletion-guardian.py`
**Insert after line 38**:

```python
    # Docker volume deletion patterns (CRITICAL - added post-Jan-8-incident)
    (r'docker\s+volume\s+(rm|remove)', 'docker volume rm/remove'),
    (r'docker\s+volume\s+prune', 'docker volume prune'),
    (r'docker\s+system\s+prune.*--volumes', 'docker system prune --volumes'),
    (r'docker\s+system\s+prune\s+-a', 'docker system prune -a (may include volumes)'),
```

#### HOOK-003: Fix Alembic Pattern
**File**: `.claude/hooks/scripts/database-deletion-guardian.py`
**Line 56**: Change from:
```python
    (r'alembic\s+downgrade\s+', 'Alembic migration downgrade'),
```
To:
```python
    (r'alembic\s+downgrade', 'Alembic migration downgrade'),
```

### Phase 2: P1 - Automatic Backup System (1.5-2 hours)

#### BACKUP-001: Create Backup Entrypoint Script
**File**: `infra/scripts/auto_backup_entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "=== CredentialMate Automatic Backup Service ==="
echo "Starting hourly backup loop..."

while true; do
    HOUR=$(date +%H)
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    # Hourly backup (rolling 24 files)
    HOURLY_FILE="/backups/hourly-${HOUR}.dump"
    echo "[${TIMESTAMP}] Creating hourly backup: ${HOURLY_FILE}"

    if pg_dump -Fc "${PGDATABASE}" > "${HOURLY_FILE}.tmp"; then
        mv "${HOURLY_FILE}.tmp" "${HOURLY_FILE}"
        echo "[${TIMESTAMP}] Hourly backup successful: $(du -h ${HOURLY_FILE} | cut -f1)"
    else
        echo "[${TIMESTAMP}] ERROR: Hourly backup failed!"
        rm -f "${HOURLY_FILE}.tmp"
    fi

    # Daily backup at midnight (keep 7 days)
    if [ "${HOUR}" = "00" ]; then
        DAILY_FILE="/backups/daily-$(date +%Y%m%d).dump"
        cp "${HOURLY_FILE}" "${DAILY_FILE}"
        echo "[${TIMESTAMP}] Daily backup created: ${DAILY_FILE}"

        # Clean old dailies (keep 7)
        ls -t /backups/daily-*.dump 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
        echo "[${TIMESTAMP}] Cleaned old daily backups"
    fi

    # Health check marker
    touch /tmp/backup-healthy

    # Sleep 1 hour
    sleep 3600
done
```

#### BACKUP-002: Add Backup Service to docker-compose.yml
**File**: `docker-compose.yml`
**Insert before volumes section (line ~335)**:

```yaml
  # Automatic hourly backup service
  backup:
    image: postgres:15-alpine
    container_name: credmate-backup-local
    restart: unless-stopped
    volumes:
      - ./backups/postgres:/backups
      - ./infra/scripts/auto_backup_entrypoint.sh:/entrypoint.sh:ro
    environment:
      PGHOST: postgres
      PGUSER: credmate_user
      PGPASSWORD: credmate_local_pass
      PGDATABASE: credmate_local
    entrypoint: ["/bin/sh", "/entrypoint.sh"]
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - credmate-local
    profiles:
      - default
```

#### BACKUP-003: Update .gitignore
**File**: `.gitignore`
**Add at end**:

```gitignore
# Database backups (keep directory structure)
backups/postgres/*.dump
backups/postgres/*.sql.gz
backups/postgres/*.sql
!backups/postgres/.gitkeep
```

Also create: `backups/postgres/.gitkeep`

#### HOOK-004: Change Hook to Fail-Closed
**File**: `.claude/hooks/scripts/database-deletion-guardian.py`
**Lines 179-182**: Change error handling from fail-open to fail-closed:

```python
    except (json.JSONDecodeError, Exception) as e:
        # Fail-closed: Block operation if we can't parse input
        sys.stderr.write(f"database-deletion-guardian: BLOCKING - Failed to parse input: {e}\n")
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "block",
                "permissionDecisionReason": f"Database deletion guardian: Parse error - operation blocked for safety. Error: {e}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)
```

### Phase 3: P2 - Safe Wrappers (1 hour)

#### SAFE-001: Create safe_docker_down.sh
**File**: `infra/scripts/safe_docker_down.sh`

```bash
#!/bin/bash
# Safe wrapper for docker compose down
# Enforces backup before volume deletion

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for volume deletion flags
if [[ "$*" == *"-v"* ]] || [[ "$*" == *"--volumes"* ]]; then
    echo ""
    echo "========================================"
    echo "VOLUME DELETION DETECTED"
    echo "========================================"
    echo ""

    # Create backup first
    echo "Creating backup before volume deletion..."
    if bash "${SCRIPT_DIR}/backup_local_db.sh" "pre-docker-down-$(date +%Y%m%d-%H%M%S)"; then
        echo ""
        echo "Backup created successfully."
    else
        echo "WARNING: Backup may have failed. Proceeding anyway..."
    fi

    echo ""
    echo "Type 'DELETE-VOLUMES' to confirm volume deletion:"
    read -r CONFIRM

    if [ "$CONFIRM" != "DELETE-VOLUMES" ]; then
        echo "Aborted."
        exit 1
    fi

    echo ""
    echo "Proceeding with docker compose down -v..."
fi

docker compose "$@"
```

#### MAKE-001: Create Makefile
**File**: `Makefile`

```makefile
# CredentialMate Development Makefile
# Usage: make <target>

.PHONY: help up down down-volumes rebuild logs ps backup backups restore shell-db shell-backend test lint

help:
	@echo "CredentialMate Development Commands"
	@echo ""
	@echo "Docker:"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop services (keeps volumes)"
	@echo "  make down-volumes  - Stop + delete volumes (SAFE: backup + confirmation)"
	@echo "  make rebuild       - Rebuild and restart all services"
	@echo "  make logs          - Follow container logs"
	@echo "  make ps            - Show container status"
	@echo ""
	@echo "Database:"
	@echo "  make backup        - Create database backup"
	@echo "  make backups       - List all backups"
	@echo "  make restore       - Restore from backup (prompts for name)"
	@echo "  make shell-db      - Open psql shell"
	@echo ""
	@echo "Development:"
	@echo "  make shell-backend - Open backend container shell"
	@echo "  make test          - Run pytest"
	@echo "  make lint          - Run linting"

up:
	docker compose up -d

down:
	docker compose down

down-volumes:
	@bash infra/scripts/safe_docker_down.sh down -v

rebuild: down-volumes
	docker compose up --build -d

logs:
	docker compose logs -f

ps:
	docker compose ps

backup:
	@bash infra/scripts/backup_local_db.sh

backups:
	@echo "Available backups:"
	@ls -lh backups/postgres/ 2>/dev/null || echo "  (no backups found)"

restore:
	@echo "Available backups:"
	@ls -1 backups/postgres/*.sql.gz 2>/dev/null | xargs -I{} basename {} || echo "  (no backups found)"
	@echo ""
	@read -p "Enter backup filename: " BACKUP; \
	bash infra/scripts/restore_local_db.sh "$$BACKUP"

shell-db:
	docker exec -it credmate-postgres-local psql -U credmate_user -d credmate_local

shell-backend:
	docker exec -it credmate-backend-dev bash

test:
	docker exec credmate-backend-dev pytest

lint:
	docker exec credmate-backend-dev ruff check .
```

### Phase 4: P3 - Documentation (1 hour)

#### DOC-001: Create Recovery Playbook
**File**: `docs/04-operations/database-recovery-playbook.md`

Complete recovery procedures for all data loss scenarios.

## Execution Order

```
Parallel Group 1 (P0): HOOK-001, HOOK-002, HOOK-003
     ↓
Parallel Group 2 (P1): HOOK-004, BACKUP-001
     ↓
Parallel Group 3 (P1): BACKUP-002, BACKUP-003
     ↓
Parallel Group 4 (P2): SAFE-001, MAKE-001
     ↓
Group 5 (P3): DOC-001
```

## Verification Commands

After implementation, verify all patterns are blocked:

```bash
# Should all be BLOCKED by hook:
docker compose down -v
docker volume rm postgres_data
docker volume prune
docker system prune -a --volumes
psql -c "DELETE FROM users"
psql -f /tmp/delete.sql
docker exec credmate-postgres-local psql -c "DROP TABLE users"
alembic downgrade-1
alembic downgrade base
```

## Autonomous Loop Command

```bash
python autonomous_loop.py --project credentialmate --max-iterations 100 \
    --work-queue tasks/work_queue_database_governance.json
```

## Success Criteria

- [ ] All P0 hook patterns detect and block their target commands
- [ ] Automatic backup service starts with docker compose up
- [ ] Hourly backup files appear in backups/postgres/
- [ ] `make down-volumes` requires backup + typed confirmation
- [ ] Recovery playbook documents all scenarios

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Hook changes break legitimate operations | Safe patterns list excludes read operations |
| Backup service fails silently | Health check file + container restart policy |
| Makefile targets conflict with existing workflow | Help target documents all commands |
