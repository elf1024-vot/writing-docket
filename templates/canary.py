#!/usr/bin/env python3
"""
canary.py — deterministic prose-metric scanner for the writing system.

Computes the seven Canary metrics declared in Standards.md against a chapter
file, compares each to the project's thresholds (from project.json), and emits
JSON. The QR workflow RUNS this script and reads the result — it never estimates
the numbers by eye. Same input always yields the same output.

This is a self-contained, dependency-free port of the VoT canary tokenizer,
trimmed to the seven metrics the writing system scores. The detector algorithms
and word lists are carried over verbatim so results match the parent system.

Metrics:
  1. passive_voice          — % of sentences with a passive construction
  2. emotion_tells          — % of sentences that name an emotion via a filter verb
  3. weak_adverbs_per_1k    — -ly adverbs adjacent to weak/tag verbs, per 1000 words
  4. sentence_variety_std_dev — std dev of sentence length (higher = more varied)
  5. complex_paragraphs     — % of paragraphs that are long AND dense
  6. readability_fk_grade   — Flesch-Kincaid grade level
  7. glue_index             — % of words that are structural "glue"

Usage:
  python canary.py --file "Chapters/Chapter 01/Chapter-01.md"
  python canary.py --file <path> --json        # machine-readable only
Reads project.json (walking up from cwd) for canary_thresholds.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

# ── Word lists (carried from the parent canary tokenizer) ──────────────────────

WEAK_VERBS = {
    "said", "asked", "replied", "answered", "whispered", "shouted", "cried",
    "gasped", "sighed", "went", "walked", "ran", "looked", "saw", "heard",
    "was", "were", "felt", "moved", "turned", "reached", "opened", "closed",
    "stood", "sat", "came", "got", "put", "took",
}
INVISIBLE_TAGS = {"said", "asked", "replied", "answered", "added", "continued", "began"}
PERFORMANCE_TAGS = {
    "whispered", "hissed", "murmured", "growled", "snarled", "barked", "spat",
    "gasped", "breathed", "sighed", "laughed", "cried", "yelled", "shouted",
    "screamed", "bellowed", "mumbled", "muttered", "called", "stammered",
    "croaked", "rasped", "purred", "drawled", "snapped",
}
FILTER_VERBS = {
    "felt", "feels", "feeling", "was", "were", "is", "am", "are", "seemed",
    "looked", "watched", "heard", "saw", "noticed", "noted", "realized",
    "thought", "wondered", "decided", "knew", "understood", "considered",
    "believed", "assumed", "pondered", "perceived",
}
EMOTION_WORDS = {
    "sad", "happy", "angry", "afraid", "scared", "terrified", "nervous",
    "anxious", "excited", "relieved", "embarrassed", "ashamed", "guilty",
    "proud", "jealous", "confused", "surprised", "shocked", "disgusted",
    "tired", "exhausted", "bored", "frustrated", "furious", "calm", "content",
    "lonely", "worried", "hopeful", "hopeless", "desperate", "helpless",
    "overwhelmed", "numb", "empty", "hollow", "cold", "hot", "dizzy", "sick",
    "weak",
}
GLUE_WORDS = {
    "of", "in", "to", "for", "and", "the", "a", "is", "was", "it", "that",
    "this", "with", "as", "but", "on", "at", "by",
    "be", "been", "being", "am", "are", "were", "do", "does", "did",
    "have", "has", "had", "shall", "should", "will", "would", "may", "might",
    "must", "can", "could",
}
TO_BE = {"is", "was", "were", "are", "am", "be", "been", "being"}
IRREGULAR_PARTICIPLES = {
    "taken", "given", "broken", "spoken", "written", "stolen", "frozen",
    "chosen", "forgotten", "hidden", "ridden", "shown", "thrown", "drawn",
    "known", "grown", "blown", "gone", "done", "seen", "made", "held",
    "told", "said", "found", "left", "kept", "felt", "heard", "brought",
    "caught", "taught", "bought", "thought", "fought", "got", "had", "put",
    "set", "cut", "hit", "let", "shut", "spent", "sent", "lost", "built",
    "burned", "burnt",
}

SENTENCE_SPLIT = re.compile(r"(?<=[.!?”\"\'])\s+(?=[A-Z\"“(])")

DEFAULT_THRESHOLDS = {
    "passive_voice": 12,
    "emotion_tells": 10,
    "weak_adverbs_per_1k": 6.0,
    "sentence_variety_std_dev": 5.5,
    "complex_paragraphs": 8,
    "readability_fk_grade": 8,
    "glue_index": 38,
}

# ── Markdown stripping (frontmatter, headers, code, links) ─────────────────────

def strip_markdown(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)   # YAML frontmatter
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)          # code fences
    text = re.sub(r"`[^`]+`", "", text)                             # inline code
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)   # headers
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)                     # images
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)                 # links → text
    return text


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def split_sentences(paragraph: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", paragraph).strip()
    if not normalized:
        return []
    return [p.strip() for p in SENTENCE_SPLIT.split(normalized) if p.strip()]


def words_in(text: str) -> list[str]:
    return re.findall(r"\b[\w'’-]+\b", text)


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?\"'“”-")
    if not word:
        return 0
    vowels, count, prev = "aeiouy", 0, False
    for ch in word:
        v = ch in vowels
        if v and not prev:
            count += 1
        prev = v
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def looks_like_past_participle(token: str) -> bool:
    t = token.lower().strip(".,;:!?\"'“”")
    if t in IRREGULAR_PARTICIPLES:
        return True
    if t.endswith("ed") and len(t) > 3:
        return True
    if t.endswith("en") and len(t) > 3:
        return True
    return False

# ── Detectors (verbatim logic from the parent tokenizer) ───────────────────────

def compute(text: str) -> dict:
    paragraphs = split_paragraphs(text)
    sentences_by_para = [split_sentences(p) for p in paragraphs]
    sent_lengths, total_words, syllables = [], 0, 0
    for sents in sentences_by_para:
        for s in sents:
            ws = words_in(s)
            sent_lengths.append(len(ws))
            total_words += len(ws)
            syllables += sum(count_syllables(w) for w in ws)

    sent_count = len(sent_lengths)
    avg_len = sum(sent_lengths) / sent_count if sent_count else 0.0
    if sent_count > 1:
        variance = sum((x - avg_len) ** 2 for x in sent_lengths) / (sent_count - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0
    fk = (0.39 * (total_words / sent_count) + 11.8 * (syllables / total_words) - 15.59
          if sent_count and total_words else 0.0)

    # Passive voice — TO_BE + past participle, one per sentence.
    passive = 0
    for sents in sentences_by_para:
        for s in sents:
            ws = words_in(s)
            for i in range(len(ws) - 1):
                if ws[i].lower() in TO_BE and looks_like_past_participle(ws[i + 1]):
                    passive += 1
                    break

    # Emotion tells — subject + filter verb + emotion word.
    pronouns = {"he", "she", "they", "i", "we"}
    emo = 0
    for sents in sentences_by_para:
        for s in sents:
            ws = words_in(s)
            hit = False
            for i in range(len(ws) - 2):
                subj_ok = ws[i].lower() in pronouns or (ws[i][:1].isupper() and ws[i].isalpha())
                if subj_ok and ws[i + 1].lower() in FILTER_VERBS and ws[i + 2].lower() in EMOTION_WORDS:
                    hit = True
                    break
            if hit:
                emo += 1

    # Weak adverbs — -ly adjacent to a weak or tag verb.
    tag_verbs = INVISIBLE_TAGS | PERFORMANCE_TAGS
    weak = 0
    for sents in sentences_by_para:
        for s in sents:
            ws = words_in(s)
            for i, w in enumerate(ws):
                lw = w.lower()
                if not lw.endswith("ly") or len(lw) <= 3:
                    continue
                adj = False
                if i > 0 and ws[i - 1].lower() in (tag_verbs | WEAK_VERBS):
                    adj = True
                elif i + 1 < len(ws) and ws[i + 1].lower() in (tag_verbs | WEAK_VERBS):
                    adj = True
                if adj:
                    weak += 1

    # Complex paragraphs — >3 sentences AND avg sentence length >20 words.
    complex_count = 0
    for p, sents in zip(paragraphs, sentences_by_para):
        if len(sents) <= 3:
            continue
        lens = [len(words_in(s)) for s in sents]
        if lens and sum(lens) / len(lens) > 20:
            complex_count += 1

    # Glue index.
    all_words = [w.lower() for w in words_in(text)]
    glue = sum(1 for w in all_words if w in GLUE_WORDS)

    pct = lambda n, d: round(100 * n / d, 2) if d else 0.0
    return {
        "word_count": total_words,
        "sentence_count": sent_count,
        "paragraph_count": len(paragraphs),
        "metrics": {
            "passive_voice": pct(passive, sent_count),
            "emotion_tells": pct(emo, sent_count),
            "weak_adverbs_per_1k": round(1000 * weak / total_words, 2) if total_words else 0.0,
            "sentence_variety_std_dev": round(stddev, 2),
            "complex_paragraphs": pct(complex_count, len(paragraphs)),
            "readability_fk_grade": round(fk, 2),
            "glue_index": pct(glue, len(all_words)),
        },
    }

# ── Threshold comparison ───────────────────────────────────────────────────────
# Most metrics PASS when the value is BELOW the threshold (less passive voice is
# better). Sentence variety is the exception: higher is better, so it PASSES when
# the value is AT OR ABOVE the threshold.

HIGHER_IS_BETTER = {"sentence_variety_std_dev"}


def evaluate(metrics: dict, thresholds: dict) -> dict:
    results = {}
    passed = 0
    for key, value in metrics.items():
        limit = thresholds.get(key, DEFAULT_THRESHOLDS.get(key))
        if key in HIGHER_IS_BETTER:
            ok = value >= limit
            direction = ">="
        else:
            ok = value < limit
            direction = "<"
        results[key] = {"value": value, "threshold": limit, "direction": direction, "pass": ok}
        if ok:
            passed += 1
    results["_summary"] = {
        "metrics_passed": passed,
        "metrics_total": len(metrics),
        "pct_passed": round(100 * passed / len(metrics), 1) if metrics else 0.0,
    }
    return results


def load_thresholds() -> dict:
    path = Path.cwd()
    while path != path.parent:
        candidate = path / "project.json"
        if candidate.exists():
            with open(candidate, encoding="utf-8") as f:
                proj = json.load(f)
            return {**DEFAULT_THRESHOLDS, **proj.get("canary_thresholds", {})}
        path = path.parent
    return dict(DEFAULT_THRESHOLDS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic Canary prose-metric scanner.")
    ap.add_argument("--file", required=True, help="Chapter file (.md or .txt).")
    ap.add_argument("--json", action="store_true", help="Emit JSON only (no table).")
    args = ap.parse_args(argv)

    fp = Path(args.file)
    if not fp.exists():
        print(f"File not found: {fp}", file=sys.stderr)
        return 1

    raw = fp.read_text(encoding="utf-8")
    data = compute(strip_markdown(raw))
    thresholds = load_thresholds()
    evaluation = evaluate(data["metrics"], thresholds)

    out = {
        "file": str(fp),
        "word_count": data["word_count"],
        "sentence_count": data["sentence_count"],
        "paragraph_count": data["paragraph_count"],
        "canary": evaluation,
    }

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print(f"Canary - {fp.name}")
    print(f"  {data['word_count']} words, {data['sentence_count']} sentences, "
          f"{data['paragraph_count']} paragraphs\n")
    print(f"  {'Metric':<26}{'Value':>9}  {'Threshold':>11}  Result")
    print(f"  {'-'*26}{'-'*9}  {'-'*11}  ------")
    labels = {
        "passive_voice": "Passive voice %",
        "emotion_tells": "Emotion tells %",
        "weak_adverbs_per_1k": "Weak adverbs /1k",
        "sentence_variety_std_dev": "Sentence variety (sd)",
        "complex_paragraphs": "Complex paragraphs %",
        "readability_fk_grade": "Readability (FK)",
        "glue_index": "Glue index %",
    }
    for key, label in labels.items():
        r = evaluation[key]
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"  {label:<26}{r['value']:>9}  {r['direction']+' '+str(r['threshold']):>11}  {mark}")
    s = evaluation["_summary"]
    print(f"\n  {s['metrics_passed']}/{s['metrics_total']} metrics passed "
          f"({s['pct_passed']}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
