---
name: novel-import
description: Import filled-in intake spreadsheets (CSV) into the project database. Usage: /novel-import [file]
---

You are importing the writer's filled-in intake spreadsheets and turning each row into a
valid, correctly-linked database entry. The writer entered natural values (names, and
optionally descriptions they chose to write); the schema's keys and links are baked in, so
you generate the ids and resolve the links. You do NOT add or embellish content — you
import exactly what the writer wrote, leaving blank what they left blank.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll bring in the characters, places, groups, and chapters you
filled into the spreadsheets, exactly as you wrote them." Before you run any commands,
reassure the writer in plain words: Claude Code may pop up approval boxes asking "Do you
want to proceed?" (sometimes with technical wording like "manual approval required");
that's normal and safe, so choose Yes (or "Yes, don't ask again" if offered), and it never
means something went wrong. Narrate the steps in everyday language and give the preview and
final results as a friendly, plain-English summary rather than raw command output.

## Step 1 — Load project context

Read `project.json` (current dir or search upward). Capture `project_slug` (= schema),
`project_path`, `ui_port`. If not found, ask for the project name and locate its folder.

## Step 2 — Find the CSVs

Look in `{{project_path}}\intake\` for `characters.csv`, `locations.csv`, `groups.csv`,
`chapters.csv`. If a specific file was passed as an argument, import only that one.

Process them in dependency order so links resolve: **characters → locations → groups →
chapters.** Skip any file that's missing or unchanged from its example-only state.

For each file: read it, parse the header row to map columns, and **ignore any row whose
first cell starts with `[EXAMPLE]`** (those are the template guides).

## Step 3 — Build rows, generating keys and resolving links

Apply the schema's baked-in relationships — the writer never supplied a key:

- **characters** — `name` is the PK (required; skip rows with no name). Take role,
  display_name, and any descriptive columns the writer filled. Never set `is_minor`.
- **locations** — derive `location_id` from `display_name` (lowercase, spaces→hyphens,
  drop punctuation). Take type/region and any descriptions given.
- **groups** — derive `group_id` from `display_name`. If `leader` is filled, resolve it
  against existing character names (query the DB); if it doesn't match exactly, drop the
  leader to NULL and flag the row. Take the other columns as given.
- **chapters** — keys are `book`, `chapter`, `part` (default part 1). Resolve `pov_char`
  against character names and `location` against location `display_name` → `location_id`;
  drop and flag any that don't resolve. Default `status` to `concept`, `priority` to `MED`
  if blank.

Query existing rows for link resolution:
`docker exec <slug>-postgres psql -U docket_master -d <schema> -t -c "SELECT name FROM <schema>.characters;"`
`docker exec <slug>-postgres psql -U docket_master -d <schema> -t -c "SELECT location_id, display_name FROM <schema>.locations;"`
(Within a single import, a leader/POV may refer to a character being imported in this same
run — resolve against both the DB and the rows you're about to insert.)

## Step 4 — Preview and confirm

Show the writer a per-file summary table of the rows you'll insert, plus a clear list of
anything you dropped (a leader/POV/location that didn't resolve) with the reason. Get a
yes before writing anything.

## Step 5 — Insert safely

For each table, write the INSERTs to `{{project_path}}\postgres\_import.sql`, doubling
single quotes in every text value, including only the columns that have a value. Use the
same `ON CONFLICT (<pk>) DO NOTHING` clause per table so re-importing is safe. Then:

1. `docker cp "<project_path>\postgres\_import.sql" <slug>-postgres:/tmp/_import.sql`
2. `docker exec <slug>-postgres psql -U docket_master -d <schema> -f /tmp/_import.sql`
3. Delete the temp file.

## Step 6 — Report

Per file: rows added vs. skipped (already existed or example), and anything dropped for an
unresolved link. Close with:
"Imported. Open the editors (http://localhost:<ui_port>/) to review, fill in anything you
left blank, and start writing."
