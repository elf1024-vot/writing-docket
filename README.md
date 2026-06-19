# writing-docket

A Claude Code skill package that builds a complete local writing infrastructure for novelists - Postgres database, PostgREST API, web UI editors, built-in search (full-text + semantic), MCP server, automated backups, and AI writing prompts - all from a single command.

## How to start (three ways)

You need **Claude Code** and **Docker Desktop** installed first (see Prerequisites below; new to this? read [INSTALL.md](INSTALL.md)). Then pick whichever is easiest:

**A. One-click (easiest).** Download this repo (green **Code** button on GitHub, then **Download ZIP**), unzip it, and double-click **`install.bat`**. It installs the skill and opens Claude Code; then type `/start-here`.

**B. One command.** In a terminal:
```bash
claude skill install https://github.com/elf1024-vot/writing-docket
```
Then start Claude Code (`claude`) and type `/start-here`.

**C. Already have Claude Code open.** Just run the install command above in it, then `/start-here`.

After that, `/start-here` interviews you and builds everything. Make sure Docker Desktop is running before you build. You will see a **Setup Complete** message and your browser will open to the writing system.

## Search

Every build ships with search on by default, both flavors fully offline:

- **Full-text search** is always available - PostgreSQL indexes every character, location, group, chapter, note, and chapter prose file automatically (a generated `tsvector`), so keyword search works with zero setup.
- **Semantic search** finds content by meaning via a local `ollama` container running `nomic-embed-text` (768-dim vectors) with the `pgvector` extension. The model is pulled once (~300MB) at setup; after that it runs entirely on your machine - no data ever leaves it.

Search is exposed three ways: a UI Search page, PostgREST RPC functions (`search_fts`, `search_semantic`), and an MCP tool (`pg_search`). If Ollama is down, semantic search falls back to full-text - it never crashes.

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
