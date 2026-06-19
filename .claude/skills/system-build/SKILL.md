---
name: system-build
description: Build a complete writing system from a plan document. Usage: /system-build [docket-plan.md]
---

You are setting up a complete local writing infrastructure. Follow each phase in order. Do not skip phases. Do not summarize or abbreviate — execute every step.

**Keep the writer company the whole way.** Assume the person watching is a novelist, not a
developer, and that any silence longer than a few seconds reads as "it's frozen / did I
break it?" So:
- Before any step that can pause (downloads, the database initializing, the model pull,
  health waits), say in one plain sentence what's happening and that a pause is normal.
- During long waits, print a short progress line every 30-60 seconds — reassurance, not
  jargon. Never go silent through a multi-minute download.
- Speak plain English, not command names or error codes. ("Setting up the database" not
  "running init.sql".) Save the technical detail for when something actually fails.
- End each phase with a one-line "done, moving on" so progress feels continuous.
The goal: the writer always knows it's working and never wonders whether to close the window.

---

## BEFORE ANYTHING ELSE — Print this banner

```
╔══════════════════════════════════════════════════════════════════╗
║  ⚠  DO NOT CLOSE THIS WINDOW                                     ║
║                                                                  ║
║  Setup takes 5-10 minutes on first run (Docker image pulls).    ║
║  Closing Claude Code mid-build will leave your project in a     ║
║  partial state. If something goes wrong, run /system-restore.   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Phase 0 — Pre-flight Checks

Run each check and print a status table. Hard-stop (abort with clear error) if Windows build < 19041 or Docker not running after install attempt.

Run these checks via Bash tool:

1. **Windows build**: `powershell -c "(Get-WmiObject Win32_OperatingSystem).BuildNumber"` — must be ≥ 19041
2. **WSL2**: `wsl --status` — look for "Default Version: 2"
3. **Docker running**: `docker info` — must succeed
4. **Docker Compose v2**: `docker compose version` — must say "v2"
5. **Python 3.9+**: `python --version` — must be ≥ 3.9
6. **Git**: `git --version` — warn if missing, offer `winget install --id Git.Git -e` but do not block

Print results as a table:
```
Pre-flight check results:
┌─────────────────────┬────────┬────────────────────────────────┐
│ Check               │ Status │ Detail                         │
├─────────────────────┼────────┼────────────────────────────────┤
│ Windows build       │  PASS  │ 26200                          │
│ WSL2                │  PASS  │ Default Version: 2             │
│ Docker running      │  PASS  │ Docker Engine 24.0.7           │
│ Docker Compose v2   │  PASS  │ v2.23.3                        │
│ Python 3.9+         │  PASS  │ 3.11.4                         │
│ Git                 │  WARN  │ Not found (optional)           │
└─────────────────────┴────────┴────────────────────────────────┘
```

If Docker is not running, print: "Docker Desktop is not running. Please start Docker Desktop and press Enter to retry." Then re-check. Hard-stop if still fails.

**Port check**: Run `netstat -ano | findstr :8090` — if port 8090 is in use, note the conflict and plan to use 8091 (increment until free).

**Search / Ollama note (not a hard-stop)**: This build includes built-in search. The semantic half uses a local `ollama` container that needs a one-time internet pull of the `nomic-embed-text` model (~300MB) and roughly 1-2GB RAM to run. None of this blocks the build: if the machine is offline or RAM-constrained, full-text search still works out of the box and semantic search can be enabled later (pull the model, then run `python scripts/embed.py --full`). Mention this to the writer in pre-flight; do not abort on it.

---

## Phase 1 — Parse plan document (if provided)

If an argument was given (e.g. `/system-build docket-plan.md`), read that file now using the Read tool.

Extract from the plan document (if present):
- Project name (override intake if found)
- Author name
- Genre
- Character list (name, role, age_or_era, brief_bio)
- Custom writing gates (any "G9:", "G10:" style gates or custom rules listed)
- TTS setting (yes/no, provider if named)
- Synthesis tracking setting (yes/no)
- Canary overrides (any specific metric thresholds)
- Series info (standalone vs series, series name)

Store all extracted values. They supplement and override intake answers.

---

## Phase 2 — Intake conversation

Ask each question in sequence. Wait for each answer before continuing. Do not batch questions.

**Q1 — Project name**
"What is the name of your project? (This becomes your folder name and database schema.)"
- If already extracted from plan doc, confirm: "Your plan doc names this '[NAME]'. Press Enter to confirm or type a different name."
- Slugify: lowercase, replace spaces/hyphens/special chars with underscores. Example: "The Iron Compass" → "the_iron_compass"

**Q2 — Author name**
"What is your name (author name for prompts and reports)?"

**Q3 — Genre**
"What is the genre? Examples: Fantasy, Romance, Thriller, Sci-Fi, Mystery, Historical, Literary Fiction, Steampunk"
- After they answer, check the genre against this mapping and offer extensions:
  - Romance → romance extension available
  - Thriller, Mystery → thriller and/or mystery extensions available
  - Fantasy, Epic Fantasy, Steampunk → fantasy-magic and/or fantasy-worldbuilding extensions available
  - Sci-Fi, Science Fiction → sci-fi extension available
  - Historical, Historical Fiction → historical extension available
- Print: "Based on your genre, these extensions are available: [list]. Each adds genre-specific database columns and adjusts quality thresholds. Install them? [list with yes/no for each, default yes]"

**Q4 — Standalone or series**
"Is this a standalone novel or part of a series?"
- If series: "What is the series name?" and "What is the name of this book (volume 1)?"

**Q5 — Workspace folder**
"Where should the project folder be created? (Default: C:\Users\[USERNAME]\ClaudeCoWork — press Enter to accept)"
- Resolve %USERPROFILE% dynamically if default accepted

**Q6 — Backup time**
"What time should the daily backup run? (Default: 23:00 — press Enter to accept, or enter a time like 02:30)"

---

## Phase 3 — Generate project.json

Assemble project.json from all gathered data:

```json
{
  "project_name": "<full name>",
  "project_slug": "<slug>",
  "author": "<author>",
  "genre": "<genre>",
  "workspace_path": "<workspace>",
  "project_path": "<workspace>\\<project_name>",
  "schema": "<slug>",
  "ui_port": 8090,
  "series": false,
  "series_name": null,
  "book_name": "<book name>",
  "installed_extensions": [],
  "synthesis_tracking": false,
  "tts_enabled": false,
  "tts_provider": null,
  "scheduled_backup_time": "23:00",
  "schema_version": "1.0",
  "built_on": "<today's date>",
  "canary_thresholds": {
    "passive_voice": 12,
    "emotion_tells": 10,
    "weak_adverbs_per_1k": 6.0,
    "sentence_variety_std_dev": 5.5,
    "complex_paragraphs": 8,
    "readability_fk_grade": 8,
    "glue_index": 38
  },
  "custom_gates": [],
  "accent_color": "<derived from project_name — see below>",
  "search": {
    "embedding_model": "nomic-embed-text",
    "embedding_dims": 768,
    "ollama_url": "http://127.0.0.1:11434"
  }
}
```

The `search` block is read by `scripts/embed.py` (embedding model, dims, Ollama URL). Keep `embedding_model` and `embedding_dims` consistent with the `vector(768)` column in `init.sql` — if you ever change the model, change the dims everywhere (init.sql, embed.py, mcp_relay, search.html, project.json).

**Set canary_thresholds from the writer's genre.** The thresholds are genre-driven, not
fixed. Resolve them in this precedence order (each later step overrides the earlier):

1. Start from the `generic` profile in `templates/canary-genres.json`.
2. **Apply the genre profile.** Take the genre the writer gave in Q3, lowercase it, and
   match it against `templates/canary-genres.json`: first the top-level keys
   (`romance`, `thriller`, `literary`, `mystery`, `scifi`, `fantasy`, `historical`,
   `horror`), then the `_synonyms` map (e.g. "Science Fiction" → `scifi`, "Steampunk" →
   `fantasy`, "Gothic" → `horror`). If the genre matches nothing, stay on `generic` and
   tell the writer "No genre profile for '[genre]' — using generic thresholds." For a
   mixed genre ("Romantic Mystery"), match each named genre and take, per metric, the
   stricter value (lower for all metrics except sentence_variety_std_dev, where higher is
   stricter).
3. **Merge extension overrides.** For each installed extension that ships a `.canary.json`,
   merge its keys on top.
4. **Merge plan-doc overrides.** Any `## Canary Overrides` the writer wrote in the plan doc
   win over everything.

