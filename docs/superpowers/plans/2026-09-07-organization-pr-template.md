# Organization Pull Request Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide every Cryptonary-Pro repository without a local override a canonical pull-request template that is compatible with the existing blocking QA contract.

**Architecture:** The public `Cryptonary-Pro/.github` repository supplies GitHub's organization-wide default template. A small standard-library Python validator and GitHub Actions workflow protect the static template from structural drift; the existing Cryptonary QA GitHub App remains the authoritative, fail-closed validator of each submitted PR body.

**Tech Stack:** Markdown, Python 3 standard library, GitHub Actions.

## Global Constraints

- Keep the organization repository public because GitHub requires that visibility for organization-wide pull-request templates.
- Preserve the eight canonical QA headings in their required order.
- Provide exactly one editable `Test files changed: Yes/No` declaration and an explicit relaxed-or-removed-assertions disclosure.
- Do not duplicate or weaken the existing runtime QA validator.
- Do not touch shared runner, Docker, Supabase, or application services.

---

### Task 1: Protect the organization template contract

**Files:**
- Create: `tests/test_validate_pull_request_template.py`
- Create: `scripts/validate_pull_request_template.py`
- Create: `.github/pull_request_template.md`

**Interfaces:**
- Consumes: the canonical headings and test-contract fields enforced by `Cryptonary-Pro/Workspace`.
- Produces: `validate_template(text: str) -> tuple[str, ...]` and a CLI that exits nonzero when the checked-in template is invalid.

- [ ] **Step 1: Write tests first**

  Cover the checked-in canonical template, missing or reordered headings, duplicate declarations, missing assertion disclosure, and a missing test-contract table.

- [ ] **Step 2: Verify the tests fail for the missing implementation**

  Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` and confirm failure because the validator does not exist.

- [ ] **Step 3: Add the minimal validator and canonical template**

  Implement exact structural checks with Python's standard library and add the eight-section Markdown template with guidance comments and the required four-column test table.

- [ ] **Step 4: Verify the tests and validator pass**

  Run `python3 -m unittest discover -s tests -p 'test_*.py' -v` and `python3 scripts/validate_pull_request_template.py` with zero failures.

### Task 2: Run validation automatically and document ownership

**Files:**
- Create: `.github/workflows/template-contract.yml`
- Modify: `README.md`

**Interfaces:**
- Consumes: the validator CLI from Task 1.
- Produces: a GitHub Actions check on template-related pushes and pull requests, plus clear documentation that the QA App is the authoritative submitted-body gate.

- [ ] **Step 1: Add the narrowly scoped workflow**

  Check out the repository, run the unit tests, and run the static template validator on changes to the template, validator, tests, or workflow.

- [ ] **Step 2: Document precedence and enforcement**

  Explain organization-default behavior, repository-local overrides, canonical source, and the distinction between static template validation and the blocking QA App.

- [ ] **Step 3: Run final verification**

  Run both Python verification commands, inspect the diff, confirm the repository is public, and confirm the QA App is configured for all installed repositories.

- [ ] **Step 4: Commit, push, and open the separate PR**

  Use a QA-contract-compliant PR body with `Test files changed: Yes`, one table row for the changed Python test, and an explicit disclosure of relaxed or removed assertions.
