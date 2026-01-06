-- AI Orchestrator Initial Schema
-- Migration: 001_initial_schema
-- Date: 2026-01-05
--
-- This creates the base tables for AI Brain operation.
-- Implementation: Phase 0

-- Issues table (bugs and tasks to work on)
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(50),  -- e.g., GitHub issue number
    project VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'open',  -- open, assigned, in_progress, pending_review, resolved, rejected
    priority VARCHAR(10) DEFAULT 'medium',
    assigned_agent VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (agent execution sessions)
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(50) PRIMARY KEY,
    agent VARCHAR(20) NOT NULL,
    project VARCHAR(50) NOT NULL,
    issue_id INTEGER REFERENCES issues(id),
    status VARCHAR(20) DEFAULT 'running',  -- running, paused, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    checkpoint_path TEXT  -- Path to checkpoint file
);

-- Audit log with causality tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES sessions(id),
    agent VARCHAR(20) NOT NULL,
    action VARCHAR(50) NOT NULL,
    details JSONB,
    caused_by VARCHAR(50),  -- ID of action that caused this one
    project VARCHAR(50),
    issue_id INTEGER REFERENCES issues(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for causality chain queries
CREATE INDEX IF NOT EXISTS idx_audit_caused_by ON audit_log(caused_by);
CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_log(session_id);

-- Knowledge Objects table
CREATE TABLE IF NOT EXISTS knowledge_objects (
    id VARCHAR(50) PRIMARY KEY,
    project VARCHAR(50) NOT NULL,
    issue_id INTEGER REFERENCES issues(id),
    what_was_learned TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    prevention_rule TEXT NOT NULL,
    detection_pattern TEXT,
    tags TEXT[],  -- Array of tags for matching
    status VARCHAR(20) DEFAULT 'draft',  -- draft, approved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by VARCHAR(50)
);

-- Index for tag-based matching
CREATE INDEX IF NOT EXISTS idx_ko_tags ON knowledge_objects USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_ko_project ON knowledge_objects(project);

-- Circuit breaker state
CREATE TABLE IF NOT EXISTS circuit_breakers (
    agent VARCHAR(20) NOT NULL,
    project VARCHAR(50) NOT NULL,
    state VARCHAR(20) DEFAULT 'CLOSED',  -- CLOSED, OPEN, HALF_OPEN
    failure_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMP,
    opened_at TIMESTAMP,
    PRIMARY KEY (agent, project)
);
