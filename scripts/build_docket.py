#!/usr/bin/env python3
"""
build_docket.py - deterministic project-file writer for writing-docket.

The /system-build skill writes <project>/project.json and <project>/.env first
(config + generated secrets), then runs:

    python scripts/build_docket.py --project-path "<project>"

This script reads those two inputs, substitutes every {{PLACEHOLDER}} across the
templates in this repo, and writes the full project tree (docker-compose, init.sql,
the web UI, prompts, scripts, intake CSVs, .gitignore, .env.example). Everything
after file generation - docker up, seeding, extension SQL, the model pull, embedding,
MCP registration, the scheduled task - stays in the skill.

It does NOT overwrite project.json or .env (its inputs). On success it prints a
summary and exits 0. If any {{PLACEHOLDER}} is left unsubstituted in a generated
file, it prints them and exits 1 so the build skill can fall back to manual writing.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TPL = REPO / "templates"

# Synthesis schema block, injected into init.sql only when synthesis_tracking=yes.
# {{SCHEMA}}/{{CLAUDE_USER}} are pre-filled before injection (see build()).
SYNTHESIS_SQL = """CREATE TABLE IF NOT EXISTS {{SCHEMA}}.character_state (
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
GRANT USAGE, SELECT ON SEQUENCE {{SCHEMA}}.open_threads_thread_id_seq TO {{CLAUDE_USER}};"""

# The synthesis entries added to the mcp_relay write-whitelist (kept as literal
# Python f-string source: {SCHEMA} is a runtime variable in mcp_relay, NOT a
# template placeholder, so it must survive substitution verbatim).
SYNTHESIS_WHITELIST = (
    '    f"INSERT INTO {SCHEMA}.character_state",\n'
    '    f"UPDATE {SCHEMA}.character_state",\n'
    '    f"INSERT INTO {SCHEMA}.open_threads",\n'
    '    f"UPDATE {SCHEMA}.open_threads",\n'
    '    f"INSERT INTO {SCHEMA}.relationship_delta",\n'
    '    f"UPDATE {SCHEMA}.relationship_delta",'
)

# template rel path -> output rel path (under the project dir)
FILES = [
    ("docker-compose.yml.tmpl", "docker-compose.yml"),
    ("init.sql.tmpl", "postgres/init.sql"),
    ("postgrest.conf.tmpl", "postgrest/postgrest.conf"),
    ("nginx.conf.tmpl", "nginx/nginx.conf"),
    ("nginx/html/docket.css", "nginx/html/docket.css"),
    ("nginx/html/index.html", "nginx/html/index.html"),
    ("nginx/html/character-editor.html", "nginx/html/character-editor.html"),
    ("nginx/html/chapter-editor.html", "nginx/html/chapter-editor.html"),
    ("nginx/html/location-editor.html", "nginx/html/location-editor.html"),
    ("nginx/html/dashboard.html", "nginx/html/dashboard.html"),
    ("nginx/html/chapter-tracker.html", "nginx/html/chapter-tracker.html"),
    ("nginx/html/search.html", "nginx/html/search.html"),
    ("nginx/html/faq.html", "nginx/html/faq.html"),
    ("nginx/html/readme.html", "nginx/html/readme.html"),
    ("mcp_relay.py.tmpl", "mcp-server/mcp_relay.py"),
    ("word_count.py", "scripts/word_count.py"),
    ("canary.py", "scripts/canary.py"),
    ("embed.py", "scripts/embed.py"),
    ("migrate.py", "scripts/migrate.py"),
    ("backup.bat.tmpl", "bat-files/backup.bat"),
    ("restore.bat.tmpl", "bat-files/restore.bat"),
    ("prompts/Init.md.tmpl", "prompts/Init.md"),
    ("prompts/Writing-Prompt.md.tmpl", "prompts/Writing-Prompt.md"),
    ("prompts/Character-Agent.md.tmpl", "prompts/Character-Agent.md"),
    ("prompts/Planning.md.tmpl", "prompts/Planning.md"),
    ("prompts/QR.md.tmpl", "prompts/QR.md"),
    ("prompts/Polish.md.tmpl", "prompts/Polish.md"),
    ("prompts/Standards.md.tmpl", "prompts/Standards.md"),
    ("prompts/Close.md.tmpl", "prompts/Close.md"),
]

INTAKE = ["characters.csv", "locations.csv", "groups.csv", "chapters.csv", "README.txt"]


def load_env(path: Path) -> dict:
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def build(project_path: Path) -> int:
    proj = json.loads((project_path / "project.json").read_text(encoding="utf-8"))
    env = load_env(project_path / ".env")

    slug = proj["project_slug"]
    schema = proj.get("schema", slug)
    canary = proj.get("canary_thresholds", {})
    synthesis = bool(proj.get("synthesis_tracking", False))
    tts = bool(proj.get("tts_enabled", False))
    claude_user = env.get("CLAUDE_USER", "docket_claude")
    custom_gates_raw = proj.get("custom_gates", []) or []

    # Conditional fragments -------------------------------------------------
    if synthesis:
        syn_whitelist = SYNTHESIS_WHITELIST
        syn_tables = SYNTHESIS_SQL.replace("{{SCHEMA}}", schema).replace("{{CLAUDE_USER}}", claude_user)
    else:
        syn_whitelist = "    # (synthesis tracking disabled)"
        syn_tables = "-- Synthesis tracking disabled."

    if custom_gates_raw:
        custom_gates = "\n\n".join(
            f"**G{9 + i} - Project-specific**\n{g}" for i, g in enumerate(custom_gates_raw))
    else:
        custom_gates = "None."

    repl = {
        "PROJECT_NAME": proj["project_name"],
        "SCHEMA": schema,
        "PROJECT_SLUG": slug,
        "PROJECT_PATH": str(project_path),
        "AUTHOR": proj.get("author", ""),
        "GENRE": proj.get("genre", ""),
        "BUILD_DATE": proj.get("built_on", ""),
        "BOOK_NAME": proj.get("book_name", proj["project_name"]),
        "ACCENT_COLOR": proj.get("accent_color", "#7a6e8a"),
        "UI_PORT": str(proj.get("ui_port", env.get("UI_PORT", "8090"))),
        "MASTER_USER": env.get("POSTGRES_USER", "docket_master"),
        "MASTER_PASSWORD": env.get("POSTGRES_PASSWORD", ""),
        "EDITOR_USER": env.get("EDITOR_USER", "docket_editor"),
        "EDITOR_PASSWORD": env.get("EDITOR_PASSWORD", ""),
        "CLAUDE_USER": claude_user,
        "CLAUDE_PASSWORD": env.get("CLAUDE_PASSWORD", ""),
        "POSTGREST_JWT_SECRET": env.get("JWT_SECRET", ""),
        "SYNTHESIS_WHITELIST": syn_whitelist,
        "SYNTHESIS_TABLES": syn_tables,
        "CUSTOM_GATES": custom_gates,
        # canary thresholds -> Standards.md placeholders
        "PASSIVE_VOICE": str(canary.get("passive_voice", 12)),
        "EMOTION_TELLS": str(canary.get("emotion_tells", 10)),
        "WEAK_ADVERBS": str(canary.get("weak_adverbs_per_1k", 6.0)),
        "SENTENCE_VARIETY": str(canary.get("sentence_variety_std_dev", 5.5)),
        "COMPLEX_PARAGRAPHS": str(canary.get("complex_paragraphs", 8)),
        "FK_GRADE": str(canary.get("readability_fk_grade", 8)),
        "GLUE_INDEX": str(canary.get("glue_index", 38)),
    }

    def sub(text: str) -> str:
        return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: repl.get(m.group(1), m.group(0)), text)

    def strip_block(text: str, start: str, end: str) -> str:
        return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.DOTALL)

    # Directories -----------------------------------------------------------
    for d in ["postgres", "postgrest", "nginx/html", "mcp-server", "scripts",
              "bat-files", "prompts", "intake", "Chapters", "Notes", "qr",
              "backups", "logs"]:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    files = list(FILES)
    if tts:
        files.append(("prompts/TTS-Prep.md.tmpl", "prompts/TTS-Prep.md"))

    written = []
    for src, dst in files:
        text = (TPL / src).read_text(encoding="utf-8")
        if dst == "nginx/html/character-editor.html" and not tts:
            text = strip_block(text, "<!-- TTS_BLOCK_START -->", "<!-- TTS_BLOCK_END -->")
            text = strip_block(text, "// TTS_PAYLOAD_START", "// TTS_PAYLOAD_END")
        (project_path / dst).write_text(sub(text), encoding="utf-8")
        written.append(dst)

    # Intake CSVs (verbatim, no substitution) -------------------------------
    for f in INTAKE:
        shutil.copyfile(TPL / "intake" / f, project_path / "intake" / f)
        written.append("intake/" + f)

    # Derived files (project.json + .env are inputs, never overwritten) ------
    (project_path / ".gitignore").write_text(
        ".env\nbackups/\nChapters/\nNotes/\nqr/\npostgres/data/\nlogs/\n__pycache__/\n*.pyc\n",
        encoding="utf-8")
    env_text = (project_path / ".env").read_text(encoding="utf-8")
    env_example = re.sub(r"(PASSWORD|JWT_SECRET)=.*", r"\1=changeme", env_text)
    (project_path / ".env.example").write_text(env_example, encoding="utf-8")
    written += [".gitignore", ".env.example"]

    # Leftover-placeholder audit -------------------------------------------
    leftovers = {}
    for dst in written:
        if dst.endswith((".csv", ".txt")):
            continue
        t = (project_path / dst).read_text(encoding="utf-8", errors="ignore")
        hits = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", t)))
        if hits:
            leftovers[dst] = hits

    print(f"build_docket: wrote {len(written)} files into {project_path}")
    if leftovers:
        print("ERROR: unsubstituted placeholders remain:")
        print(json.dumps(leftovers, indent=2))
        return 1
    print("build_docket: all placeholders resolved, no leftovers.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write a writing-docket project from project.json + .env.")
    ap.add_argument("--project-path", required=True, help="Project directory containing project.json and .env.")
    args = ap.parse_args(argv)
    pp = Path(args.project_path)
    if not (pp / "project.json").exists() or not (pp / ".env").exists():
        print(f"ERROR: {pp} must contain both project.json and .env before running this.", file=sys.stderr)
        return 1
    return build(pp)


if __name__ == "__main__":
    raise SystemExit(main())
