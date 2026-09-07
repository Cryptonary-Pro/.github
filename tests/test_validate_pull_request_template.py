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

    def test_heading_hidden_in_html_comment_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "## Outcome",
            "<!--\n## Outcome\n-->",
            1,
        )

        self.assertIn(
            "required heading must appear exactly once: Outcome",
            VALIDATOR.validate_template(template),
        )

    def test_heading_inside_fenced_code_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "## Outcome",
            "```markdown\n## Outcome\n```",
            1,
        )

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
        template = self.canonical_template().replace(
            "Test files changed: Yes/No",
            "Test files changed: Yes/No\nTest files changed: Yes/No",
            1,
        )

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            VALIDATOR.validate_template(template),
        )

    def test_test_file_declaration_outside_test_contract_section_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "Test files changed: Yes/No",
            "Test selection: Yes/No",
            1,
        )
        template += "\nTest files changed: Yes/No\n"

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            VALIDATOR.validate_template(template),
        )

    def test_commented_test_contract_fields_are_rejected(self) -> None:
        template = self.canonical_template().replace(
            "Test files changed: Yes/No",
            "<!--\nTest files changed: Yes/No\n-->",
            1,
        )
        template = template.replace(
            "Relaxed or removed assertions: None.",
            "<!-- Relaxed or removed assertions: None. -->",
            1,
        )
        template = template.replace(
            "| file | change | business behavior | reason |\n"
            "| --- | --- | --- | --- |",
            "<!--\n"
            "| file | change | business behavior | reason |\n"
            "| --- | --- | --- | --- |\n"
            "-->",
            1,
        )

        violations = VALIDATOR.validate_template(template)

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            violations,
        )
        self.assertIn(
            "template must contain one relaxed-or-removed-assertions disclosure",
            violations,
        )
        self.assertIn(
            "template must contain the canonical test-contract table",
            violations,
        )

    def test_nonvisible_html_cannot_supply_test_contract_declaration(self) -> None:
        for tag in ("template", "script", "style"):
            with self.subTest(tag=tag):
                template = self.canonical_template().replace(
                    "Test files changed: Yes/No",
                    f"<{tag}>\nTest files changed: Yes/No\n</{tag}>",
                    1,
                )

                self.assertIn(
                    "template must contain exactly one "
                    "Test files changed: Yes/No declaration",
                    VALIDATOR.validate_template(template),
                )

    def test_higher_level_heading_closes_test_contract_section(self) -> None:
        template = self.canonical_template().replace(
            "## Test contract changes\n\nTest files changed: Yes/No",
            "## Test contract changes\n\n# Outside test contract\n\n"
            "Test files changed: Yes/No",
            1,
        )

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            VALIDATOR.validate_template(template),
        )

    def test_indented_higher_level_heading_closes_test_contract_section(self) -> None:
        template = self.canonical_template().replace(
            "## Test contract changes\n\nTest files changed: Yes/No",
            "## Test contract changes\n\n   # Outside test contract\n\n"
            "Test files changed: Yes/No",
            1,
        )

        self.assertIn(
            "template must contain exactly one Test files changed: Yes/No declaration",
            VALIDATOR.validate_template(template),
        )

    def test_heavily_indented_fence_cannot_supply_test_contract_declaration(self) -> None:
        template = self.canonical_template().replace(
            "Test files changed: Yes/No",
            "    ```text\nTest files changed: Yes/No\n    ```",
            1,
        )

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

    def test_blockquoted_test_contract_table_is_rejected(self) -> None:
        template = self.canonical_template().replace(
            "| file | change | business behavior | reason |\n"
            "| --- | --- | --- | --- |",
            "> | file | change | business behavior | reason |\n"
            "> | --- | --- | --- | --- |",
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
