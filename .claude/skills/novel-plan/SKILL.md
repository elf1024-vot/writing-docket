---
name: novel-plan
description: Load scene planning context from the project database. Usage: /novel-plan [chapter] [part]
---

You are loading scene planning context for a writing session. This is a wrapper that loads data and then hands off to the Planning.md prompt.

## Step 1 — Load project context

Read project.json from current directory (or search upward for it). Load all fields.

## Step 2 — Identify target chapter

If chapter and part were passed as arguments (e.g. `/novel-plan 5 2`), use them.
Otherwise ask: "Which chapter are you planning? (Enter chapter number, and part number if applicable)"

## Step 3 — Load planning data from DB

Connect via the MCP tool (tool name is the project_slug) or via docker exec psql.

Run these queries:

The active book name is in project.json as `book_name` — use it for `[BOOK]` below.

```sql
-- Chapter metadata
SELECT c.*, l.display_name as location_name
FROM {{SCHEMA}}.chapters c
LEFT JOIN {{SCHEMA}}.locations l ON c.location = l.location_id
WHERE c.book = '[BOOK]' AND c.chapter = [N];

-- Cast for this chapter
SELECT char.*
FROM {{SCHEMA}}.characters char
JOIN {{SCHEMA}}.chapter_cast cc ON char.name = cc.character_id
WHERE cc.chapter_id = (SELECT chapter_id FROM {{SCHEMA}}.chapters WHERE book = '[BOOK]' AND chapter = [N]);

-- Open threads (if synthesis enabled)
SELECT * FROM {{SCHEMA}}.open_threads WHERE status = 'open' ORDER BY thread_id LIMIT 10;

-- HIGH notes scoped to this chapter or project-wide
SELECT * FROM {{SCHEMA}}.notes WHERE priority = 'HIGH' AND status = 'open'
  AND (scope = 'project' OR (scope = 'chapter' AND chapter = [N])) ORDER BY created_at;

-- Recent QR scores
SELECT chapter, summary, qr FROM {{SCHEMA}}.chapters 
  WHERE book = '[BOOK]' AND qr IS NOT NULL ORDER BY chapter DESC LIMIT 5;
```

## Step 4 — Read the Planning prompt

Read the full content of prompts/Planning.md from the project directory.

## Step 5 — Deliver scene brief

Using the loaded data and the Planning.md instructions, deliver a structured scene brief:

```
═══════════════════════════════════════════════════════════
  Scene Brief — Chapter [N][, Part P]
═══════════════════════════════════════════════════════════
  Chapter:  [N][, Part P]
  POV:      [pov_char]
  Location: [location]
  Status:   [status]

  Summary:
  [chapter summary]

  Cast in scene:
  [character list with brief role notes]

  Open threads relevant to this chapter:
  [thread list if synthesis enabled]

  HIGH notes:
  [note list]

  Recent QR trend:
  Ch[N-2]: [score]  Ch[N-1]: [score]  Ch[N]: [score or "not yet scored"]

  Planning prompt follows:
═══════════════════════════════════════════════════════════

[Planning.md content]
```
