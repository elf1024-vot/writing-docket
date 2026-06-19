-- Mystery Extension for Writing Docket
-- Adds clue tracking, alibi, and investigation columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS alibi TEXT,
  ADD COLUMN IF NOT EXISTS motive TEXT,
  ADD COLUMN IF NOT EXISTS opportunity TEXT,
  ADD COLUMN IF NOT EXISTS red_herring BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS knows_what TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS clues_planted TEXT,
  ADD COLUMN IF NOT EXISTS clues_revealed TEXT,
  ADD COLUMN IF NOT EXISTS red_herrings TEXT,
  ADD COLUMN IF NOT EXISTS investigation_progress TEXT;

-- Clue tracking table
CREATE TABLE IF NOT EXISTS {{SCHEMA}}.clues (
  id SERIAL PRIMARY KEY,
  clue TEXT NOT NULL,
  planted_chapter INTEGER,
  revealed_chapter INTEGER,
  points_to TEXT,
  misleads_to TEXT,
  status TEXT DEFAULT 'planted' CHECK (status IN ('planted','revealed','explained','red-herring')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON {{SCHEMA}}.clues TO docket_editor;
GRANT SELECT ON {{SCHEMA}}.clues TO docket_claude;
GRANT USAGE, SELECT ON SEQUENCE {{SCHEMA}}.clues_id_seq TO docket_editor, docket_claude;
