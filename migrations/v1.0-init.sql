-- Writing Docket Migration v1.0
-- Initial schema version placeholder.
-- The actual schema is created by postgres/init.sql during docker compose up.
-- This file exists to establish the baseline for future migrations.
-- No SQL to run — the schema is already at v1.0 after build.

-- Future migrations will be added as v1.1-description.sql, v1.2-description.sql, etc.
-- Each migration file must be idempotent (safe to run twice).
-- Use IF NOT EXISTS and IF EXISTS guards throughout.

SELECT 'Writing Docket schema v1.0 baseline' AS migration_status;
