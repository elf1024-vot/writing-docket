-- Thriller Extension for Writing Docket
-- Adds threat, stakes, and pacing columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS threat_level TEXT CHECK (threat_level IN ('minimal','moderate','serious','critical','lethal', NULL)),
  ADD COLUMN IF NOT EXISTS skills TEXT,
  ADD COLUMN IF NOT EXISTS weakness TEXT,
  ADD COLUMN IF NOT EXISTS agenda TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS stakes TEXT,
  ADD COLUMN IF NOT EXISTS threat_escalation TEXT,
  ADD COLUMN IF NOT EXISTS clock_ticking BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS deadline TEXT;

ALTER TABLE {{SCHEMA}}.locations
  ADD COLUMN IF NOT EXISTS security_level TEXT,
  ADD COLUMN IF NOT EXISTS entry_points TEXT,
  ADD COLUMN IF NOT EXISTS surveillance TEXT;
