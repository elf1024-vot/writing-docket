---
name: novel-add-group
description: Create group rows from writer-supplied key and link fields. Usage: /novel-add-group
---

You are scaffolding group ROWS — the structure and links, not the prose. The writer
supplies the key field and any links (the leader is a foreign key to a character); you
validate the links exist and build correctly-keyed rows. You do NOT author purpose or
membership prose — leave those empty for the writer.

A group is any grouping: gang, guild, family, faction, crew, coven, house, order, agency.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll set up entries for your groups, the gangs, guilds,
families, or factions in your story, so they're ready to flesh out later." Before you run
any commands, reassure the writer in plain words: Claude Code may pop up approval boxes
asking "Do you want to proceed?" (sometimes with technical wording like "manual approval
required"); that's normal and safe, so choose Yes (or "Yes, don't ask again" if offered),
and it never means something went wrong. Narrate the steps in everyday language and finish
with a friendly, plain-English summary instead of raw command output.

## Step 1 — Load project context

Read `project.json` (current dir or search upward). Capture `project_slug` (= schema),
`project_path`, `ui_port`. If not found, ask for the project name and locate its folder.

## Step 2 — Ask the writer for natural values

The schema's key (`group_id`) and the leader→character link are baked in — you generate
the id and resolve the leader, the writer just names things. Collect:

"List the groups to add — one per line, by name. Optionally add a type and who leads it,
e.g.:
`The Ironwright Guild | guild | led by Lady Vex`
A bare name is fine. A leader has to be a character that already exists — if they're not
in the cast yet, leave them off and add them first with /novel-add-characters."

For each, derive `group_id` automatically from the name (lowercase, spaces→hyphens, drop
punctuation; e.g. "The Ironwright Guild" → `ironwright-guild`). The writer supplies the
leader's name in plain language; you resolve it to the FK in the next step.

## Step 3 — Validate the foreign keys

Query existing character names so you can check every supplied leader:
`docker exec <slug>-postgres psql -U docket_master -d <schema> -t -c "SELECT name FROM <schema>.characters ORDER BY name;"`

For each group: if a `leader` was given and it does NOT match an existing character name
exactly, do NOT insert that leader (the FK would reject the row). Drop it to NULL and list
it for the writer with a note to add the character first or fix the spelling.

## Step 4 — Build and confirm the rows

Assemble each row:
- `group_id` (auto-derived PK), `display_name` (the name given), `type` (if given),
  `leader` (only if it resolved to an existing character).
- `territory_or_base`, `purpose`, `membership_notes`, `notes` → left NULL for the writer.

Show the exact rows and any dropped leaders, and get a yes before writing.

## Step 5 — Insert safely

1. Write SQL to `{{project_path}}\postgres\_add.sql`, doubling single quotes. Include
   `leader` in the column list ONLY when it passed validation:
   ```sql
   INSERT INTO <schema>.groups (group_id, display_name, type, leader)
   VALUES ('ironwright-guild', 'The Ironwright Guild', 'guild', 'Lady Vex')
   ON CONFLICT (group_id) DO NOTHING;
   ```
2. `docker cp "<project_path>\postgres\_add.sql" <slug>-postgres:/tmp/_add.sql`
3. `docker exec <slug>-postgres psql -U docket_master -d <schema> -f /tmp/_add.sql`
4. Delete the temp file.

## Step 6 — Report

How many added vs. skipped, any leaders dropped (and why), plus:
"Group rows exist. To link members, add character↔group rows in the character_groups
table (both the character and the group must exist first)."
