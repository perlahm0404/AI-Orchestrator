-- SQLite Schema for AI Orchestrator Work Queue
-- Implements epic → feature → task → test_case hierarchy
-- Reference: KO-aio-002 (SQLite persistence), KO-aio-004 (Feature hierarchy)

-- Enable foreign keys (SQLite has them off by default)
PRAGMA foreign_keys = ON;

-- Schema versioning table (for migrations)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial schema version
INSERT INTO schema_version (version, description) VALUES (1, 'Initial schema: epics, features, tasks, test_cases');

-- Epics table (top-level organizational unit)
CREATE TABLE IF NOT EXISTS epics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Features table (belongs to epic, has many tasks)
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    epic_id TEXT,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked')),
    priority INTEGER DEFAULT 2,  -- 0=P0, 1=P1, 2=P2
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (epic_id) REFERENCES epics(id) ON DELETE CASCADE
);

-- Tasks table (belongs to feature)
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked')),
    retry_budget INTEGER DEFAULT 15,
    retries_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE CASCADE
);

-- Test cases table (belongs to task or feature)
CREATE TABLE IF NOT EXISTS test_cases (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    feature_id TEXT,
    description TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'passing', 'failing')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_features_epic_id ON features(epic_id);
CREATE INDEX IF NOT EXISTS idx_features_status ON features(status);
CREATE INDEX IF NOT EXISTS idx_tasks_feature_id ON tasks(feature_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_test_cases_task_id ON test_cases(task_id);
CREATE INDEX IF NOT EXISTS idx_test_cases_feature_id ON test_cases(feature_id);

-- Trigger: Update feature status when all tasks complete
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

-- Trigger: Update epic status when all features complete
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

-- Trigger: Update updated_at on epic modification
CREATE TRIGGER IF NOT EXISTS update_epics_timestamp
AFTER UPDATE ON epics
FOR EACH ROW
BEGIN
    UPDATE epics SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger: Update updated_at on feature modification
CREATE TRIGGER IF NOT EXISTS update_features_timestamp
AFTER UPDATE ON features
FOR EACH ROW
BEGIN
    UPDATE features SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger: Update updated_at on task modification
CREATE TRIGGER IF NOT EXISTS update_tasks_timestamp
AFTER UPDATE ON tasks
FOR EACH ROW
BEGIN
    UPDATE tasks SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger: Set completed_at when task status becomes completed
CREATE TRIGGER IF NOT EXISTS set_task_completed_at
AFTER UPDATE ON tasks
WHEN NEW.status = 'completed' AND OLD.status != 'completed'
BEGIN
    UPDATE tasks SET completed_at = datetime('now') WHERE id = NEW.id;
END;
