---
name: system-restore
description: Restore a writing-docket project from a backup. Usage: /system-restore
---

You are restoring a writing-docket project from a backup.

## Step 1 — Load project context

Read project.json. Load: project_slug, schema, project_path.

## Step 2 — List backups

List all files in backups/ directory. Group by type:
- DB backups: `{{PROJECT_SLUG}}-YYYY-MM-DD.sql` or `.sql.gz`
- Manuscript backups: `{{PROJECT_SLUG}}-manuscripts-YYYY-MM-DD.zip`

Print a table:
```
Available backups:
┌────┬──────────────────────────────────────────────┬──────────┬────────────────┐
│ #  │ File                                         │ Size     │ Date           │
├────┼──────────────────────────────────────────────┼──────────┼────────────────┤
│ 1  │ the_iron_compass-2026-06-18.sql              │ 2.3 MB   │ 2026-06-18     │
│ 2  │ the_iron_compass-manuscripts-2026-06-18.zip  │ 145 KB   │ 2026-06-18     │
└────┴──────────────────────────────────────────────┴──────────┴────────────────┘
```

## Step 3 — Ask what to restore

"What would you like to restore?
  1. Database only (from a .sql backup)
  2. Manuscripts only (from a .zip backup)
  3. Both database and manuscripts
  4. Cancel"

Then ask: "Which backup date? (Enter the number from the table)"

## Step 4 — Confirm

Print what will happen. Then: "Type YES to confirm restore. This will overwrite current data."

Wait for exactly "YES" — anything else aborts.

## Step 5 — Execute restore

**If DB restore:**
1. Stop containers: `docker compose stop postgrest nginx`
2. Drop and recreate schema:
   ```sql
   DROP SCHEMA {{SCHEMA}} CASCADE;
   CREATE SCHEMA {{SCHEMA}};
   ```
3. Restore: `docker exec -i {{PROJECT_SLUG}}-postgres psql -U {{MASTER_USER}} -d {{SCHEMA}} < backups/{{BACKUP_FILE}}`
4. Re-run any extension SQL for installed_extensions
5. Restart containers: `docker compose start postgrest nginx`

**If manuscript restore:**
1. Warn: "This will overwrite files in Chapters/, Notes/, and qr/. Your current files will be replaced."
2. Extract: `Expand-Archive -Path backups/{{ZIP_FILE}} -DestinationPath {{PROJECT_PATH}} -Force`

## Step 6 — Confirm completion

Print: "Restore complete. Restored from [backup file]."
