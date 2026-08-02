# Changelog

All notable changes to VeriWeave Govern are documented in this file.

The project follows [Semantic Versioning](https://semver.org/) for public
release numbering.

## [Unreleased]

### Planned

- OIDC and workload identity
- PostgreSQL persistence and migrations
- tenant isolation and role-based administration
- signed policy bundles and approval workflows

## [0.2.0] - 2026-08-02

### Changed

- standardized the repository, package metadata, and container metadata under
  the Apache License 2.0;
- added canonical `LICENSE` and `NOTICE` files;
- upgraded package metadata to the current SPDX-based license expression and
  removed the deprecated license classifier that caused PEP 639 build failures;
- professionalized the README, security policy, contribution process, support
  policy, roadmap, citation metadata, issue forms, and pull-request workflow;
- added OCI image metadata and ensured license files are included in images and
  Python distributions;
- expanded CI to Python 3.13, package validation, and Node 24-native GitHub
  Actions.

### Fixed

- corrected the package configuration so editable installs, source
  distributions, wheels, containers, and benchmarks can proceed past license
  metadata validation.

## [0.1.0] - 2026-07-31

### Added

- deterministic policy evaluation with `deny > review > allow` precedence;
- evidence-quality validation and required-evidence gates;
- explicit human-review routing;
- hash-chained audit records with optional HMAC signatures;
- FastAPI service, dashboard, Docker Compose environment, tests, and an
  end-to-end benchmark with HTML and JSON reports.

[Unreleased]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vtavakkoli/veriweave-govern/releases/tag/v0.1.0
