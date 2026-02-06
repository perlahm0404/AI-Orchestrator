-- Migration 002: Add progress rollup triggers
-- Automatically update feature/epic status when tasks/features complete

-- Trigger: Update feature status when task completes
CREATE TRIGGER IF NOT EXISTS update_feature_status_on_task_complete
AFTER UPDATE ON tasks
WHEN NEW.status = 'completed'
BEGIN
    UPDATE features
    SET
        status = CASE
            WHEN (SELECT COUNT(*) FROM tasks WHERE feature_id = NEW.feature_id AND status != 'completed') = 0
            THEN 'completed'
            ELSE 'in_progress'
        END,
        updated_at = datetime('now')
    WHERE id = NEW.feature_id;
END;

-- Trigger: Update epic status when feature completes
CREATE TRIGGER IF NOT EXISTS update_epic_status_on_feature_complete
AFTER UPDATE ON features
WHEN NEW.status = 'completed'
BEGIN
    UPDATE epics
    SET
        status = CASE
            WHEN (SELECT COUNT(*) FROM features WHERE epic_id = NEW.epic_id AND status != 'completed') = 0
            THEN 'completed'
            ELSE 'in_progress'
        END,
        updated_at = datetime('now')
    WHERE id = NEW.epic_id;
END;

-- Update schema version
INSERT INTO schema_version (version, description) VALUES (2, 'Add progress rollup triggers');
