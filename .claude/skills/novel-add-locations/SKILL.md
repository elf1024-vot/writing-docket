---
name: novel-add-locations
description: Create location rows from writer-supplied key fields. Usage: /novel-add-locations
---

You are scaffolding location ROWS — the structure, not the prose. The writer supplies the
key fields; you build correctly-keyed rows and insert them. You do NOT author the
exterior/interior/sensory descriptions — that is the writer's work, done later. Leave
those fields empty.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll set up entries for your locations so they're ready to
describe later; I won't write the descriptions, just create the slots." Before you run any
commands, reassure the writer in plain words: Claude Code may pop up approval boxes asking
"Do you want to proceed?" (sometimes with technical wording like "manual approval
required"); that's normal and safe, so choose Yes (or "Yes, don't ask again" if offered),
and it never means something went wrong. Narrate the steps in everyday language and finish
with a friendly, plain-English summary instead of raw command output.

## Step 1 — Load project context

Read `project.json` (current dir or search upward). Capture `project_slug` (= schema),
`project_path`, `ui_port`. If not found, ask for the project name and locate its folder.

## Step 2 — Ask the writer for natural values

The schema's key (`location_id`) and links are baked in — you generate the id, the writer
just names the place. Collect names:

"List the locations to add — one per line, by name. Optionally add a type after a `|`
(interior / exterior / district / building / landmark / region) and a region, e.g.:
`The Workshop | interior | Lower City`
A bare name is fine."

For each, derive `location_id` automatically from the name (lowercase, spaces→hyphens,
drop punctuation; e.g. "The Workshop" → `the-workshop`). The writer does not supply ids —
you generate them from the relationship the schema already defines. Use only the
descriptive values the writer gave; do not invent descriptions.

## Step 3 — Build and confirm the rows

Assemble each row:
- `location_id` (auto-derived PK), `display_name` (the name given), `type`/`region` (if given).
- `exterior_desc`, `interior_desc`, `sensory`, `books_present`, `notes` → left NULL for
  the writer to author later.

Show the exact rows (with the generated id shown for each) and get a yes before writing.

## Step 4 — Insert safely

1. Write SQL to `{{project_path}}\postgres\_add.sql`, doubling single quotes. Include only
   supplied columns:
   ```sql
   INSERT INTO <schema>.locations (location_id, display_name, type, region)
   VALUES ('the-workshop', 'The Workshop', 'interior', 'Lower City')
   ON CONFLICT (location_id) DO NOTHING;
   ```
2. `docker cp "<project_path>\postgres\_add.sql" <slug>-postgres:/tmp/_add.sql`
3. `docker exec <slug>-postgres psql -U docket_master -d <schema> -f /tmp/_add.sql`
4. Delete the temp file.

## Step 5 — Report

How many added vs. skipped, plus:
"Location rows exist with ids and names. Write the exterior, interior, and sensory detail
in the Location editor (http://localhost:<ui_port>/location-editor.html) when you're ready."
