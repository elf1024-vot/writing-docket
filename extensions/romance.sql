-- Romance Extension for Writing Docket
-- Adds character relationship and arc columns for romance genre

ALTER TABLE {{SCHEMA}}.characters
  ADD COLUMN IF NOT EXISTS love_language TEXT,
  ADD COLUMN IF NOT EXISTS attachment_style TEXT CHECK (attachment_style IN ('secure','anxious','avoidant','disorganized', NULL)),
  ADD COLUMN IF NOT EXISTS emotional_wall TEXT,
  ADD COLUMN IF NOT EXISTS romantic_arc TEXT,
  ADD COLUMN IF NOT EXISTS wound TEXT,
  ADD COLUMN IF NOT EXISTS need TEXT;

ALTER TABLE {{SCHEMA}}.chapters
  ADD COLUMN IF NOT EXISTS tension_type TEXT CHECK (tension_type IN ('slow burn','conflict','misunderstanding','proximity','jealousy', NULL)),
  ADD COLUMN IF NOT EXISTS heat_level TEXT CHECK (heat_level IN ('sweet','sensual','open door','closed door', NULL)),
  ADD COLUMN IF NOT EXISTS romantic_arc_position TEXT;

ALTER TABLE {{SCHEMA}}.relationships
  ADD COLUMN IF NOT EXISTS romantic_tension INTEGER DEFAULT 0 CHECK (romantic_tension BETWEEN 0 AND 10),
  ADD COLUMN IF NOT EXISTS first_meeting_chapter INTEGER,
  ADD COLUMN IF NOT EXISTS turning_point_chapter INTEGER;

-- Example rows showing new columns (safe to delete)
-- INSERT INTO {{SCHEMA}}.characters (name, role, love_language, attachment_style, romantic_arc, is_minor)
-- VALUES ('[EXAMPLE] Romance Character', 'protagonist', 'acts of service', 'anxious', 'guarded -> vulnerable -> committed', FALSE);
