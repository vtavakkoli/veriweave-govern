# Contributing to VeriWeave Govern

Thank you for helping improve VeriWeave Govern. This repository is a
source-available commercial product and research integration foundation, so
contributions must preserve deterministic behavior, auditability, and clear
licensing.

## Before contributing

- Use an issue to discuss substantial changes before implementation.
- Do not include confidential, personal, customer, employer-owned, or
  restricted material.
- Confirm that you have the right to contribute all submitted code,
  documentation, tests, examples, and data.
- Security vulnerabilities must follow [`SECURITY.md`](SECURITY.md), not the
  public issue tracker.

External code contributions require prior maintainer approval and may require
a separate contributor agreement before merge. This protects the project's
ability to provide both source-available and commercial licensing.

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

Unless a separate written agreement states otherwise, contributions accepted
into a BUSL-licensed release are distributed under the same Business Source
License parameters that apply to that release and later under its Change
License. Do not submit code copied from an incompatible license.

Opening an issue or pull request does not grant production or commercial-use
rights beyond those provided by [`LICENSE`](LICENSE).
