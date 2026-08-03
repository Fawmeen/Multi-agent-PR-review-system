-- 001_init.sql
-- Idempotent schema creation for AI-PR Review Agent
-- Run against your Tiger Cloud database once.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS vectorscale;

-- ============================================================
-- TABLES
-- ============================================================

-- 1. Reviews table: one row per PR review
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    repository TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    commit_sha TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    summary JSONB NOT NULL DEFAULT '{}',
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0.0,
    workflow_run_id TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Findings table: one row per individual finding
CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
    agent TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    suggestion TEXT,
    rule_reference TEXT,
    is_approved BOOLEAN DEFAULT FALSE,
    is_disputed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for HITL queue: fetch unapproved findings quickly
CREATE INDEX IF NOT EXISTS idx_findings_pending_approval
    ON findings (is_approved, is_disputed, created_at);

-- 3. Code chunks table for RAG (hybrid search)
CREATE TABLE IF NOT EXISTS code_chunks (
    id BIGSERIAL PRIMARY KEY,
    repository TEXT NOT NULL,
    file_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(768),
    extra_data JSONB NOT NULL DEFAULT '{}',  
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Agent events hypertable (time-series: tracing, cost tracking)
CREATE TABLE IF NOT EXISTS agent_events (
    time TIMESTAMPTZ NOT NULL,
    event_type TEXT NOT NULL,
    agent_name TEXT,
    workflow_run_id TEXT,
    tokens_used INTEGER DEFAULT 0,
    duration_ms DOUBLE PRECISION,
    extra_data JSONB NOT NULL DEFAULT '{}'
);

-- Convert agent_events into a hypertable (TimescaleDB)
SELECT create_hypertable('agent_events', 'time', if_not_exists => TRUE);

-- ============================================================
-- INDEXES for RAG
-- ============================================================

-- Full-text search index on code chunk content
CREATE INDEX IF NOT EXISTS idx_code_chunks_fts
    ON code_chunks USING GIN (to_tsvector('english', content));

-- DiskANN index for vector similarity (pgvectorscale)
CREATE INDEX IF NOT EXISTS idx_code_chunks_embedding
    ON code_chunks USING diskann (embedding);

-- ============================================================
-- CONTINUOUS AGGREGATES (for economics dashboard)
-- ============================================================

-- 1-minute aggregate for real-time cost monitoring-- ============================================================
-- CONTINUOUS AGGREGATES (for economics dashboard)
-- ============================================================

-- 1‑minute aggregate for real‑time cost monitoring
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_health_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    agent_name,
    COUNT(*) AS event_count,
    SUM(tokens_used) AS total_tokens,
    AVG(duration_ms) AS avg_duration_ms,
    MAX(duration_ms) AS max_duration_ms
FROM agent_events
WHERE event_type = 'llm_call'
GROUP BY bucket, agent_name
WITH NO DATA;

-- Refresh policy — only add if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM timescaledb_information.jobs
        WHERE proc_name = 'policy_refresh_continuous_aggregate'
        AND hypertable_name = 'agent_health_1m'
    ) THEN
        PERFORM add_continuous_aggregate_policy('agent_health_1m',
            start_offset => INTERVAL '5 minutes',
            end_offset => INTERVAL '1 minute',
            schedule_interval => INTERVAL '1 minute'
        );
    END IF;
END $$;