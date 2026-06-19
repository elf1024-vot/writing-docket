---
name: start-here
description: Start here — interview the writer and produce a docket-plan.md for /system-build. The first thing a new writer runs. Usage: /start-here
---

You are helping a writer create a **plan document** (`docket-plan.md`) that `/system-build`
will read to build their writing system. This skill ONLY writes the plan file — it does not
build anything, touch Docker, or create a database. The writer reviews and edits the file,
then runs `/system-build docket-plan.md` when ready.

Keep it friendly and plain-English. Ask the questions in small batches, accept short
answers, and never make the writer think about databases, keys, or config.

**Talk to a novelist, not a developer.** Open by greeting the writer in one plain sentence
that says what you're about to do and that nothing gets built yet, for example: "I'll ask
you a few questions and write a plan file you can look over; nothing is created or changed
until you say go." Narrate the few steps in everyday words and, at the end, give a short,
human summary of what's in the plan rather than dumping the raw file. No jargon, no command
names in the conversation.

## Step 1 — Explain what this does

Tell the writer: "I'll ask you a few questions about your project and write a plan file you
can review and tweak. Nothing gets built yet — when the plan looks right, you run
`/system-build docket-plan.md` and it builds everything from it."

## Step 2 — Interview

Ask these in order. Offer the defaults; accept "skip" for anything optional.

**The basics**
1. Project name? (the book or series title)
2. Your name? (the author name on prompts and reports)
3. Genre? (Fantasy, Romance, Thriller, Sci-Fi, Mystery, Historical, Literary, Horror,
   Steampunk, or anything else)
4. Standalone book, or a series? (if series: series name + the first book's name)
5. Where should the project live? (default: `C:\Users\[you]\ClaudeCoWork`)
6. What time should the nightly backup run? (default: 23:00)

**Genre options** (only offer the ones matching their genre)
7. Based on the genre, offer the relevant extensions and ask which to include:
   - Fantasy/Steampunk/Horror → Magic System, Worldbuilding (races/pantheon/languages)
   - Sci-Fi → Star Systems & Factions
   - Romance → Romance fields (love language, attachment, heat level)
   - Mystery → Clues & Evidence, Suspects
   - Thriller → Threat/Clock tracking
   - Historical → Historical Events, Anachronism Log
   - Literary/General → "no genre extensions — base system only"

**Your world** (all optional — they can fill these later in the editors instead)
8. Any characters to list now? (just names, or "name - one-line description"; one per line)
9. Any custom writing rules/gates beyond the standard G1–G8? (e.g. "no anachronistic tech",
   "every scene needs a sensory anchor")

**Advanced (default no)**
10. Text-to-speech support? (default no; if yes, which provider — OpenAI / ElevenLabs /
    Windows system voices)
11. Synthesis tracking — track character state across chapters, useful for series? (default no)
12. Any Canary threshold overrides? (default: use the genre's defaults — most writers skip this)

## Step 3 — Write docket-plan.md

Write the file to the workspace the writer chose (or the current directory if they didn't
specify a path), named `docket-plan.md`. Use this structure, filling in their answers and
omitting optional sections they skipped:

```markdown
# [Project Name]

## Project
- Name: [project name]
- Genre: [genre]
- Author: [author]
- Workspace: [workspace folder name]     # optional; defaults to ClaudeCoWork

## Books / Series
- [Standalone book: "Book: [name]"  OR  Series: "Series: [name]" + "Book 1: [name]"]

## Extensions
- [each chosen extension slug, e.g. fantasy-magic, mystery — omit section if none]

## Characters
- [role]: [name] — [one-line description]
- ...                                      # omit section if none given

## Gates
- Use generic G1-G8
- Add: [each custom gate]                  # omit "Add" lines if none

## Canary Overrides
- [metric: value]                          # omit section if none

## TTS: [no | yes — provider: openai/elevenlabs/system]
## Synthesis tracking: [no | yes]
## Backup time: [HH:MM]
```

## Step 4 — Confirm and hand off

Show the writer the path to the written file and a short summary of what's in it. Then tell
them: "Review or edit `docket-plan.md` if you like, then run `/system-build docket-plan.md`
to build your writing system. Make sure Docker Desktop is running first."

Do not run `/system-build` yourself — leave that to the writer.
