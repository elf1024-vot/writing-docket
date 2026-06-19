#!/usr/bin/env python3
"""
embed.py — build the unified search index (full-text + semantic vectors).

Reads the base tables and the Chapters/ prose files, writes one row per entity
into <schema>.search_index, and (when Ollama is reachable) fills the 768-dim
embedding column via the local nomic-embed-text model.

Full-text search needs nothing from this script — the search_index.tsv column is
GENERATED in the database, so FTS works the instant a row is written. This script
adds the semantic layer on top and is safe to run repeatedly: unchanged rows
(matched by a sha256 content hash) are skipped.

Graceful degradation: if Ollama is unreachable, rows are still upserted (title,
body, content_hash) so FTS covers them; the embedding is left NULL and a warning
is printed. Re-run once Ollama is up to fill the missing vectors.

Usage:
  python embed.py                 # --full (default): index everything
  python embed.py --full          # rebuild/refresh all rows
  python embed.py --since-edits   # only rows whose body hash changed
  python embed.py --ollama-url http://127.0.0.1:11434
  python embed.py --model nomic-embed-text

Reads project.json (walking up from cwd) and .env (like word_count.py).
Connects as the EDITOR role, which has CRUD on search_index.
Pure stdlib + psycopg2.
"""

import re
import os
import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.error
from pathlib import Path


# ── Config loading (mirrors word_count.py) ─────────────────────────────────────

def load_project():
    """Find and load project.json walking up from cwd."""
    path = Path.cwd()
    while path != path.parent:
        candidate = path / "project.json"
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f), path
        path = path.parent
    raise FileNotFoundError("project.json not found in current directory or any parent.")


def load_env(project_path: Path) -> dict:
    env = {}
    env_file = project_path / ".env"
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


# ── Markdown stripping (carried from canary.py) ────────────────────────────────

def strip_markdown(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)   # YAML frontmatter
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)          # code fences
    text = re.sub(r"`[^`]+`", "", text)                             # inline code
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)   # headers
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)                     # images
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)                 # links -> text
    return re.sub(r"\s+", " ", text).strip()


def join_fields(*parts) -> str:
    """Join non-empty text fields with a separator into one body string."""
    return "\n".join(str(p).strip() for p in parts if p and str(p).strip())


# ── Ollama embedding (stdlib HTTP) ─────────────────────────────────────────────

