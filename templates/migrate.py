#!/usr/bin/env python3
"""
migrate.py — Run schema migrations for writing-docket.

Usage:
  python migrate.py --from 1.0 --to 1.1
  python migrate.py --list
  python migrate.py --status

Migrations are in the migrations/ directory of the skills repo.
Each migration file is named: vX.Y-description.sql
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path

def load_project():
    path = Path.cwd()
    while path != path.parent:
        candidate = path / "project.json"
        if candidate.exists():
            with open(candidate) as f:
                return json.load(f), path
        path = path.parent
    raise FileNotFoundError("project.json not found.")

def load_env(project_path: Path) -> dict:
    env = {}
    with open(project_path / ".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def find_migrations_dir():
    """Find the migrations/ directory in the skills repo."""
    # This script lives in scripts/ under the project dir.
    # The skills repo is found via claude skill list or by env var WRITING_DOCKET_REPO.
    repo = os.environ.get("WRITING_DOCKET_REPO")
    if repo:
        m = Path(repo) / "migrations"
        if m.exists():
            return m
    # Fallback: look for it next to the templates dir (common install patterns)
    script_dir = Path(__file__).parent
    for candidate in [
        script_dir.parent / "migrations",
        Path.home() / ".claude" / "skills" / "writing-docket" / "migrations",
    ]:
        if candidate.exists():
            return candidate
    return None

def parse_version(v: str) -> tuple:
    parts = v.lstrip("v").split(".")
    return tuple(int(p) for p in parts)

def version_str(t: tuple) -> str:
    return ".".join(str(p) for p in t)

def get_migrations(migrations_dir: Path):
    pattern = re.compile(r"v(\d+\.\d+)-.*\.sql")
    migrations = []
    for f in migrations_dir.glob("v*.sql"):
        m = pattern.match(f.name)
        if m:
            migrations.append((parse_version(m.group(1)), f))
    return sorted(migrations, key=lambda x: x[0])

def run_migration(sql_file: Path, schema: str, env: dict):
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed.")
        sys.exit(1)
    sql = sql_file.read_text(encoding="utf-8")
    sql = sql.replace("{{SCHEMA}}", schema)
    conn = psycopg2.connect(
        host="127.0.0.1", port=5432,
        dbname=env.get("POSTGRES_DB", schema),
        user=env.get("POSTGRES_USER"),
        password=env.get("POSTGRES_PASSWORD")
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print(f"  Applied: {sql_file.name}")
    except Exception as e:
        conn.rollback()
        print(f"  FAILED: {sql_file.name}: {e}")
        raise
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Run writing-docket schema migrations.")
    parser.add_argument("--from", dest="from_ver", help="Current schema version")
    parser.add_argument("--to", dest="to_ver", help="Target schema version")
    parser.add_argument("--list", action="store_true", help="List available migrations")
    parser.add_argument("--status", action="store_true", help="Show current schema version")
    args = parser.parse_args()

    project, project_path = load_project()
    env = load_env(project_path)
    schema = project["schema"]
    current_ver = project.get("schema_version", "1.0")

    migrations_dir = find_migrations_dir()
    if not migrations_dir:
        print("Could not find migrations directory. Set WRITING_DOCKET_REPO env var.")
        sys.exit(1)

    migrations = get_migrations(migrations_dir)

    if args.list:
        print("Available migrations:")
        for ver, f in migrations:
            print(f"  v{version_str(ver)} — {f.name}")
        return

    if args.status:
        print(f"Current schema version: {current_ver}")
        return

    from_ver = parse_version(args.from_ver or current_ver)
    to_ver = parse_version(args.to_ver or version_str(migrations[-1][0]) if migrations else current_ver)

    applicable = [(v, f) for v, f in migrations if from_ver < v <= to_ver]
    if not applicable:
        print(f"No migrations to apply from v{version_str(from_ver)} to v{version_str(to_ver)}.")
        return

    print(f"Applying {len(applicable)} migration(s)...")
    for ver, f in applicable:
        run_migration(f, schema, env)

    # Update project.json
    project["schema_version"] = version_str(to_ver)
    with open(project_path / "project.json", "w") as pf:
        json.dump(project, pf, indent=2)
    print(f"Schema version updated to {version_str(to_ver)}.")

if __name__ == "__main__":
    main()
