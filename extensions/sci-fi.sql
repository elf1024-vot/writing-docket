-- Sci-Fi Extension for Writing Docket
-- Adds technology, faction, and world-state columns

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS faction TEXT,
  ADD COLUMN IF NOT EXISTS augmentation TEXT,
  ADD COLUMN IF NOT EXISTS tech_affinity TEXT,
  ADD COLUMN IF NOT EXISTS origin_world TEXT,
  ADD COLUMN IF NOT EXISTS clearance_level TEXT;

ALTER TABLE {{SCHEMA}}.locations
  ADD COLUMN IF NOT EXISTS tech_level TEXT,
  ADD COLUMN IF NOT EXISTS controlled_by TEXT,
  ADD COLUMN IF NOT EXISTS hazards TEXT,
  ADD COLUMN IF NOT EXISTS coordinates TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS tech_featured TEXT,
  ADD COLUMN IF NOT EXISTS faction_conflict TEXT,
  ADD COLUMN IF NOT EXISTS world_state_notes TEXT;

ALTER TABLE {{SCHEMA}}.groups
  ADD COLUMN IF NOT EXISTS faction_type TEXT CHECK (faction_type IN ('government','corporation','rebel','cult','neutral','alien', NULL)),
  ADD COLUMN IF NOT EXISTS home_world TEXT,
  ADD COLUMN IF NOT EXISTS resources TEXT;
