#!/usr/bin/env python3
"""
word_count.py — Scan Chapters/ folder and update chapter word counts in the DB.

Usage:
  python word_count.py               # scan all chapters
  python word_count.py --chapter 3   # scan Chapter-3.md
  python word_count.py --chapter 3 --part 2  # scan Chapter-3-Part-2.md

Reads project.json and .env for configuration.
"""

import re
import os
import sys
import json
import argparse
from pathlib import Path

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

def count_words(filepath: Path) -> int:
    """Count words in a markdown file, excluding frontmatter, headers, code blocks."""
    text = filepath.read_text(encoding="utf-8")
    # Remove YAML frontmatter
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", "", text)
    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    # Remove markdown links/images
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    # Count words
    words = text.split()
    return len(words)

def find_chapter_files(chapters_dir: Path, chapter_num=None, part_num=None):
    """Find chapter markdown files matching the given filter."""
    results = []
    pattern = re.compile(r"Chapter-(\d+)(?:-Part-(\d+))?\.md", re.IGNORECASE)
    for f in chapters_dir.glob("*.md"):
        m = pattern.match(f.name)
        if m:
            ch = int(m.group(1))
            pt = int(m.group(2)) if m.group(2) else 1
            if chapter_num is not None and ch != chapter_num:
                continue
            if part_num is not None and pt != part_num:
                continue
            results.append((ch, pt, f))
    return sorted(results)

def update_word_count(schema: str, book: str, chapter_num: int, part_num: int, word_count: int,
                      host: str, port: int, dbname: str, user: str, password: str):
    """Update word_count in the chapters table."""
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {schema}.chapters SET word_count = %s, last_modified = NOW() "
                f"WHERE book = %s AND chapter = %s AND part = %s",
                (word_count, book, chapter_num, part_num)
            )
            if cur.rowcount == 0:
                print(f"  WARNING: No chapter row found for {book} Ch{chapter_num} Pt{part_num}")
            conn.commit()
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Update chapter word counts.")
    parser.add_argument("--chapter", type=int, default=None, help="Chapter number")
    parser.add_argument("--part", type=int, default=None, help="Part number (default 1)")
    args = parser.parse_args()

    project, project_path = load_project()
    env = load_env(project_path)

    schema = project["schema"]
    book = project["book_name"]
    chapters_dir = project_path / "Chapters"

    if not chapters_dir.exists():
        print(f"Chapters directory not found at {chapters_dir}")
        sys.exit(1)

    db_config = {
        "host": "127.0.0.1",
        "port": 5432,
        "dbname": env.get("POSTGRES_DB", schema),
        "user": env.get("CLAUDE_USER", "docket_claude"),
        "password": env.get("CLAUDE_PASSWORD", ""),
    }

    files = find_chapter_files(chapters_dir, args.chapter, args.part)
    if not files:
        print("No matching chapter files found.")
        sys.exit(0)

    print(f"Updating word counts for {len(files)} file(s)...")
    for ch, pt, filepath in files:
        wc = count_words(filepath)
        label = f"Chapter-{ch}" + (f"-Part-{pt}" if pt > 1 else "")
        print(f"  {label}: {wc:,} words")
        update_word_count(schema, book, ch, pt, wc, **db_config)
    print("Done.")

if __name__ == "__main__":
    main()
