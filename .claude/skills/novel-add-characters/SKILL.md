---
name: novel-add-characters
description: Create character rows from writer-supplied key fields. Usage: /novel-add-characters
---

You are scaffolding character ROWS — the structure, not the prose. The writer supplies the
fields needed to form valid entries; you build correctly-keyed rows and insert them. You do
NOT author background, arc, dialogue, or any descriptive content — that is the writer's
work (done later in the editors or a CoWork authoring session). Leave those fields empty.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll set up entries for your characters so they're ready to
flesh out later; I won't write anything about them, just create the slots." Before you run
any commands, reassure the writer in plain words: Claude Code may pop up approval boxes
asking "Do you want to proceed?" (sometimes with technical wording like "manual approval
required"); that's normal and safe, so choose Yes (or "Yes, don't ask again" if offered),
and it never means something went wrong. Narrate the steps in everyday language and finish
with a friendly, plain-English summary instead of raw command output.

## Step 1 — Load project context

Read `project.json` (current dir or search upward). Capture `project_slug` (= schema),
`project_path`, `ui_port`. If not found, ask for the project name and locate its folder.

## Step 2 — Ask the writer for natural values

The schema already defines the keys and links — you apply them, the writer never has to
think about them. For characters the primary key IS the name, so just collect names:

"List the characters to add — one per line. Optionally add a role after a `|`
(protagonist / antagonist / ally / minor / narrator), e.g.:
`Lady Vex | protagonist`
`The Archivist | antagonist`
A bare name is fine."

Do not invent names or roles. Use only what the writer gives.

## Step 3 — Build and confirm the rows

For each line, assemble a row using ONLY the supplied fields:
- `name` (required PK), `display_name` (only if given), `role` (only if given).
- Everything else (background, arc, dialogue_prompt, image_prompt, age_or_era, notes) is
  left NULL for the writer to author later. Do not set `is_minor` (defaults FALSE; DB
  forbids TRUE).

Show the writer the exact rows you will insert and get a yes before writing.

## Step 4 — Insert safely

1. Write SQL to `{{project_path}}\postgres\_add.sql`, doubling single quotes in any text
   value. Include only the columns the writer supplied:
   ```sql
   INSERT INTO <schema>.characters (name, display_name, role)
   VALUES ('Lady Vex', 'Lady Vex', 'protagonist')
   ON CONFLICT (name) DO NOTHING;
   ```
   (Omit `display_name`/`role` from the column list for rows where they weren't given.)
2. `docker cp "<project_path>\postgres\_add.sql" <slug>-postgres:/tmp/_add.sql`
3. `docker exec <slug>-postgres psql -U docket_master -d <schema> -f /tmp/_add.sql`
4. Delete the temp file.

`ON CONFLICT (name) DO NOTHING` makes re-running safe.

## Step 5 — Report

How many added vs. skipped (already existed), plus:
"The character rows exist with names and roles set. Flesh out their backgrounds, arcs,
and voices in the Character editor (http://localhost:<ui_port>/character-editor.html) or a
writing session — that authoring is intentionally left to you."
