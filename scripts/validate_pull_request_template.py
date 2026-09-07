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
    r"(?m)^[ ]{0,3}(?:[-*+][ \t]+)?"
    r"Test files changed[ \t]*:[ \t]*Yes/No[ \t]*$"
)
ASSERTION_DISCLOSURE = re.compile(
    r"(?m)^[ ]{0,3}(?:[-*+][ \t]+)?"
    r"Relaxed or removed assertions[ \t]*:[ \t]*\S.*$"
)
NO_TEST_RATIONALE = re.compile(
    r"(?m)^[ ]{0,3}(?:[-*+][ \t]+)?No-test rationale[ \t]*:[ \t]*.*$"
)
TABLE_HEADER = re.compile(
    r"(?m)^[ ]{0,3}\| file \| change \| business behavior \| reason \|[ \t]*$"
)
TABLE_SEPARATOR = re.compile(
    r"(?m)^[ ]{0,3}\| --- \| --- \| --- \| --- \|[ \t]*$"
)
NONVISIBLE_HTML_CONTAINERS = (
    "head",
    "iframe",
    "noembed",
    "noframes",
    "noscript",
    "script",
    "style",
    "template",
    "textarea",
    "title",
    "xmp",
)
MARKDOWN_HEADING = re.compile(
    r"(?m)^[ ]{0,3}(?P<marks>#{1,6})[ \t]+"
    r"(?P<title>[^\r\n]*?)[ \t]*\r?$"
)


def _masked(content: str) -> str:
    """Blank content while preserving line boundaries for later parsing."""
    return re.sub(r"[^\r\n]", " ", content)


def _without_fenced_code(text: str) -> str:
    """Mask Markdown fenced code blocks, including an unclosed final fence."""
    result: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_character is None:
            opening = re.match(r"^[ \t]*(?P<fence>`{3,}|~{3,})", content)
            if opening is None:
                result.append(line)
                continue

            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            result.append(_masked(line))
            continue

        result.append(_masked(line))
        if re.fullmatch(
            rf"[ ]{{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            content,
        ):
            fence_character = None
            fence_length = 0

    return "".join(result)


def _visible_markdown(text: str) -> str:
    """Mask content the QA parser does not treat as visible Markdown."""
    visible = _without_fenced_code(text)
    visible = re.sub(
        r"<!--.*?(?:-->|\Z)",
        lambda match: _masked(match.group()),
        visible,
        flags=re.DOTALL,
    )
    for tag in NONVISIBLE_HTML_CONTAINERS:
        visible = re.sub(
            rf"<{tag}\b[^>]*>.*?(?:</{tag}[ \t]*>|\Z)",
            lambda match: _masked(match.group()),
            visible,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return visible


def _test_contract_section(text: str) -> str:
    """Return the visible Test contract changes body, excluding later sections."""
    section_heading = re.search(
        r"(?m)^[ ]{0,3}##[ \t]+Test contract changes[ \t]*\r?$",
        text,
    )
    if section_heading is None:
        return ""

    body_start = section_heading.end()
    for heading in MARKDOWN_HEADING.finditer(text, body_start):
        if len(heading.group("marks")) <= 2:
            return text[body_start : heading.start()]
    return text[body_start:]


def validate_template(text: str) -> tuple[str, ...]:
    """Return structural contract violations for one template body."""
    violations: list[str] = []
    positions: list[int] = []
    visible_text = _visible_markdown(text)

    for heading in REQUIRED_HEADINGS:
        matches = tuple(
            re.finditer(
                rf"(?m)^[ ]{{0,3}}##[ \t]+{re.escape(heading)}[ \t]*\r?$",
                visible_text,
            )
        )
        if len(matches) != 1:
            violations.append(f"required heading must appear exactly once: {heading}")
        else:
            positions.append(matches[0].start())

    if len(positions) == len(REQUIRED_HEADINGS) and positions != sorted(positions):
        violations.append("required headings must use canonical order")

    test_contract = _test_contract_section(visible_text)
    if len(TEST_DECLARATION.findall(test_contract)) != 1:
        violations.append(
            "template must contain exactly one Test files changed: Yes/No declaration"
        )
    if len(ASSERTION_DISCLOSURE.findall(test_contract)) != 1:
        violations.append(
            "template must contain one relaxed-or-removed-assertions disclosure"
        )
    if len(NO_TEST_RATIONALE.findall(test_contract)) != 1:
        violations.append("template must contain one No-test rationale field")
    if len(TABLE_HEADER.findall(test_contract)) != 1 or len(
        TABLE_SEPARATOR.findall(test_contract)
    ) != 1:
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