def get_embedding(body: str, ollama_url: str, model: str):
    """Return a list[float] embedding, or None if Ollama is unreachable/errors."""
    url = ollama_url.rstrip("/") + "/api/embeddings"
    payload = json.dumps({"model": model, "prompt": body}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        emb = data.get("embedding")
        if not emb:
            return None
        return emb
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return None


def vector_literal(emb) -> str:
    """Format a list of floats as a pgvector literal: '[v1,v2,...]'."""
    return "[" + ",".join(repr(float(x)) for x in emb) + "]"


# ── Corpus building ────────────────────────────────────────────────────────────

def build_corpus(cur, schema: str, book: str, project_path: Path):
    """Return a list of (entity_type, entity_key, title, body) tuples."""
    items = []

    # characters
    cur.execute(
        f"SELECT name, display_name, role, background, arc, dialogue_prompt, "
        f"image_prompt, notes FROM {schema}.characters"
    )
    for (name, display_name, role, background, arc, dialogue_prompt,
         image_prompt, notes) in cur.fetchall():
        body = join_fields(display_name, role, background, arc,
                           dialogue_prompt, image_prompt, notes)
        items.append(("character", name, name, body))

    # locations
    cur.execute(
        f"SELECT location_id, display_name, type, region, exterior_desc, "
        f"interior_desc, sensory, notes FROM {schema}.locations"
    )
    for (location_id, display_name, type_, region, exterior_desc,
         interior_desc, sensory, notes) in cur.fetchall():
        body = join_fields(type_, region, exterior_desc, interior_desc,
                           sensory, notes)
        items.append(("location", location_id, display_name or location_id, body))

    # groups
    cur.execute(
        f"SELECT group_id, display_name, type, purpose, membership_notes, notes "
        f"FROM {schema}.groups"
    )
    for (group_id, display_name, type_, purpose, membership_notes,
         notes) in cur.fetchall():
        body = join_fields(type_, purpose, membership_notes, notes)
        items.append(("group", group_id, display_name or group_id, body))

    # chapters
    cur.execute(
        f"SELECT book, chapter, part, summary FROM {schema}.chapters"
    )
    for (b, chapter, part, summary) in cur.fetchall():
        key = f"{b}|{chapter}|{part}"
        title = f"Ch {chapter}.{part}"
        items.append(("chapter", key, title, join_fields(summary)))

    # notes
    cur.execute(f"SELECT note_id, scope, body FROM {schema}.notes")
    for (note_id, scope, body) in cur.fetchall():
        items.append(("note", str(note_id), scope, join_fields(body)))

    # chapter prose files: Chapters/**/*.md
    chapters_dir = project_path / "Chapters"
    if chapters_dir.exists():
        for md in sorted(chapters_dir.glob("**/*.md")):
            try:
                raw = md.read_text(encoding="utf-8")
            except OSError:
                continue
            body = strip_markdown(raw)
            if not body:
                continue
            items.append(("chapter_prose", md.stem, md.stem, body))

    return items


# ── Indexing ───────────────────────────────────────────────────────────────────

def index_item(cur, schema, entity_type, entity_key, title, body,
               since_edits, ollama_url, model, stats):
    body = body or ""
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    cur.execute(
        f"SELECT content_hash, embedding IS NOT NULL FROM {schema}.search_index "
        f"WHERE entity_type = %s AND entity_key = %s",
        (entity_type, entity_key),
    )
    existing = cur.fetchone()
    if existing is not None:
        old_hash, has_embedding = existing
        if old_hash == content_hash and has_embedding:
            stats["skipped"] += 1
            return

    # Upsert title/body/content_hash (do NOT clobber embedding here).
    cur.execute(
        f"INSERT INTO {schema}.search_index "
        f"(entity_type, entity_key, title, body, content_hash, updated_at) "
        f"VALUES (%s, %s, %s, %s, %s, now()) "
        f"ON CONFLICT (entity_type, entity_key) DO UPDATE SET "
        f"title = EXCLUDED.title, body = EXCLUDED.body, "
        f"content_hash = EXCLUDED.content_hash, updated_at = now()",
        (entity_type, entity_key, title, body, content_hash),
    )
    stats["indexed"] += 1

    if not body.strip():
        return

    emb = get_embedding(body, ollama_url, model)
    if emb is None:
        stats["ollama_down"] += 1
        return
    cur.execute(
        f"UPDATE {schema}.search_index SET embedding = %s::vector "
        f"WHERE entity_type = %s AND entity_key = %s",
        (vector_literal(emb), entity_type, entity_key),
    )
    stats["embedded"] += 1


def main():
    parser = argparse.ArgumentParser(description="Build the search index (FTS + vectors).")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--full", action="store_true",
                   help="Rebuild/refresh all rows (default).")
    g.add_argument("--since-edits", action="store_true",
                   help="Only process rows whose body hash changed.")
    parser.add_argument("--ollama-url", default=None,
                        help="Ollama base URL (default from project.json or http://127.0.0.1:11434)")
    parser.add_argument("--model", default=None,
                        help="Embedding model (default from project.json or nomic-embed-text)")
    args = parser.parse_args()

    project, project_path = load_project()
    env = load_env(project_path)

    schema = project["schema"]
    book = project.get("book_name", project.get("project_name", ""))

    search_cfg = project.get("search", {})
    ollama_url = args.ollama_url or search_cfg.get("ollama_url", "http://127.0.0.1:11434")
    model = args.model or search_cfg.get("embedding_model", "nomic-embed-text")

    # --since-edits and --full share the same hash-skip logic; --since-edits is the
    # explicit name for "only changed". Default (neither flag) behaves as --full.
    since_edits = bool(args.since_edits)

    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    db_config = {
        "host": "127.0.0.1",
        "port": 5432,
        "dbname": env.get("POSTGRES_DB", schema),
        "user": env.get("EDITOR_USER", "docket_editor"),
        "password": env.get("EDITOR_PASSWORD", ""),
    }

    conn = psycopg2.connect(**db_config)
    stats = {"indexed": 0, "embedded": 0, "skipped": 0, "ollama_down": 0}
    try:
        with conn.cursor() as cur:
            corpus = build_corpus(cur, schema, book, project_path)
            print(f"Found {len(corpus)} entities to index "
                  f"(model={model}, ollama={ollama_url}).")
            for (entity_type, entity_key, title, body) in corpus:
                index_item(cur, schema, entity_type, entity_key, title, body,
                           since_edits, ollama_url, model, stats)
            conn.commit()
    finally:
        conn.close()

    print("Done.")
    print(f"  rows indexed : {stats['indexed']}")
    print(f"  embedded     : {stats['embedded']}")
    print(f"  skipped      : {stats['skipped']}")
    if stats["ollama_down"]:
        print(f"  ollama-down  : {stats['ollama_down']} "
              f"(embeddings left NULL; FTS still works. Re-run once Ollama is up.)")


if __name__ == "__main__":
    main()
