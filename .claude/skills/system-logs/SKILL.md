---
name: system-logs
description: Collect all logs (containers + build + scripts) into one diagnostic file. Usage: /system-logs [project-name]
---

You are gathering every log into a single file the writer can read or send when something
is wrong. Read-only — never change configuration or data.

## Step 1 — Load project context

Read `project.json` (current dir or search upward; or use the project name argument to find
the folder under the workspace). Capture `project_slug` (= schema/container prefix),
`project_path`, `ui_port`.

## Step 2 — Build the diagnostic file

Create `{{PROJECT_PATH}}\logs\` if needed. Write a fresh file
`{{PROJECT_PATH}}\logs\diagnostic-[YYYY-MM-DD-HHMM].txt` containing, in order, with a clear
header before each section:

1. **Summary** — project name, slug, UI port, today's date/time, schema_version.
2. **Container status** —
   `docker ps -a --filter "name={{PROJECT_SLUG}}-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`
3. **Container logs** — last 200 lines of each, labeled:
   - `docker logs --tail 200 {{PROJECT_SLUG}}-postgres`
   - `docker logs --tail 200 {{PROJECT_SLUG}}-postgrest`
   - `docker logs --tail 200 {{PROJECT_SLUG}}-nginx`
   - `docker logs --tail 200 {{PROJECT_SLUG}}-ollama`
4. **Postgres errors only** (quick triage) —
   `docker logs {{PROJECT_SLUG}}-postgres 2>&1 | findstr /I "error fatal panic denied \"does not exist\""`
5. **Health probes** —
   - PostgREST: `curl -s -o NUL -w "%%{http_code}" http://127.0.0.1:3000/`
   - Web UI: `curl -s -o NUL -w "%%{http_code}" http://127.0.0.1:{{UI_PORT}}/`
   - Ollama: `curl -s http://127.0.0.1:11434/api/tags`
6. **Search index state** —
   `docker exec {{PROJECT_SLUG}}-postgres psql -U docket_master -d {{SCHEMA}} -c "SELECT count(*) total, count(embedding) embedded FROM {{SCHEMA}}.search_index;"`
7. **Project log tails** — the last 50 lines of each file in `{{PROJECT_PATH}}\logs\` EXCEPT
   the diagnostic file you're writing: the most recent `build-*.log`, `embed.log`,
   `word_count.log`, `backup.log` (whichever exist).

Never include `.env` contents or any password in the diagnostic file. If you encounter a
credential, write `[redacted]`.

## Step 3 — Report

Print a short verdict: which containers are up/down, any error lines found, the search
index counts, and the full path to the diagnostic file. Tell the writer: "If you need help,
open or send this file: [path] — it has everything needed to diagnose the problem, and no
passwords."
