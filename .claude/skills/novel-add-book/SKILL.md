---
name: novel-add-book
description: Register a book and scaffold blank chapter rows from writer-supplied keys. Usage: /novel-add-book
---

You are scaffolding the chapter STRUCTURE for a book — the keyed rows and the on-disk
folders, not the prose. The writer supplies the keys (book name, chapter count, and
optionally which POV character / location each chapter links to); you validate any links
and build correctly-keyed rows. You do NOT author summaries or chapter content — the rows
are left blank for the writer to fill.

## Step 1 — Load project context

Read `project.json` (current dir or search upward). Capture `project_slug` (= schema),
`project_path`, `ui_port`, `series`, `series_name`. If not found, ask for the project name
and locate its folder.

## Step 2 — Ask the writer for natural values

The schema's keys (`book`, `chapter`, `part`) and the POV→character / location→location
links are baked in — you assign chapter numbers and resolve the links, the writer just
gives names. Ask:

1. "What is the **book name**?"
2. "How many **chapters** do you want to scaffold? (You can add more anytime with the
   chapter editor's + New Chapter button.)"
3. "Want to set a POV character or location for any chapters now? Tell me in plain
   language (e.g. 'Ch 1 is Lady Vex at The Workshop') — they have to already exist.
   Otherwise I'll leave them blank."

You assign `chapter` numbers (1..N) and `part` (1) yourself — those are the keys, baked
into the schema. The writer supplies POV/location by name; you resolve them to FKs next.
Do not invent a book name, POV, or location.

## Step 3 — Validate any foreign keys

If the writer named POV characters or locations, resolve each plain name to its key and
verify it exists:
- `docker exec <slug>-postgres psql -U docket_master -d <schema> -t -c "SELECT name FROM <schema>.characters;"`
- `docker exec <slug>-postgres psql -U docket_master -d <schema> -t -c "SELECT location_id, display_name FROM <schema>.locations;"`

`pov_char` stores the character `name` directly. `location` stores the `location_id` — so
match the writer's spoken location name against `display_name` and use the matching
`location_id`. Drop any assignment that doesn't resolve to an existing row, and list it for
the writer.

## Step 4 — Create the chapter folders on disk

Under `{{project_path}}` (or the book's subfolder in a series layout), create
`Chapters\Chapter NN\Chapter-NN.md` for each chapter N (two-digit zero-padded), each
containing only minimal key frontmatter — no prose:
```markdown
---
book: <book name>
chapter: N
part: 1
---
```

## Step 5 — Build the blank chapter rows

Each row carries only keys and structural defaults; descriptive fields stay blank:
- `book` (key) = the book name, `chapter` (key) = 1..N, `part` (key) = 1
- `status` = `'concept'`, `priority` = `'MED'`
- `pov_char` / `location` = only the validated assignments, else NULL
- `summary`, `cast`, `qr` = NULL; `word_count` defaults 0

Insert safely:
1. Write SQL to `{{project_path}}\postgres\_add.sql`, doubling single quotes in the book
   name. Include `pov_char`/`location` only where validated:
   ```sql
   INSERT INTO <schema>.chapters (book, chapter, part, status, priority)
   VALUES ('The Iron Compass', 1, 1, 'concept', 'MED')
   ON CONFLICT (book, chapter, part) DO NOTHING;
   ```
2. `docker cp "<project_path>\postgres\_add.sql" <slug>-postgres:/tmp/_add.sql`
3. `docker exec <slug>-postgres psql -U docket_master -d <schema> -f /tmp/_add.sql`
4. Delete the temp file.

`ON CONFLICT (book, chapter, part) DO NOTHING` keeps re-running safe.

## Step 6 — Report

Book name, chapters created vs. already existed, any dropped POV/location assignments,
where the Chapter folders live, plus:
"The chapter skeleton exists. Set POV, location, and summaries in the Chapter editor or
the Tracker (http://localhost:<ui_port>/chapter-tracker.html). When you're ready to draft,
that authoring happens in a writing session — run /novel-plan then /novel-write."
