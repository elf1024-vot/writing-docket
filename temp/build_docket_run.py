#!/usr/bin/env python3
"""One-shot writing-docket builder (stand-in for scripts/build_docket.py).
Reads templates/, substitutes placeholders, writes the full project tree.
Run from the writing-docket repo root."""
import json, os, re, secrets, datetime, shutil
from pathlib import Path

REPO = Path(r"C:\Users\elf10\ClaudeCoWork\writing-docket")
TPL  = REPO / "templates"

# ---- resolved config -------------------------------------------------------
PROJECT_NAME = "TEST"
SLUG         = "test"
AUTHOR       = "TEST Author"
GENRE        = "Fantasy"
WORKSPACE    = r"C:\Users\elf10\ClaudeCoWork"
PROJECT_PATH = Path(WORKSPACE) / "TEST"
BOOK_NAME    = "TEST Book One"
UI_PORT      = 8090
EXTENSIONS   = ["fantasy-magic"]
SYNTHESIS    = False
TTS          = False
TTS_PROVIDER = None
BACKUP_TIME  = "23:00"
BUILD_DATE   = "2026-06-19"
ACCENT       = "hsl(320, 55%, 58%)"   # 'TEST' char-code sum 320 % 360
CUSTOM_GATES_RAW = ["this is a TEST project; nothing here is real content"]

CANARY = {
    "passive_voice": 12,
    "emotion_tells": 10,
    "weak_adverbs_per_1k": 6.0,
    "sentence_variety_std_dev": 5.5,
    "complex_paragraphs": 10,
    "readability_fk_grade": 9,
    "glue_index": 38,
}

MASTER_USER, EDITOR_USER, CLAUDE_USER = "docket_master", "docket_editor", "docket_claude"
PW_MASTER = secrets.token_urlsafe(16)
PW_EDITOR = secrets.token_urlsafe(16)
PW_CLAUDE = secrets.token_urlsafe(16)
JWT       = secrets.token_urlsafe(32)

# ---- project.json ----------------------------------------------------------
project_json = {
    "project_name": PROJECT_NAME,
    "project_slug": SLUG,
    "author": AUTHOR,
    "genre": GENRE,
    "workspace_path": WORKSPACE,
    "project_path": str(PROJECT_PATH),
    "schema": SLUG,
    "ui_port": UI_PORT,
    "series": False,
    "series_name": None,
    "book_name": BOOK_NAME,
    "installed_extensions": EXTENSIONS,
    "synthesis_tracking": SYNTHESIS,
    "tts_enabled": TTS,
    "tts_provider": TTS_PROVIDER,
    "scheduled_backup_time": BACKUP_TIME,
    "schema_version": "1.0",
    "built_on": BUILD_DATE,
    "canary_thresholds": CANARY,
    "custom_gates": CUSTOM_GATES_RAW,
    "accent_color": ACCENT,
    "search": {
        "embedding_model": "nomic-embed-text",
        "embedding_dims": 768,
        "ollama_url": "http://127.0.0.1:11434",
    },
}

# ---- directories -----------------------------------------------------------
for d in ["postgres", "postgrest", "nginx/html", "mcp-server", "scripts",
          "bat-files", "prompts", "intake", "Chapters", "Notes", "qr",
          "backups", "logs"]:
    (PROJECT_PATH / d).mkdir(parents=True, exist_ok=True)

(PROJECT_PATH / "project.json").write_text(json.dumps(project_json, indent=2), encoding="utf-8")

# ---- .env / .env.example ---------------------------------------------------
env = f"""POSTGRES_DB={SLUG}
POSTGRES_USER={MASTER_USER}
POSTGRES_PASSWORD={PW_MASTER}
EDITOR_USER={EDITOR_USER}
EDITOR_PASSWORD={PW_EDITOR}
CLAUDE_USER={CLAUDE_USER}
CLAUDE_PASSWORD={PW_CLAUDE}
JWT_SECRET={JWT}
UI_PORT={UI_PORT}
PROJECT_SLUG={SLUG}
DOCKET_ENV={PROJECT_PATH}\\.env
OLLAMA_URL=http://127.0.0.1:11434
EMBED_MODEL=nomic-embed-text
"""
(PROJECT_PATH / ".env").write_text(env, encoding="utf-8")

env_example = re.sub(r"(PASSWORD|JWT_SECRET)=.*", r"\1=changeme", env)
(PROJECT_PATH / ".env.example").write_text(env_example, encoding="utf-8")

(PROJECT_PATH / ".gitignore").write_text(
    ".env\nbackups/\nChapters/\nNotes/\nqr/\npostgres/data/\n__pycache__/\n*.pyc\n",
    encoding="utf-8")

