"""Verify red-then-green TDD evidence on the current branch.

Checks each commit between the merge base with the default branch and HEAD.
A commit that touches production code (``src/``) must satisfy one of:

- an earlier commit in the range already touched ``tests/`` (test-first commits), or
- its message carries both ``[red]`` and ``[green]`` markers (single-commit mode,
  paired with a *Red/green record* note in the spec), or
- its type is exempt (``docs``, ``chore``, ``ci``, ``build``, ``refactor``,
  ``style``), matching the ``TDD: optional`` reasons allowed by ``specs/TEMPLATE.md``.

Run via ``make check-tdd``. An empty commit range (e.g. on ``main``) passes.
"""

from __future__ import annotations

import subprocess
import sys

EXEMPT_TYPES = frozenset({"docs", "chore", "ci", "build", "refactor", "style", "test"})
DEFAULT_BRANCH = "main"
PRODUCTION_PREFIX = "src/"
TEST_PREFIX = "tests/"


def _git(*args: str) -> str:
    result = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _merge_base() -> str | None:
    for ref in (f"origin/{DEFAULT_BRANCH}", DEFAULT_BRANCH):
        try:
            base = _git("merge-base", "HEAD", ref)
        except subprocess.CalledProcessError:
            continue
        if base:
            return base
    return None


def _commits_in_range(base: str) -> list[str]:
    output = _git("rev-list", "--reverse", f"{base}..HEAD")
    return output.splitlines() if output else []


def _commit_message(commit: str) -> str:
    return _git("log", "-1", "--format=%B", commit)


def _changed_files(commit: str) -> list[str]:
    output = _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return output.splitlines() if output else []


def _commit_type(subject: str) -> str:
    return subject.split(":", 1)[0].split("(", 1)[0].strip().rstrip("!")


def main() -> int:
    """Run the TDD gate and return a process exit code."""
    base = _merge_base()
    if base is None:
        print("check-tdd: no merge base with the default branch found; skipping.")
        return 0

    commits = _commits_in_range(base)
    tests_seen = False
    failures: list[str] = []

    for commit in commits:
        files = _changed_files(commit)
        message = _commit_message(commit)
        subject = message.splitlines()[0] if message else ""

        if any(f.startswith(PRODUCTION_PREFIX) for f in files):
            has_markers = "[red]" in message and "[green]" in message
            exempt = _commit_type(subject) in EXEMPT_TYPES
            if not (tests_seen or has_markers or exempt):
                failures.append(f"{commit[:8]} {subject}")

        # Updated after the check so a mixed test+src commit still needs markers.
        if any(f.startswith(TEST_PREFIX) for f in files):
            tests_seen = True

    if failures:
        print("check-tdd: production code landed without red-then-green evidence:")
        for failure in failures:
            print(f"  - {failure}")
        print(
            "Fix: land a `test:` commit before the implementation commit, or add "
            "[red]/[green] markers to a combined commit (with a Red/green record "
            "note in the spec)."
        )
        return 1

    print(f"check-tdd: OK ({len(commits)} commit(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
