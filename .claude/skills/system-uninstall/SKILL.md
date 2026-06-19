---
name: system-uninstall
description: Tear down a writing-docket project. Usage: /system-uninstall
---

You are uninstalling a writing-docket project. Follow carefully — some data will be permanently deleted.

## Step 1 — Find the project

Read `project.json` from the current directory (or search upward). If not found, ask: "Where is your project folder?"

Load: project_name, project_slug, schema, project_path, ui_port.

## Step 2 — Print what will be deleted

```
The following will be permanently deleted:
  - Docker containers: {{PROJECT_SLUG}}-postgres, {{PROJECT_SLUG}}-postgrest, {{PROJECT_SLUG}}-nginx
  - Docker images: postgres:16, postgrest/postgrest, nginx:alpine
  - Docker volume: {{PROJECT_SLUG}}_pgdata (ALL DATABASE DATA)
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

1. `docker compose down --rmi all -v` (from project directory)
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
