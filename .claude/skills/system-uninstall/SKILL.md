---
name: system-uninstall
description: Tear down a writing-docket project. Usage: /system-uninstall
---

You are uninstalling a writing-docket project. Follow carefully — some data will be permanently deleted.

**Talk to a novelist, not a developer.** Open with one plain sentence saying what you're
about to do, for example: "I'll remove the machinery that runs your writing system; your
actual writing stays safe on your computer." Before you run any commands, reassure the
writer in plain words: Claude Code may pop up approval boxes asking "Do you want to
proceed?" (sometimes with technical wording like "manual approval required"); that's normal
and safe, so choose Yes (or "Yes, don't ask again" if offered), and it never means
something went wrong. Narrate the steps in everyday language and finish with a friendly,
plain-English summary instead of raw command output.

**This permanently removes things, so be calm but crystal clear.** In the confirmation
step, say in plain words exactly what gets deleted (the database and the behind-the-scenes
program files) and, just as clearly, what is kept and stays safe: their chapters, notes,
QR files, backups, and plan. Do not delete anything until the writer has clearly confirmed;
keep the existing confirmation requirement (typing the project name exactly) exactly as
written below.

## Step 1 — Find the project

Read `project.json` from the current directory (or search upward). If not found, ask: "Where is your project folder?"

Load: project_name, project_slug, schema, project_path, ui_port.

## Step 2 — Print what will be deleted

```
The following will be permanently deleted:
  - Docker containers: {{PROJECT_SLUG}}-postgres, {{PROJECT_SLUG}}-postgrest, {{PROJECT_SLUG}}-nginx, {{PROJECT_SLUG}}-ollama
  - Docker images: pgvector/pgvector:pg16, postgrest/postgrest, nginx:alpine, ollama/ollama
  - Docker volume: {{PROJECT_SLUG}}_pgdata (ALL DATABASE DATA)
  - Docker volume: {{PROJECT_SLUG}}_ollama (downloaded embedding model)
  - Infrastructure files: docker-compose.yml, postgres/, postgrest/, nginx/, mcp-server/, scripts/, bat-files/, prompts/
  - MCP registration: {{PROJECT_SLUG}} from Claude config
  - Windows Scheduled Task: WritingDocket-{{PROJECT_SLUG}}-Backup

The following will NOT be deleted (your writing is safe):
  - Chapters/
  - Notes/
  - qr/
  - backups/
  - docket-plan.md (if present)
  - project.json
```

## Step 3 — Confirm

Print: "To confirm uninstall, type the project name exactly: {{PROJECT_NAME}}"

Wait for input. If input does not match exactly, abort: "Confirmation did not match. Uninstall cancelled."

## Step 4 — Execute uninstall

Run in order:

1. `docker compose down --rmi all -v` (from project directory) — this removes all four containers ({{PROJECT_SLUG}}-postgres, -postgrest, -nginx, -ollama), their images, and both named volumes ({{PROJECT_SLUG}}_pgdata and {{PROJECT_SLUG}}_ollama). If either volume lingers (e.g. compose file already deleted), remove it explicitly: `docker volume rm {{PROJECT_SLUG}}_pgdata {{PROJECT_SLUG}}_ollama`.
2. Drop DB roles (connect as master user first time, then drop):
   - Read master password from .env
   - `docker exec {{PROJECT_SLUG}}-postgres psql -U {{MASTER_USER}} -c "DROP SCHEMA {{SCHEMA}} CASCADE;"` — but container is down, skip this; schema is in the volume which is deleted
3. Remove MCP from claude_desktop_config.json — read the file, delete the key for {{PROJECT_SLUG}}, write back
4. Run `claude mcp remove {{PROJECT_SLUG}}`
5. Remove scheduled task: `schtasks /Delete /TN "WritingDocket-{{PROJECT_SLUG}}-Backup" /F`
6. Delete infrastructure files (use PowerShell Remove-Item):
   - docker-compose.yml, .env, .env.example, .gitignore
   - Directories: postgres/, postgrest/, nginx/, mcp-server/, scripts/, bat-files/, prompts/

## Step 5 — Confirm completion

Print:
```
Uninstall complete. Your writing files are preserved at:
  {{PROJECT_PATH}}\Chapters\
  {{PROJECT_PATH}}\Notes\
  {{PROJECT_PATH}}\qr\
  {{PROJECT_PATH}}\backups\
```
