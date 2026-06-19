-- Fantasy Worldbuilding Extension for Writing Docket
-- Adds political, historical, and world-state columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS title TEXT,
  ADD COLUMN IF NOT EXISTS house_clan TEXT,
  ADD COLUMN IF NOT EXISTS political_allegiance TEXT,
  ADD COLUMN IF NOT EXISTS prophecy_role TEXT,
  ADD COLUMN IF NOT EXISTS languages_spoken TEXT;

ALTER TABLE {{SCHEMA}}.locations
  ADD COLUMN IF NOT EXISTS political_control TEXT,
  ADD COLUMN IF NOT EXISTS history TEXT,
  ADD COLUMN IF NOT EXISTS myths_legends TEXT,
  ADD COLUMN IF NOT EXISTS trade_routes TEXT;

ALTER TABLE {{SCHEMA}}.groups
  ADD COLUMN IF NOT EXISTS political_power TEXT CHECK (political_power IN ('dominant','strong','moderate','weak','underground', NULL)),
  ADD COLUMN IF NOT EXISTS founding_era TEXT,
  ADD COLUMN IF NOT EXISTS enemies TEXT,
  ADD COLUMN IF NOT EXISTS allies TEXT,
  ADD COLUMN IF NOT EXISTS secrets TEXT;

-- World state table for tracking macro-level changes
CREATE TABLE IF NOT EXISTS {{SCHEMA}}.world_events (
  id SERIAL PRIMARY KEY,
  event TEXT NOT NULL,
  chapter_number INTEGER,
  region TEXT,
  political_impact TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON {{SCHEMA}}.world_events TO docket_editor;
GRANT SELECT ON {{SCHEMA}}.world_events TO docket_claude;
GRANT USAGE, SELECT ON SEQUENCE {{SCHEMA}}.world_events_id_seq TO docket_editor, docket_claude;