Write the resolved values into project.json `canary_thresholds`. These fill the
`{{PASSIVE_VOICE}}` etc. placeholders in Standards.md and are read at scoring time by
`scripts/canary.py`.

Add synthesis_tracking: true if plan doc specified it. Add tts_enabled: true and tts_provider if plan doc specified TTS.

**Derive accent_color deterministically from project_name** so each project gets its own consistent color without the writer choosing one. Compute a hue from the name (e.g. sum of character codes mod 360) and set accent_color to a rich mid-saturation dark-theme-friendly color at that hue, e.g. `hsl(H, 55%, 58%)`. Store the resolved hex (or the `hsl()` string) in project.json as `accent_color`; it fills `{{ACCENT_COLOR}}` in `docket.css`. Do NOT hardcode a fixed default — every project derives its own.

Example: `"The Iron Compass"` → sum of character codes = 1487 → `1487 % 360 = 47` → `accent_color = "hsl(47, 55%, 58%)"` (a warm amber/gold). A different name yields a different hue, so each project's site reads as its own.

`{{ACCENT_COLOR}}` → resolved accent_color from project.json (add this to the Phase 4 variable mapping).

---

## Phase 4 — Generate passwords

Run this Python snippet via Bash tool to generate all passwords and the JWT secret:

```python
import secrets
pw_master = secrets.token_urlsafe(16)
pw_editor = secrets.token_urlsafe(16)
pw_claude = secrets.token_urlsafe(16)
jwt = secrets.token_urlsafe(32)
print(f"MASTER={pw_master}")
print(f"EDITOR={pw_editor}")
print(f"CLAUDE={pw_claude}")
print(f"JWT={jwt}")
```

