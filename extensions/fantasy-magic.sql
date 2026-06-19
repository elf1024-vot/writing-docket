-- Fantasy Magic Extension for Writing Docket
-- Adds magic system columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS magic_type TEXT,
  ADD COLUMN IF NOT EXISTS power_level TEXT CHECK (power_level IN ('none','minor','moderate','strong','exceptional','legendary', NULL)),
  ADD COLUMN IF NOT EXISTS magic_cost TEXT,
  ADD COLUMN IF NOT EXISTS magic_limitations TEXT,
  ADD COLUMN IF NOT EXISTS magic_source TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS magic_used TEXT,
  ADD COLUMN IF NOT EXISTS magic_consequences TEXT,
  ADD COLUMN IF NOT EXISTS power_balance_shift TEXT;

ALTER TABLE {{SCHEMA}}.locations
  ADD COLUMN IF NOT EXISTS magic_resonance TEXT,
  ADD COLUMN IF NOT EXISTS wards TEXT,
  ADD COLUMN IF NOT EXISTS magical_history TEXT;
