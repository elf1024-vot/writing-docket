-- Historical Fiction Extension for Writing Docket
-- Adds era-specific and social context columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS social_class TEXT,
  ADD COLUMN IF NOT EXISTS historical_role TEXT,
  ADD COLUMN IF NOT EXISTS era_skills TEXT,
  ADD COLUMN IF NOT EXISTS era_limitations TEXT,
  ADD COLUMN IF NOT EXISTS speech_dialect_notes TEXT;

ALTER TABLE {{SCHEMA}}.locations
  ADD COLUMN IF NOT EXISTS era TEXT,
  ADD COLUMN IF NOT EXISTS historical_significance TEXT,
  ADD COLUMN IF NOT EXISTS period_details TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS historical_context TEXT,
  ADD COLUMN IF NOT EXISTS anachronism_flags TEXT,
  ADD COLUMN IF NOT EXISTS research_notes TEXT;

-- Period accuracy notes table
CREATE TABLE IF NOT EXISTS {{SCHEMA}}.research_notes (
  id SERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  verified_fact TEXT,
  source TEXT,
  applies_to TEXT,
  chapter_reference INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON {{SCHEMA}}.research_notes TO docket_editor;
GRANT SELECT ON {{SCHEMA}}.research_notes TO docket_claude;
GRANT USAGE, SELECT ON SEQUENCE {{SCHEMA}}.research_notes_id_seq TO docket_editor, docket_claude;