Capture the output. Use these for all credential placeholders.

Variable mapping:
- `{{PROJECT_NAME}}` → project_name
- `{{SCHEMA}}` → project_slug (schema name)
- `{{EDITOR_USER}}` → `docket_editor`
- `{{EDITOR_PASSWORD}}` → generated editor password
- `{{CLAUDE_USER}}` → `docket_claude`
- `{{CLAUDE_PASSWORD}}` → generated claude password
- `{{MASTER_USER}}` → `docket_master`
- `{{MASTER_PASSWORD}}` → generated master password
- `{{POSTGREST_JWT_SECRET}}` → generated JWT secret
- `{{UI_PORT}}` → resolved port (8090 or next available)
- `{{PROJECT_PATH}}` → full project path
- `{{PROJECT_SLUG}}` → project_slug
- `{{AUTHOR}}` → author name
- `{{GENRE}}` → genre
- `{{BUILD_DATE}}` → today's date
- `{{BOOK_NAME}}` → book_name from project.json (for standalone: same as project_name; for series: first book name)
- `{{ACCENT_COLOR}}` → resolved accent_color from project.json (name-derived, per Phase 3)
- `{{BACKUP_TIME}}` → scheduled_backup_time from project.json (from intake Q6; default "23:00")
- `{{TTS_ENABLED}}` → tts_enabled from project.json (true/false; gates the TTS blocks in character-editor.html and whether prompts/TTS-Prep.md is written)
- `{{EXTENSION}}` → loop-local: the current extension name while iterating in Phases 6/8
- `{{SYNTHESIS_WHITELIST}}` → replacement for the marker in mcp-server/mcp_relay.py (see Phase 5 synthesis note): empty when synthesis off; the three synthesis whitelist lines when on

**Canary threshold key → Standards.md placeholder mapping.** The project.json
`canary_thresholds` keys differ from the Standards.md placeholders — map them explicitly
when writing `prompts/Standards.md`:
- `passive_voice` → `{{PASSIVE_VOICE}}`
- `emotion_tells` → `{{EMOTION_TELLS}}`
- `weak_adverbs_per_1k` → `{{WEAK_ADVERBS}}`
- `sentence_variety_std_dev` → `{{SENTENCE_VARIETY}}`
- `complex_paragraphs` → `{{COMPLEX_PARAGRAPHS}}`
- `readability_fk_grade` → `{{FK_GRADE}}`
- `glue_index` → `{{GLUE_INDEX}}`

---

## Phase 5 — Write all project files

Create the project directory: `{{PROJECT_PATH}}`

Create all subdirectories: postgres/, postgrest/, nginx/html/, mcp-server/, scripts/, bat-files/, prompts/, Chapters/, Notes/, qr/, backups/

### Preferred path — run the build script (`scripts/build_docket.py` in the repo root)

If `scripts/build_docket.py` exists in the skills repo, **use it as the canonical file
writer** instead of hand-writing each file. It is the single source of truth for
placeholder substitution and handles the things that are easy to get wrong by hand:
per-file backslash escaping (JSON `\\` vs literal paths), the synthesis SQL + whitelist
injection, TTS block include/strip, and the canary-key → Standards-placeholder mapping.

Contract:
1. First write `project.json` (from Phase 3) and `.env` (the block below) into
   `{{PROJECT_PATH}}` — these are the script's inputs (config + resolved secrets).
