---
name: system-upgrade
description: Upgrade writing-docket to the latest skill version. Usage: /system-upgrade
---

You are upgrading the writing-docket skill and the installed project infrastructure.

## Step 1 — Load project context

Read project.json. Load: project_slug, schema, project_path, schema_version, installed_extensions.

## Step 2 — Check current skill version

The skills are installed in Claude Code's skill directory. Find the installed writing-docket repo path via `claude skill list`.

## Step 3 — Pull latest (if git repo)

If the skills repo has a .git directory, run `git pull origin main` from the repo root.

If not a git repo, print: "Skills were not installed via git. To get updates, run: claude skill install https://github.com/elf1024-vot/writing-docket"
Stop here.

## Step 4 — Check schema version

Read the latest schema version from migrations/ directory (highest version number).

Compare to project.json schema_version.

If project is behind: "Schema migration required: {{CURRENT}} → {{LATEST}}. This will ALTER your database. Continue? [y/n]"

## Step 5 — Run migrations (if needed)

Run scripts/migrate.py from the project directory:
```
python scripts/migrate.py --from {{CURRENT_VERSION}} --to {{LATEST_VERSION}}
```

migrate.py handles all intermediate migrations in order.

Update project.json schema_version after successful migration.

## Step 6 — Update prompts

Copy updated prompt templates from the skills repo into the project's prompts/ directory.

EXCEPTION: Do not overwrite prompts/Standards.md — it may contain custom gates. Instead:
1. Read the project's Standards.md
2. Read the new Standards.md.tmpl
3. Compare the G1-G8 section
4. If G1-G8 changed, print a diff and ask: "Quality gates have been updated. Apply updates? [y/n]"
5. Never delete custom gates (G9+)

## Step 7 — Rebuild containers

```
docker compose pull
docker compose up -d --build
```

## Step 8 — Confirm

Print: "Upgrade complete. Schema: {{OLD}} → {{NEW}}. Prompts updated. Containers rebuilt."
