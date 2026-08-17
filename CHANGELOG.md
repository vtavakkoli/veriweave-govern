# Changelog

All notable changes to VeriWeave Govern are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Changed

- narrowed the supported runtime and CI target to Python 3.13 only, including package metadata and Docker images.

### Fixed

- replaced deprecated `typing.Iterable` imports in the research calibration and metrics modules with `collections.abc.Iterable` so Ruff passes on Python 3.13.

### Planned

- independent human-labelled real-world governance corpus
- pinned official OPA and Cedar execution in publication benchmark runs
- OIDC/workload identity, PostgreSQL, tenant isolation, signed policy approval workflow

## [0.3.0] - 2026-08-16

### Added

- GovernBench-v1 synthetic scientific benchmark across five domains, adversarial evidence/action attacks, OOD cases and temporal policy evolution;
- default 30-seed × 2,000-case evaluation with bootstrap 95% confidence intervals;
- learned logistic evidence calibration and safety-weighted threshold selection;
- RBAC, ABAC, deterministic language-style proxy, VeriWeave, and external OPA/Cedar baseline contracts;
- false-allow/deny/review metrics, GASR, Brier score, ECE, AUROC/AUPRC, temporal accuracy, and scalability profiling;
- six ablation experiments covering evidence, contradiction, oversight, OOD, precedence and temporal replay;
- counterfactual decision analysis and VeriWeave Governance Certificate research artifact;
- human-evaluation protocol, annotation template and Cohen-kappa scorer;
- EU AI Act, NIST AI RMF, and high-level ISO/IEC 42001 technical crosswalks;
- consulting assessment model and VGRI readiness utility;
- versioned synthetic reference results and research HTML report;
- Docker Compose research profile and CI research-smoke job.

### Changed

- upgraded package/container version to 0.3.0 and included `research`/`consulting` modules in distributions;
- clarified that LLMs may assist evidence/policy workflows but do not own the final authorization decision;
- strengthened documentation around scientific boundaries, external validity, and non-certification claims.

## [0.2.0] - 2026-08-02

- standardized Apache-2.0 licensing, package/container metadata, README, security, contribution/support, roadmap and citation metadata;
- expanded CI/package validation and Python 3.13 support.

## [0.1.0] - 2026-07-31

- deterministic `deny > review > allow` policy evaluation;
- evidence gates, human-review routing, tamper-evident audit, FastAPI service, Docker, tests and end-to-end benchmark.

[Unreleased]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vtavakkoli/veriweave-govern/releases/tag/v0.1.0