2. Run it from the repo root:
   ```
   python scripts/build_docket.py --project-path "{{PROJECT_PATH}}"
   ```
   The script reads `{{PROJECT_PATH}}/project.json` and `{{PROJECT_PATH}}/.env`, reads the
   templates under `templates/`, substitutes every placeholder, and writes all the files in
   the list below into the project directory.
3. If the script reports success, skip the manual per-file writing and continue to Phase 6.
4. If the script is **absent or errors**, fall back to writing each file by hand per the
   list below (Write tool), filling all {{PLACEHOLDER}} values yourself. The manual path and
   the script must produce identical output — keep them in sync.

### Manual path (fallback)

Write each file below. Read the corresponding template from the skills repo (the directory where this skill file lives, go up to the repo root, then into templates/). Fill in all {{PLACEHOLDER}} values.

**File list — write every one of these:**

1. `project.json` — the assembled project.json from Phase 3
2. `.env` — all credentials and config:
   ```
   POSTGRES_DB={{SCHEMA}}
   POSTGRES_USER={{MASTER_USER}}
   POSTGRES_PASSWORD={{MASTER_PASSWORD}}
   EDITOR_USER={{EDITOR_USER}}
   EDITOR_PASSWORD={{EDITOR_PASSWORD}}
   CLAUDE_USER={{CLAUDE_USER}}
   CLAUDE_PASSWORD={{CLAUDE_PASSWORD}}
   JWT_SECRET={{POSTGREST_JWT_SECRET}}
   UI_PORT={{UI_PORT}}
   PROJECT_SLUG={{PROJECT_SLUG}}
   DOCKET_ENV={{PROJECT_PATH}}\.env
   OLLAMA_URL=http://127.0.0.1:11434
   EMBED_MODEL=nomic-embed-text
   ```
   (`OLLAMA_URL` / `EMBED_MODEL` are read by `mcp-server/mcp_relay.py` for the `pg_search` tool; `embed.py` reads the same values from `project.json`'s `search` block.)
3. `.gitignore`:
   ```
   .env
   backups/
   Chapters/
   Notes/
   qr/
   postgres/data/
   __pycache__/
   *.pyc
   ```
4. `.env.example` — same as .env but with placeholder values, safe to commit
5. `docker-compose.yml` — from templates/docker-compose.yml.tmpl
6. `postgres/init.sql` — from templates/init.sql.tmpl
7. `postgrest/postgrest.conf` — from templates/postgrest.conf.tmpl
8. `nginx/nginx.conf` — from templates/nginx.conf.tmpl
8b. `nginx/html/docket.css` — from templates/nginx/html/docket.css (copy + placeholder substitution). Shared design system stylesheet (all HTML pages link it). Keep `--accent: {{ACCENT_COLOR}}` as the themable hook in `:root` — do NOT hardcode a color; the build fills `{{ACCENT_COLOR}}` with the name-derived accent from project.json.
9. `nginx/html/index.html` — from templates/nginx/html/index.html (copy + placeholder substitution). Nav hub with card links to all editors. The brand / header text is purely `{{PROJECT_NAME}}` + `{{AUTHOR}}` + `{{GENRE}}` — nothing genre-specific baked in. The whole site must read as that writer's own project.
10. `nginx/html/character-editor.html` — from templates/nginx/html/character-editor.html (copy + placeholder substitution). Full CRUD via PostgREST. Does NOT render an `is_minor` toggle (DB enforces is_minor=FALSE). The TTS fields live between the `<!-- TTS_BLOCK_START -->`/`<!-- TTS_BLOCK_END -->` markers in the form and `// TTS_PAYLOAD_START`/`// TTS_PAYLOAD_END` markers in the JS payload — INCLUDE both blocks when `{{TTS_ENABLED}}` is true, STRIP both blocks (and the marker comments) when false.
11. `nginx/html/chapter-editor.html` — from templates/nginx/html/chapter-editor.html (copy + placeholder substitution). CRUD on chapters; composite PK (book,chapter,part) — PATCH filters on all three. Has "+ New Chapter" and "+ Add Part".
12. `nginx/html/location-editor.html` — from templates/nginx/html/location-editor.html (copy + placeholder substitution).
13. `nginx/html/dashboard.html` — from templates/nginx/html/dashboard.html (copy + placeholder substitution). Read-only live dashboard; CSS-bar chart for word count (no external Chart.js — fully offline).
14. `nginx/html/notes-editor.html` — from templates/nginx/html/notes-editor.html (copy + placeholder substitution).
15. `nginx/html/chapter-tracker.html` — from templates/nginx/html/chapter-tracker.html (copy + placeholder substitution).
15b. `nginx/html/search.html` — from templates/nginx/html/search.html (copy + placeholder substitution). Built-in search page (full-text + semantic). Calls PostgREST RPC at `/api/rpc/search_fts` and `/api/rpc/search_semantic`, and Ollama at `/ollama/api/embeddings`; falls back to text search when Ollama is down.
16. `nginx/html/faq.html` — from templates/nginx/html/faq.html (copy + placeholder substitution).
17. `nginx/html/readme.html` — from templates/nginx/html/readme.html (copy + placeholder substitution).
18. `mcp-server/mcp_relay.py` — from templates/mcp_relay.py.tmpl
19. `scripts/word_count.py` — from templates/word_count.py
19b. `scripts/canary.py` — from templates/canary.py (deterministic prose-metric scanner the QR workflow runs; no placeholder substitution)
19c. `scripts/embed.py` — from templates/embed.py (builds the search_index: full-text rows + Ollama embeddings; no placeholder substitution — reads project.json + .env at runtime)
20. `scripts/migrate.py` — from templates/migrate.py
21. `bat-files/backup.bat` — from templates/backup.bat.tmpl
22. `bat-files/restore.bat` — from templates/restore.bat.tmpl
22b. `intake/characters.csv`, `intake/locations.csv`, `intake/groups.csv`, `intake/chapters.csv`, `intake/README.txt` — copy verbatim from templates/intake/ (no placeholder substitution; the writer fills these in a spreadsheet, then runs /novel-import).
23. `prompts/Init.md` — from templates/prompts/Init.md.tmpl
24. `prompts/Writing-Prompt.md` — from templates/prompts/Writing-Prompt.md.tmpl
25. `prompts/Character-Agent.md` — from templates/prompts/Character-Agent.md.tmpl
26. `prompts/Planning.md` — from templates/prompts/Planning.md.tmpl
27. `prompts/QR.md` — from templates/prompts/QR.md.tmpl
28. `prompts/Polish.md` — from templates/prompts/Polish.md.tmpl
29. `prompts/Standards.md` — from templates/prompts/Standards.md.tmpl, filling in canary thresholds and custom gates
30. `prompts/Close.md` — from templates/prompts/Close.md.tmpl
31. If TTS enabled: `prompts/TTS-Prep.md` — from templates/prompts/TTS-Prep.md.tmpl

The web UI files (docket.css + the 10 HTML pages above, including search.html) are NOT written inline — copy each from `templates/nginx/html/*` and substitute the `{{PLACEHOLDER}}` variables, exactly the same way the other templated files are produced. They are functional vanilla JS pages that call PostgREST at /api/ and link `docket.css`; everything is offline/self-contained (no CDN, no external fonts/scripts). Honor the TTS include/strip markers in character-editor.html per item 10. Every page links `docket.css` and uses `var(--accent)` for its accent color (never a hardcoded hex), so the whole site picks up the name-derived theme. Page titles and header/brand text use `{{PROJECT_NAME}}` (and `{{AUTHOR}}` where an author line fits) — never genre labels and never any VoT / Vampires-of-Tucson wording.

**Authoritative column reference for the HTML editors** — the inline CRUD pages MUST use exactly these columns (they match postgres/init.sql; do not invent `title`, `description`, `full_profile`, `resolved`, `chapter_number`, etc.):

- **characters** (PK `name`): `name`, `display_name`, `role`, `age_or_era`, `is_minor`, `background`, `arc`, `dialogue_prompt`, `image_prompt`, `tts_voice_prompt`, `tts_voice_id`, `profile_size`, `notes`. (No `brief_bio`/`full_profile`/`voice_notes`.)
- **locations** (PK `location_id`): `location_id`, `display_name`, `type`, `region`, `exterior_desc`, `interior_desc`, `sensory`, `books_present`, `notes`. (No `name`/`description`/`atmosphere`.)
- **chapters** (PK `(book, chapter, part)`; surrogate `chapter_id`): `book`, `chapter`, `part`, `pov_char`, `location` (FK→locations.location_id), `cast`, `summary`, `word_count`, `qr`, `status`, `priority`, `notes`, `storyline`, `timeline`, `season`, `last_modified`. status ∈ `concept`/`draft`/`polished`/`finished`/`published`; priority ∈ `HIGH`/`MED`/`LOW`. (Columns are `chapter`/`part`, not `chapter_number`/`part_number`; no `title`; timestamp is `last_modified`.)
- **chapter_cast**: `chapter_id` (FK→chapters.chapter_id), `character_id` (FK→characters.name). (No `character_name`/`role_in_scene`.)
- **relationships** (PK `(char_a, char_b)`): `char_a`, `char_b`, `relationship_type`, `trust_level`, `notes`.
- **notes** (PK `note_id`): `scope` (`project`/`book`/`chapter`/`character`/`location`/`group`), `book`, `chapter`, `part`, `character_name`, `location_id`, `group_id`, `priority` (`HIGH`/`MED`/`LOW`), `status` (`open`/`resolved`/`archived`), `body`, `created_at`, `expires_at`. Active notes = `status = 'open'` (not `resolved = FALSE`); body column is `body` (not `content`).
- Location joins: `chapters.location = locations.location_id`. Cast joins: `chapter_cast.character_id = characters.name`.

**Synthesis whitelist injection (mcp-server/mcp_relay.py)**: replace the
`    # {{SYNTHESIS_WHITELIST}}` marker line:
- If `synthesis_tracking = false`: replace with `    # (synthesis tracking disabled)`
- If `synthesis_tracking = true`: replace with these three lines (keep the indentation so
  they sit inside the WRITE_WHITELIST list):
  ```
      f"INSERT INTO {SCHEMA}.character_state",
      f"UPDATE {SCHEMA}.character_state",
      f"INSERT INTO {SCHEMA}.open_threads",
      f"UPDATE {SCHEMA}.open_threads",
      f"INSERT INTO {SCHEMA}.relationship_delta",
      f"UPDATE {SCHEMA}.relationship_delta",
  ```

**Synthesis table injection**: When writing `postgres/init.sql`, replace the `{{SYNTHESIS_TABLES}}` placeholder:
- If `synthesis_tracking = false`: replace with `-- Synthesis tracking disabled.`
- If `synthesis_tracking = true`: replace with the following SQL block:

```sql
CREATE TABLE IF NOT EXISTS {{SCHEMA}}.character_state (
  character_name  TEXT REFERENCES {{SCHEMA}}.characters(name) ON UPDATE CASCADE,
  book            TEXT,
  chapter         INTEGER,
  part            INTEGER,
  condition       TEXT,
  location_exit   TEXT,
  last_known_info TEXT,
  open_wounds     TEXT,
  notes           TEXT,
  PRIMARY KEY (character_name, book, chapter, part)
);

CREATE TABLE IF NOT EXISTS {{SCHEMA}}.open_threads (
  thread_id       SERIAL PRIMARY KEY,
  description     TEXT,
  planted_in      TEXT,
  status          TEXT DEFAULT 'open' CHECK (status IN ('open','resolved','dropped')),
  resolution      TEXT,
  notes           TEXT
);

CREATE TABLE IF NOT EXISTS {{SCHEMA}}.relationship_delta (
  char_a          TEXT REFERENCES {{SCHEMA}}.characters(name) ON UPDATE CASCADE,
  char_b          TEXT REFERENCES {{SCHEMA}}.characters(name) ON UPDATE CASCADE,
  book            TEXT,
  chapter         INTEGER,
  delta_type      TEXT,
  description     TEXT,
  cumulative_note TEXT,
  PRIMARY KEY (char_a, char_b, book, chapter, delta_type)
);

GRANT SELECT ON {{SCHEMA}}.character_state, {{SCHEMA}}.open_threads, {{SCHEMA}}.relationship_delta TO {{CLAUDE_USER}};
GRANT INSERT, UPDATE ON {{SCHEMA}}.character_state, {{SCHEMA}}.open_threads, {{SCHEMA}}.relationship_delta TO {{CLAUDE_USER}};
GRANT USAGE, SELECT ON SEQUENCE {{SCHEMA}}.open_threads_thread_id_seq TO {{CLAUDE_USER}};
```

---

## Phase 6 — Install extensions

For each extension the user selected:
1. Read the corresponding .sql file from the skills repo extensions/ directory
2. Note it will be run after Docker is up (deferred to Phase 8)
3. Read the .canary.json file if it exists and merge thresholds into project.json canary_thresholds
4. Add the extension name to project.json installed_extensions array
5. Update project.json on disk

---

## Phase 7 — Start Docker

**Before running anything, tell the writer what's about to happen — this is the longest
pause in setup and silence here looks like a freeze.** Print:

```
Starting your writing system's services now.

This is the slow part. On the first build, your computer downloads four programs
(the database, the search engine, the web server, and the AI search helper). That can
take 3-10 minutes depending on your internet speed - and the screen may look like it's
sitting still while large files download in the background. That's completely normal.
Please leave this window open; I'll tell you the moment it's ready.
```

From the project directory, run:
```
docker compose up -d
```

Poll for health every 10 seconds, up to 5 minutes. **Don't go silent while polling** — every
30-60 seconds print a short, plain-language progress line so the writer knows it's alive,
e.g. "Still downloading and starting up... (the database is up, waiting on the rest)" or
"Almost there - the search helper is still getting ready." Use what `docker compose ps`
actually shows; never invent progress.
```
docker compose ps
```

Wait until postgres, postgrest, nginx, AND ollama containers show status "running" or "healthy".

If Postgres takes more than 60 seconds, reassure in plain words: "The database is setting
itself up for the first time (creating your tables) - this only happens once and is normal."

The `ollama` container may take a little longer to report healthy on first run (image pull). Wait for it to reach "running"/"healthy" before the model-pull phase below. If it does not come up, do not abort the build — tell the writer in friendly terms that the AI semantic search will be unavailable until Ollama is running, but ordinary keyword search works right away, and the build will continue.

When all four are up, print: "Your services are running. Setting up your project now..."

---

## Phase 8 — Run extension SQL

For each selected extension:

1. Read the `.sql` file from the skills repo `extensions/` directory (using the Read tool — find the repo root by locating where this skill file lives)
2. Write the SQL content to a temp file in the project directory: `postgres/ext-{{EXTENSION}}.sql`
3. Copy it into the running container and execute it:
   ```
   docker cp "{{PROJECT_PATH}}\postgres\ext-{{EXTENSION}}.sql" {{PROJECT_SLUG}}-postgres:/tmp/ext.sql
   docker exec {{PROJECT_SLUG}}-postgres psql -U {{MASTER_USER}} -d {{SCHEMA}} -f /tmp/ext.sql
   ```
4. Delete the temp file after execution
5. Print: "Extension [name] installed."

Replace `{{SCHEMA}}` in the extension SQL with the actual schema name before writing the temp file — extension SQL files use `{{SCHEMA}}` as a placeholder.

---

## Phase 9 — Seed the database

Insert [EXAMPLE] instructional rows into every table so the user can see the structure immediately.

Run the following via `docker exec {{PROJECT_SLUG}}-postgres psql -U {{MASTER_USER}} -d {{SCHEMA}}`:

```sql
-- Example character (demonstrates every field)
INSERT INTO {{SCHEMA}}.characters
  (name, display_name, role, age_or_era, background, arc, dialogue_prompt, image_prompt, profile_size, notes, is_minor)
VALUES (
  '[EXAMPLE] How to Fill Characters',
  'Example Character Name',
  'protagonist',
  '30s',
  '[EXAMPLE] 2-5 sentences. Origin, formative event, what shaped this person.',
  '[EXAMPLE] Where they START and where they END UP — not what happens, what changes.',
  '[EXAMPLE] How they sound: rhythm, vocabulary, accent, verbal tells. "Clipped sentences, never finishes a thought out loud."',
  '[EXAMPLE] Visual description for image generation. Height, build, distinctive features, clothing.',
  0,
  'DELETE this row after you have added your first real character.',
  FALSE
);

-- Example location
INSERT INTO {{SCHEMA}}.locations
  (location_id, display_name, type, exterior_desc, interior_desc, sensory, notes)
VALUES (
  'example-location',
  '[EXAMPLE] Location Name',
  'interior',
  '[EXAMPLE] What does it look like from outside / approaching?',
  '[EXAMPLE] What does it look like inside?',
  '[EXAMPLE] What does it smell, sound, feel like? At least two senses.',
  'DELETE this row after adding a real location.'
);

-- Example chapter (book name uses your project name).
-- word_count is explicitly 0 and qr is left NULL: there is no manuscript yet, so the
-- dashboard/index must read honestly (0 words, no QR). Do NOT seed a fake/demo word count
-- or QR score — those numbers are computed from real prose by word_count.py and the QR flow.
INSERT INTO {{SCHEMA}}.chapters
  (book, chapter, part, status, summary, priority, word_count)
VALUES (
  '{{BOOK_NAME}}',
  1,
  1,
  'concept',
  '[EXAMPLE] One paragraph: what happens in this chapter, whose POV, where it ends.',
  'MED',
  0
);

-- Example note
INSERT INTO {{SCHEMA}}.notes (priority, scope, status, body)
VALUES (
  'HIGH',
  'project',
  'open',
  '[EXAMPLE] This is a HIGH-priority project note. Delete it and add your own in the Notes editor.'
);
```

After inserting example rows, insert real characters from the plan doc (if any were extracted in Phase 1). For each character:
```sql
INSERT INTO {{SCHEMA}}.characters (name, role, age_or_era, notes, is_minor)
VALUES ('<name>', '<role>', '<age_or_era_or_blank>', '<brief description from plan>', FALSE);
```

---

## Phase 9b — Pull embedding model + build search index

This wires up search after the seed rows exist, so the index has content from the start.

**Tell the writer before the pull — it's the second long pause.** Print:
```
Setting up AI-powered search. I'm downloading the search model now (about 300 MB,
one time only). This can take a couple of minutes and the screen may pause while it
downloads - that's expected. Keyword search already works; this adds search-by-meaning.
```

1. **Pull the embedding model** into the Ollama container (one-time, needs internet, ~300MB):
   ```
   docker exec {{PROJECT_SLUG}}-ollama ollama pull nomic-embed-text
   ```
   Wait for the pull to complete. If it fails (offline, or Ollama not up), do NOT abort:
   print a warning — "Could not pull nomic-embed-text. Semantic search will be unavailable
   until you run `docker exec {{PROJECT_SLUG}}-ollama ollama pull nomic-embed-text` and then
   `python scripts/embed.py --full`. Full-text search works regardless." — and skip step 2.

2. **Build the search index** over the seeded rows:
   ```
   python scripts/embed.py --full
   ```
   (Run from the project directory so it finds project.json + .env. It connects as the
   editor role, upserts every entity into `{{SCHEMA}}.search_index`, and fills embeddings via
   Ollama. If Ollama is down it still writes the FTS rows and leaves embeddings NULL.)

Print the embed.py summary (rows indexed / embedded / skipped / ollama-down).

---

## Phase 10 — Register MCP

Run:
```
claude mcp add {{PROJECT_SLUG}} python "{{PROJECT_PATH}}\mcp-server\mcp_relay.py"
```

Also update `%APPDATA%\Claude\claude_desktop_config.json`:
- Read the file (or create empty `{"mcpServers":{}}` if missing)
- Merge in:
  ```json
  {
    "mcpServers": {
      "{{PROJECT_SLUG}}": {
        "command": "python",
        "args": ["{{PROJECT_PATH}}\\mcp-server\\mcp_relay.py"],
        "env": {
          "DOCKET_ENV": "{{PROJECT_PATH}}\\.env"
        }
      }
    }
  }
  ```
- Write back (merge, do not overwrite other entries)

---

## Phase 11 — Create Windows Scheduled Task

Run via PowerShell:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "{{BACKUP_TIME}}"
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c \"{{PROJECT_PATH}}\bat-files\backup.bat\""
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "WritingDocket-{{PROJECT_SLUG}}-Backup" -Trigger $trigger -Action $action -Settings $settings -RunLevel Highest -Force
```

---

## Phase 12 — Print setup summary

```
╔══════════════════════════════════════════════════════════════════╗
║  Setup Complete — {{PROJECT_NAME}}                               ║
║                                                                  ║
║  Web UI:       http://localhost:{{UI_PORT}}                      ║
║  Characters:   http://localhost:{{UI_PORT}}/character-editor.html║
║  Chapters:     http://localhost:{{UI_PORT}}/chapter-editor.html  ║
║  Dashboard:    http://localhost:{{UI_PORT}}/dashboard.html       ║
║                                                                  ║
║  MCP registered as: {{PROJECT_SLUG}}                            ║
║  Backup runs nightly at {{BACKUP_TIME}}                         ║
║                                                                  ║
║  Next steps:                                                     ║
║  1. Restart Claude Desktop to activate the MCP server.          ║
║  2. Open the web UI and replace [EXAMPLE] rows with your data.  ║
║  3. Run /novel-plan before your first writing session.          ║
╚══════════════════════════════════════════════════════════════════╝
```

Print the credentials summary (master password, editor password) and warn the user to save them — they are NOT stored in the project.json.

## Phase 13 — Open the web UI

After the summary, open the writer's browser to the running UI so they land on it
immediately. Use the resolved port. On Windows, run via the Bash tool:

```
cmd /c start "" "http://127.0.0.1:{{UI_PORT}}/"
```

(The empty `""` is the required title argument for `start`; without it a quoted URL is
treated as the window title and nothing opens.) If that fails for any reason, fall back to:

```
powershell -NoProfile -Command "Start-Process 'http://127.0.0.1:{{UI_PORT}}/'"
```

Then tell the writer: "Opening your writing system in the browser. If it didn't open,
visit http://127.0.0.1:{{UI_PORT}}/ yourself." Do not block on this — a failure to launch
the browser is not a build failure.
