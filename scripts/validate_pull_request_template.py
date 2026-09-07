#!/usr/bin/env python3
"""Validate the organization-wide pull-request template structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / ".github" / "pull_request_template.md"

REQUIRED_HEADINGS = (
    "Outcome",
    "What changed",
    "Scope and non-goals",
    "Test contract changes",
    "Verification",
    "Risk, rollout, and rollback",
    "Product or UI evidence",
    "Checklist",
)

TEST_DECLARATION = re.compile(
    r"(?m)^[ \t]*(?:[-*+][ \t]+)?Test files changed[ \t]*:[ \t]*Yes/No[ \t]*$"
)
ASSERTION_DISCLOSURE = re.compile(
    r"(?m)^[ \t]*(?:[-*+][ \t]+)?Relaxed or removed assertions[ \t]*:[ \t]*\S.*$"
)
NO_TEST_RATIONALE = re.compile(
    r"(?m)^[ \t]*(?:[-*+][ \t]+)?No-test rationale[ \t]*:[ \t]*\S.*$"
)
TABLE_HEADER = "| file | change | business behavior | reason |"
TABLE_SEPARATOR = "| --- | --- | --- | --- |"


def validate_template(text: str) -> tuple[str, ...]:
    """Return structural contract violations for one template body."""
    violations: list[str] = []
    positions: list[int] = []

    for heading in REQUIRED_HEADINGS:
        matches = tuple(
            re.finditer(rf"(?m)^##[ \t]+{re.escape(heading)}[ \t]*$", text)
        )
        if len(matches) != 1:
            violations.append(f"required heading must appear exactly once: {heading}")
        else:
            positions.append(matches[0].start())

    if len(positions) == len(REQUIRED_HEADINGS) and positions != sorted(positions):
        violations.append("required headings must use canonical order")

    if len(TEST_DECLARATION.findall(text)) != 1:
        violations.append(
            "template must contain exactly one Test files changed: Yes/No declaration"
        )
    if len(ASSERTION_DISCLOSURE.findall(text)) != 1:
        violations.append(
            "template must contain one relaxed-or-removed-assertions disclosure"
        )
    if len(NO_TEST_RATIONALE.findall(text)) != 1:
        violations.append("template must contain one No-test rationale field")
    if text.count(TABLE_HEADER) != 1 or text.count(TABLE_SEPARATOR) != 1:
        violations.append("template must contain the canonical test-contract table")

    return tuple(violations)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: validate_pull_request_template.py [template-path]", file=sys.stderr)
        return 2

    template_path = Path(arguments[0]) if arguments else DEFAULT_TEMPLATE
    try:
        text = template_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"unable to read pull-request template: {error}", file=sys.stderr)
        return 1

    violations = validate_template(text)
    if violations:
        for violation in violations:
            print(f"error: {violation}", file=sys.stderr)
        return 1

    print(f"pull-request template contract valid: {template_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
