# Contributing to VeriWeave Govern

Thank you for helping improve VeriWeave Govern. This is an open-source
engineering and research project, so contributions should preserve
deterministic behavior, auditability, security, and clear documentation.

Participation in this project is governed by
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Before contributing

- Use an issue to discuss substantial changes before implementation.
- Do not include confidential, personal, customer, employer-owned, or
  restricted material.
- Confirm that you have the right to contribute all submitted code,
  documentation, tests, examples, and data.
- Security vulnerabilities must follow [`SECURITY.md`](SECURITY.md), not the
  public issue tracker.
- Check existing issues and pull requests to avoid duplicating active work.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the local quality checks:

```bash
ruff check app benchmark tests
pytest -q
python -m build
python -m twine check dist/*
```

Run the end-to-end benchmark when behavior, policy evaluation, evidence
validation, audit logic, API contracts, or Docker configuration changes:

```bash
make benchmark
```

## Change requirements

A pull request should:

- have one clear purpose;
- include tests for changed behavior;
- preserve deterministic `deny > review > allow` precedence;
- keep fail-safe behavior for uncovered or ambiguous actions;
- avoid Python `eval` or equivalent dynamic execution in policy evaluation;
- document API, policy schema, configuration, and operational changes;
- update `CHANGELOG.md` for user-visible changes;
- avoid committing generated reports, secrets, credentials, or private data.

## Commit and pull-request guidance

Use concise imperative commit messages. Pull-request descriptions should cover:

- what changed and why;
- security and governance impact;
- backward-compatibility considerations;
- tests and benchmarks executed;
- documentation and migration requirements.

## Licensing of contributions

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in this project is licensed under the Apache License 2.0, in
accordance with Section 5 of [`LICENSE`](LICENSE).

Do not submit code or content copied from an incompatible license. Retain
required attribution and third-party notices when applicable.
