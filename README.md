# Cryptonary-Pro community health

This public repository provides organization-wide GitHub community health
defaults for Cryptonary-Pro repositories that do not define a local override.

## Pull-request contract

The default template is
[`.github/pull_request_template.md`](.github/pull_request_template.md). GitHub
pre-populates it for new pull requests across the organization.

The canonical contract is maintained in
[`Cryptonary-Pro/Workspace`](https://github.com/Cryptonary-Pro/Workspace/blob/main/governance/templates/pull-request.md).
The Cryptonary QA GitHub App is installed with `repository_selection: all` and
remains the authoritative, fail-closed validator of submitted pull-request
bodies. The test in this repository protects the default template itself from
losing required headings or test-contract fields.

A repository-local pull-request template takes precedence over this default.
Local overrides should therefore be avoided unless they are deliberately kept
compatible with the canonical QA contract.

## Local verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_pull_request_template.py
```