# ---- conditional fragments -------------------------------------------------
if SYNTHESIS:
    syn_whitelist = ('    f"INSERT INTO {SCHEMA}.character_state",\n'
                     '    f"UPDATE {SCHEMA}.character_state",\n'
                     '    f"INSERT INTO {SCHEMA}.open_threads",\n'
                     '    f"UPDATE {SCHEMA}.open_threads",\n'
                     '    f"INSERT INTO {SCHEMA}.relationship_delta",\n'
                     '    f"UPDATE {SCHEMA}.relationship_delta",')
else:
    syn_whitelist = "    # (synthesis tracking disabled)"

if SYNTHESIS:
    syn_tables = (REPO / "temp" / "_synthesis_block.sql").read_text(encoding="utf-8")
else:
    syn_tables = "-- Synthesis tracking disabled."

if CUSTOM_GATES_RAW:
    custom_gates = "\n\n".join(
        f"**G{9+i} — Project-specific**\n{g}" for i, g in enumerate(CUSTOM_GATES_RAW))
else:
    custom_gates = "None."

tts_provider_notes = TTS_PROVIDER or "TTS not configured for this project."

REPL = {
    "PROJECT_NAME": PROJECT_NAME, "SCHEMA": SLUG, "PROJECT_SLUG": SLUG,
    "PROJECT_PATH": str(PROJECT_PATH), "AUTHOR": AUTHOR, "GENRE": GENRE,
    "BUILD_DATE": BUILD_DATE, "BOOK_NAME": BOOK_NAME, "ACCENT_COLOR": ACCENT,
    "UI_PORT": str(UI_PORT),
    "MASTER_USER": MASTER_USER, "MASTER_PASSWORD": PW_MASTER,
    "EDITOR_USER": EDITOR_USER, "EDITOR_PASSWORD": PW_EDITOR,
    "CLAUDE_USER": CLAUDE_USER, "CLAUDE_PASSWORD": PW_CLAUDE,
    "POSTGREST_JWT_SECRET": JWT,
    "SYNTHESIS_WHITELIST": syn_whitelist, "SYNTHESIS_TABLES": syn_tables,
    "CUSTOM_GATES": custom_gates, "TTS_PROVIDER_NOTES": tts_provider_notes,
    # canary -> Standards placeholders
    "PASSIVE_VOICE": str(CANARY["passive_voice"]),
    "EMOTION_TELLS": str(CANARY["emotion_tells"]),
    "WEAK_ADVERBS": str(CANARY["weak_adverbs_per_1k"]),
    "SENTENCE_VARIETY": str(CANARY["sentence_variety_std_dev"]),
    "COMPLEX_PARAGRAPHS": str(CANARY["complex_paragraphs"]),
    "FK_GRADE": str(CANARY["readability_fk_grade"]),
    "GLUE_INDEX": str(CANARY["glue_index"]),
}

def sub(text):
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: REPL.get(m.group(1), m.group(0)), text)

def strip_block(text, start, end):
    return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.DOTALL)

# ---- file map: (template rel path, output rel path) ------------------------
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
    ("nginx/html/notes-editor.html", "nginx/html/notes-editor.html"),
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
if TTS:
    FILES.append(("prompts/TTS-Prep.md.tmpl", "prompts/TTS-Prep.md"))

written = []
for src, dst in FILES:
    text = (TPL / src).read_text(encoding="utf-8")
    if dst == "nginx/html/character-editor.html" and not TTS:
        text = strip_block(text, "<!-- TTS_BLOCK_START -->", "<!-- TTS_BLOCK_END -->")
        text = strip_block(text, "// TTS_PAYLOAD_START", "// TTS_PAYLOAD_END")
    out = sub(text)
    (PROJECT_PATH / dst).write_text(out, encoding="utf-8")
    written.append(dst)

# ---- intake CSVs verbatim --------------------------------------------------
for f in ["characters.csv", "locations.csv", "groups.csv", "chapters.csv", "README.txt"]:
    shutil.copyfile(TPL / "intake" / f, PROJECT_PATH / "intake" / f)
    written.append("intake/" + f)

# ---- leftover-placeholder audit -------------------------------------------
leftovers = {}
for dst in written:
    if dst.endswith((".csv", ".txt", ".png")):
        continue
    t = (PROJECT_PATH / dst).read_text(encoding="utf-8", errors="ignore")
    hits = set(re.findall(r"\{\{[A-Z_]+\}\}", t))
    if hits:
        leftovers[dst] = sorted(hits)

print("WROTE", len(written), "files +", "project.json/.env/.env.example/.gitignore")
print("PW_MASTER", PW_MASTER)
print("PW_EDITOR", PW_EDITOR)
print("PW_CLAUDE", PW_CLAUDE)
if leftovers:
    print("LEFTOVER_PLACEHOLDERS", json.dumps(leftovers, indent=2))
else:
    print("LEFTOVER_PLACEHOLDERS none")
