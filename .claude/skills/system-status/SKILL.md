---
name: system-status
description: Check health of a running writing-docket project. Usage: /system-status
---

You are checking the health of a writing-docket project.

## Step 1 — Load project

Read project.json from current directory. Load: project_slug, schema, project_path, ui_port, installed_extensions, canary_thresholds.

## Step 2 — Check Docker containers

Run: `docker compose ps` from project directory.

Parse output for: {{PROJECT_SLUG}}-postgres, {{PROJECT_SLUG}}-postgrest, {{PROJECT_SLUG}}-nginx.

Status: running/healthy = PASS, stopped/restarting/absent = FAIL.

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
```

## Step 7 — Print status report

```
╔══════════════════════════════════════════════════════╗
║  Status Report — {{PROJECT_NAME}}                    ║
╠══════════════════════════════════════════════════════╣
║  Services                                            ║
║    Postgres       [PASS/FAIL]                        ║
║    PostgREST      [PASS/FAIL]                        ║
║    Nginx (Web UI) [PASS/FAIL]  http://localhost:PORT ║
║    MCP Server     [PASS/FAIL]                        ║
╠══════════════════════════════════════════════════════╣
║  Project Stats                                       ║
║    Characters:    [N]                                ║
║    Chapters:      [N]                                ║
║    Total words:   [N]                                ║
║    Open HIGH notes: [N]                              ║
╠══════════════════════════════════════════════════════╣
║  Recent QR Scores                                    ║
║    Ch1: [score]  Ch2: [score]  Ch3: [score]         ║
╠══════════════════════════════════════════════════════╣
║  Backup                                              ║
║    Last backup:   [date] ([size])                    ║
╚══════════════════════════════════════════════════════╝
```
