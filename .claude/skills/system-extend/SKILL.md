---
name: system-extend
description: Add a genre extension to an existing writing-docket project. Usage: /system-extend [extension-name]
---

You are adding a genre extension to an existing writing-docket project.

## Available extensions

- romance — love_language, attachment_style, emotional_wall, romantic_arc columns; heat_level; emotion-focused canary overrides
- sci-fi — technology_level, faction, augmentation columns; worldbuilding notes; elevated FK grade threshold
- fantasy-magic — magic_system, power_level, cost columns; fk_grade and complex_paragraph overrides
- fantasy-worldbuilding — world_building notes, faction loyalties, prophecy references
- mystery — alibi, motive, opportunity columns on characters; clue tracking on chapters
- thriller — threat_level, stakes columns; tighter passive voice and adverb thresholds
- historical — era, social_class, historical_role columns; elevated FK grade

## Step 1 — Load project context

Read project.json from the current directory. Load: project_slug, schema, project_path, installed_extensions.

## Step 2 — Identify extension

If an extension name was passed as argument, use it. Otherwise list available extensions and ask which to install.

Check installed_extensions — if already present, print: "Extension [name] is already installed." and stop.

## Step 3 — Locate extension files

The extension SQL and canary JSON are in the skills repo. Find the repo root by locating this skill file and going up to the repo root.

Read: `extensions/{{EXTENSION}}.sql` and `extensions/{{EXTENSION}}.canary.json` (if exists).

## Step 4 — Run extension SQL

Substitute {{SCHEMA}} with the project schema name throughout the SQL.

Check that Docker is running: `docker compose ps` from the project directory.

Run the SQL: pipe it into the postgres container via docker exec.

Each ALTER TABLE uses IF NOT EXISTS — safe to run even if partially applied.

## Step 5 — Merge canary thresholds

If a .canary.json exists for this extension, merge its values into project.json canary_thresholds. Extension values override defaults.

## Step 6 — Update Standards.md

Append any extension-specific gate notes to prompts/Standards.md. For example, romance adds:
```
## Romance Extension Gates

R1 — Emotional tension is shown through behavior and internal reaction, not told.
R2 — Heat level is consistent with the scene's position in the romantic arc.
R3 — Relationship progression is earned, not jumped.
```

## Step 7 — Add to installed_extensions

Add the extension name to project.json installed_extensions array. Write project.json.

## Step 8 — Seed example rows

Insert [EXAMPLE] rows showing the new columns in the character and chapter tables.

## Step 9 — Confirm

Print: "Extension [name] installed. New columns are visible in the character and chapter editors."
