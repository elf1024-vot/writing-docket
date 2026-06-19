# writing-docket

A Claude Code skill package that builds a complete local writing infrastructure for novelists — Postgres database, PostgREST API, web UI editors, MCP server, automated backups, and AI writing prompts — all from a single command.

## Prerequisites

- [Claude Code](https://claude.ai/code) (latest)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL2 backend on Windows)
- Python 3.9+
- Windows 10 version 2004 (build 19041) or later

## Install

```bash
claude skill install https://github.com/elf1024-vot/writing-docket
```

**New to this? Read [INSTALL.md](INSTALL.md)** — a complete, non-technical, step-by-step
walkthrough from a fresh Windows PC (installing WSL2, Docker, Python, and Claude Code),
plus troubleshooting. The quick version below assumes the prerequisites are already in place.

## Usage

1. **Run `/start-here`** — it interviews you and writes a `docket-plan.md` you can review and edit. (Or write the plan by hand, or skip it entirely.)
2. Run `/system-build docket-plan.md` in Claude Code (or just `/system-build` to answer everything in conversation).
3. Answer any remaining intake questions (project name, genre, series, workspace path, backup time).
4. Wait for setup to complete (~5 minutes first run for Docker pulls).
5. Open `http://localhost:8090` in your browser.

## After setup

**Populate your world** — two ways, both build the keys and links for you (build in this order: characters → locations → groups → chapters):

*Conversational* — paste a list, Claude scaffolds the rows:

1. `/novel-add-characters` — create characters from a list of names
2. `/novel-add-locations` — create locations from a list
3. `/novel-add-group` — create groups/factions from a list (can reference character leaders)
4. `/novel-add-book` — register a book and scaffold blank chapters

*Spreadsheet (recommended for bulk entry)* — fill in the `intake\*.csv` templates **locally** in Excel, LibreOffice, or Google Sheets, then:

- `/novel-import` — reads the filled CSVs, generates ids, resolves links, inserts rows

> **Recommended: keep it offline.** The CSV templates live on your machine and never leave
> it — your story bible stays private and works with no internet. A live Google Sheets sync
> (cloud) is planned as an explicit opt-in for anyone who wants it, but the local CSV path
> is the recommended default.

Then write:

- `/novel-plan` — Get a structured scene brief before writing
- `/system-status` — Check all services
- `/system-extend romance` — Add romance-specific DB columns and canary overrides
- `/system-restore` — Restore from a backup

## FAQ

After setup, a full FAQ is available at `http://localhost:8090/faq.html`.

---

## Author

Built by E.L. Frederick. If this is useful to you, please subscribe:
**https://substack.com/@elfrederick**
