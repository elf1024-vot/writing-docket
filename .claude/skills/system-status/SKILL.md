---
name: system-status
description: Check health of a running writing-docket project. Usage: /system-status
---

You are checking the health of a writing-docket project.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll run a quick health check on your writing system to make
sure everything's running; this only looks, it doesn't change anything." Before you run any
checks, reassure the writer in plain words: Claude Code may pop up approval boxes asking
"Do you want to proceed?" (sometimes with technical wording like "manual approval
required"); that's normal and safe, so choose Yes (or "Yes, don't ask again" if offered),
and it never means something went wrong. Narrate the checks in everyday language and give a
friendly plain-English summary of the results first; the status table and numbers can
follow, but lead with a human sentence ("Good news, everything's up and running").

## Step 1 — Load project

Read project.json from current directory. Load: project_slug, schema, project_path, ui_port, installed_extensions, canary_thresholds.

## Step 2 — Check Docker containers

Run: `docker compose ps` from project directory.

Parse output for: {{PROJECT_SLUG}}-postgres, {{PROJECT_SLUG}}-postgrest, {{PROJECT_SLUG}}-nginx, {{PROJECT_SLUG}}-ollama.

Status: running/healthy = PASS, stopped/restarting/absent = FAIL.

For the ollama container, also confirm the embedding model is present:
```
docker exec {{PROJECT_SLUG}}-ollama ollama list
```
Look for `nomic-embed-text` in the output. If the container is up but the model is missing,
report WARN — "Ollama running but nomic-embed-text not pulled; semantic search unavailable.
Run: docker exec {{PROJECT_SLUG}}-ollama ollama pull nomic-embed-text, then python scripts/embed.py --full."
If the ollama container is down, report it as WARN (not FAIL): full-text search still works;
only semantic search is affected.

## Step 3 — Check PostgREST

Run: `curl -s http://127.0.0.1:3000/` — expect 200 response.

## Step 4 — Check MCP

Run: `claude mcp list` — verify {{PROJECT_SLUG}} appears.

## Step 5 — Check last backup

List files in backups/ sorted by date. Report most recent backup file name and size.

If no backups found: WARN — "No backups found. Run bat-files\backup.bat manually."

If most recent backup is older than 2 days: WARN — "Last backup is [N] days old."

## Step 6 — Query DB stats

Via docker exec psql, run:
```sql
SELECT COUNT(*) FROM {{SCHEMA}}.characters WHERE name NOT LIKE '[EXAMPLE]%';
SELECT COUNT(*) FROM {{SCHEMA}}.chapters WHERE summary NOT LIKE '[EXAMPLE]%';
SELECT SUM(word_count) FROM {{SCHEMA}}.chapters;
SELECT COUNT(*) FROM {{SCHEMA}}.notes WHERE priority='HIGH' AND status='open';
SELECT chapter, summary, qr FROM {{SCHEMA}}.chapters ORDER BY chapter DESC LIMIT 3;
SELECT count(*), count(embedding) FROM {{SCHEMA}}.search_index;
```

The last query reports the search index health: total indexed rows vs. rows with an
embedding. If `count(*) > 0` but `count(embedding) = 0`, semantic search has nothing to
match against — note that the model pull + `python scripts/embed.py --full` still needs to
run (full-text search works regardless).

## Step 7 — Print status report

```
╔══════════════════════════════════════════════════════╗
║  Status Report — {{PROJECT_NAME}}                    ║
╠══════════════════════════════════════════════════════╣
║  Services                                            ║
║    Postgres       [PASS/FAIL]                        ║
║    PostgREST      [PASS/FAIL]                        ║
║    Nginx (Web UI) [PASS/FAIL]  http://localhost:PORT ║
║    Ollama         [PASS/WARN]  (model: nomic-embed)  ║
║    MCP Server     [PASS/FAIL]                        ║
╠══════════════════════════════════════════════════════╣
║  Project Stats                                       ║
║    Characters:    [N]                                ║
║    Chapters:      [N]                                ║
║    Total words:   [N]                                ║
║    Open HIGH notes: [N]                              ║
║    Search index:  [N] rows / [N] embedded           ║
╠══════════════════════════════════════════════════════╣
║  Recent QR Scores                                    ║
║    Ch1: [score]  Ch2: [score]  Ch3: [score]         ║
╠══════════════════════════════════════════════════════╣
║  Backup                                              ║
║    Last backup:   [date] ([size])                    ║
╚══════════════════════════════════════════════════════╝
```
