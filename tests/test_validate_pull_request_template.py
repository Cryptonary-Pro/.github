from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_pull_request_template.py"
TEMPLATE_PATH = ROOT / ".github" / "pull_request_template.md"

SPEC = importlib.util.spec_from_file_location("validate_pull_request_template", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load template validator")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class PullRequestTemplateContractTests(unittest.TestCase):
    @classmethod
    def canonical_template(cls) -> str:
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_checked_in_template_satisfies_the_contract(self) -> None:
        self.assertEqual((), VALIDATOR.validate_template(self.canonical_template()))

    def test_missing_heading_is_rejected(self) -> None:
        template = self.canonical_template().replace("## Outcome", "## Result", 1)

        self.assertIn(
            "required heading must appear exactly once: Outcome",
            VALIDATOR.validate_template(template),
        )

    def test_reordered_headings_are_rejected(self) -> None:
        template = self.canonical_template()
        template = template.replace("## Outcome", "## HEADING-SWAP", 1)
        template = template.replace("## What changed", "## Outcome", 1)
        template = template.replace("## HEADING-SWAP", "## What changed", 1)

        self.assertIn(
            "required headings must use canonical order",
            VALIDATOR.validate_template(template),
        )

    def test_duplicate_test_file_declaration_is_rejected(self) -> None:
        template = self.canonical_template() + "\nTest files changed: Yes/No\n"

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            VALIDATOR.validate_template(template),
        )

    def test_missing_assertion_disclosure_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "Relaxed or removed assertions: None.",
            "Assertion changes are described above.",
            1,
        )

        self.assertIn(
            "template must contain one relaxed-or-removed-assertions disclosure",
            VALIDATOR.validate_template(template),
        )

    def test_missing_test_contract_table_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "| file | change | business behavior | reason |",
            "| file | notes |",
            1,
        )

        self.assertIn(
            "template must contain the canonical test-contract table",
            VALIDATOR.validate_template(template),
        )

    def test_missing_test_contract_table_separator_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "| --- | --- | --- | --- |",
            "| --- | --- |",
            1,
        )

        self.assertIn(
            "template must contain the canonical test-contract table",
            VALIDATOR.validate_template(template),
        )

    def test_missing_no_test_rationale_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "No-test rationale:",
            "Testing rationale:",
            1,
        )

        self.assertIn(
            "template must contain one No-test rationale field",
            VALIDATOR.validate_template(template),
        )

    def test_cli_accepts_the_checked_in_template(self) -> None:
        standard_output = io.StringIO()
        with redirect_stdout(standard_output):
            result = VALIDATOR.main((str(TEMPLATE_PATH),))

        self.assertEqual(0, result)
        self.assertIn("pull-request template contract valid", standard_output.getvalue())

    def test_cli_rejects_an_invalid_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            invalid_template = Path(directory) / "pull_request_template.md"
            invalid_template.write_text("## Outcome\nIncomplete.\n", encoding="utf-8")
            standard_error = io.StringIO()
            with redirect_stderr(standard_error):
                result = VALIDATOR.main((str(invalid_template),))

        self.assertEqual(1, result)
        self.assertIn("error: required heading", standard_error.getvalue())


if __name__ == "__main__":
    unittest.main()
