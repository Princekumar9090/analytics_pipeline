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
MODEL = "claude-sonnet-4-6"
MAX_DIFF_CHARS = 15000  # keep the review focused and fast; huge diffs should be split into smaller commits anyway


def get_diff() -> str:
    base = os.environ.get("REVIEW_BASE_REF", "origin/main")
    result = subprocess.run(
        ["git", "diff", f"{base}...HEAD"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        # Fallback for local pre-commit use: staged changes, no remote ref needed
        result = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True, cwd=REPO_ROOT,
        )
    return result.stdout


def load(filename: str) -> str:
    path = os.path.join(REPO_ROOT, filename)
    if not os.path.exists(path):
        return ""
    with open(path) as f:
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

Review the diff below strictly against the standards and architecture context above.

Reply with a first line of exactly PASS or FAIL, then bullet-point findings.

FAIL only for real violations:
- Naming convention violations (topics, tables, env vars, consumer groups)
- Missing tests for Tier 1 components (per STANDARDS.md section 4)
- Unstructured logging (bare print(), missing correlation ID)
- Silently swallowed errors (bare except:, dropped events with no DLQ/log)
- A breaking event-schema change with no corresponding DECISIONS.md entry
- Scope-tier violations (e.g. building a Tier 3 item as if it were Tier 1)

Do NOT fail on style nitpicks, naming you'd merely phrase differently, or
missing tests for Tier 2b/optional components. Be the skeptical-but-fair
architect described in ARCHITECT_REVIEWER.md — state the single biggest
issue first if there is one.

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
        max_tokens=1000,
        messages=[{"role": "user", "content": build_prompt(diff)}],
    )
    text = response.content[0].text
    print(text)
    return 1 if text.strip().upper().startswith("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
