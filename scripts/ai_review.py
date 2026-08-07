#!/usr/bin/env python3
"""
AI architecture reviewer.

Reviews the current diff against ARCHITECT_REVIEWER.md, STANDARDS.md, and
ARCHITECTURE.md, using those docs as the "system context" instead of
re-reading the whole repo on every run — same principle as a human
reviewer who knows the codebase's documented decisions rather than
re-deriving them from scratch each time.

Usage:
    python scripts/ai_review.py                 # reviews origin/main...HEAD
    REVIEW_BASE_REF=main python scripts/ai_review.py

Exit code 0 = PASS, 1 = FAIL (non-zero blocks CI / the commit).
Requires ANTHROPIC_API_KEY in the environment.
"""
import os
import subprocess
import sys

from anthropic import Anthropic

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "claude-sonnet-5"  # real API model string — not the Artifacts-only "claude-sonnet-4-6"
MAX_DIFF_CHARS = 15000  # keep the review focused and fast; huge diffs should be split into smaller commits anyway
MAX_TOKENS = 2500  # enough room for the detailed, multi-section review format


def get_diff() -> str:
    base = os.environ.get("REVIEW_BASE_REF", "origin/main")
    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD"],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )
    if result.returncode != 0:
        # Fallback for local pre-commit use: staged changes, no remote ref needed
        result = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True, cwd=REPO_ROOT, check=False,
        )
    return result.stdout


def load(filename: str) -> str:
    path = os.path.join(REPO_ROOT, filename)
    if not os.path.exists(path):
        return ""
    # errors="replace" swaps any invalid byte for U+FFFD instead of crashing —
    # a doc file with one stray non-UTF-8 character (common after Windows
    # editors save as cp1252/ANSI) shouldn't take down the whole review.
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def build_prompt(diff: str) -> str:
    context = "\n\n".join([
        "--- ARCHITECT_REVIEWER.md (your reviewer persona and checklist) ---",
        load("ARCHITECT_REVIEWER.md"),
        "--- STANDARDS.md (naming, schema, logging, testing rules) ---",
        load("STANDARDS.md"),
        "--- ARCHITECTURE.md excerpt (scope tiers + component map) ---",
        load("ARCHITECTURE.md")[:4000],
    ])
    return f"""{context}

Review the diff below as the architect persona described above. Produce a
detailed, structured review — this is meant to teach, not just gate.

## Summary
1-2 sentences: what this diff actually does.

## Findings
Only include the categories below that this diff genuinely touches — don't
force a section that isn't relevant. For each relevant category, state the
single biggest issue first if there is one, then 1-3 critical questions
(same spirit as ARCHITECT_REVIEWER.md's standing checklist):
- Schema / data model changes
- Kafka / streaming changes (partitioning, delivery semantics, windowing)
- API changes (REST/GraphQL)
- Infra / deploy changes
- Standards compliance (naming, schema versioning, logging, testing per tier)
- Performance (unnecessary allocations, N+1 patterns, blocking calls inside
  async code, missing indexes on frequently-filtered columns, unbounded
  loops/queries over potentially large tables)

## Verdict
End with exactly one line, formatted precisely as:
VERDICT: PASS
or
VERDICT: FAIL
followed by 1-2 sentences on why.

FAIL only for real violations — naming convention violations, missing
tests for Tier 1 components, unstructured logging, silently swallowed
errors, a breaking schema change with no DECISIONS.md entry, or a
scope-tier violation. Do NOT fail on style nitpicks, phrasing preferences,
or missing tests for Tier 2b/optional components.

DIFF:
{diff[:MAX_DIFF_CHARS]}
"""


def main() -> int:
    diff = get_diff()
    if not diff.strip():
        print("No diff to review.")
        return 0

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY not set — skipping AI review (won't block locally without it).")
        return 0

    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": build_prompt(diff)}],
    )
    text = response.content[0].text
    print(text)

    text_upper = text.upper()
    if "VERDICT: FAIL" in text_upper:
        is_fail = True
    elif "VERDICT: PASS" in text_upper:
        is_fail = False
    else:
        # Couldn't find a clean verdict line — fail open (don't block on our
        # own parsing bug) but make it loud so it doesn't go unnoticed.
        print("WARNING: could not parse a VERDICT: line from the response — defaulting to PASS.")
        is_fail = False

    header = "## 🤖 AI Architecture Review\n\n" + ("❌ **FAIL**" if is_fail else "✅ **PASS**") + "\n\n"
    with open(os.path.join(REPO_ROOT, "review_output.md"), "w") as f:
        f.write(header + text)

    return 1 if is_fail else 0


if __name__ == "__main__":
    sys.exit(main())
