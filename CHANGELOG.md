# Changelog

All notable changes to VeriWeave Govern are documented here. The project follows Semantic Versioning.

## [Unreleased]

### Added

- machine-checkable primary-law and temporal-applicability audit for the 150-case EU/Austria publication validation set;
- human-readable 2026-08-17 legal snapshot describing the EU AI Act Digital Omnibus amendments and the Austrian NISG transition;
- publication-contract tests for official-source provenance, future-effective Annex III timing and the local Gemma 4 Ollama baseline.

### Changed

- incorporated Regulation (EU) 2026/1744 into the legal-source registry and corrected Article 6(2)/Annex III high-risk benchmark timing to the amended 2 December 2027 application date;
- updated Article 4 AI-literacy summaries to the amended requirement to support development of AI literacy rather than imply a guaranteed individual level;
- changed the actual local Ollama publication baseline from `gemma3n:e2b` to `gemma4:e2b` while keeping `http://host.docker.internal:11434` as the Docker-to-host endpoint;
- strengthened the blind two-annotator, pre-adjudication Cohen's-kappa and adjudication protocol documentation;
- separated current GDPR automated-decision cases from future-effective AI Act Annex III deployer obligations.

### Planned

- complete two genuinely independent annotator reviews and adjudication of the EU/Austria validation set;
- OIDC/workload identity, PostgreSQL, tenant isolation and signed policy approval workflow.

## [0.4.0] - 2026-08-17

### Added

- a 150-case EU/Austria regulation-grounded publication validation set with 50 public-administration, 50 enterprise IT/DevOps and 50 data/AI-governance cases, stored as six reviewable 25-case partitions;
- a snapshot-versioned official-source registry covering the EU AI Act, GDPR and selected Austrian DSG, IFG, E-Government and NIS/NIS2-related provisions;
- blind annotator A/B worksheets, adjudication worksheet and automatic Cohen's-kappa reporting without fabricating human labels;
- independently executable OPA/Rego 1.17.0 and Cedar 4.12.0 publication baselines;
- an actual local Ollama edge-LLM baseline using structured output;
- a Docker Compose `publication` profile that connects to host Ollama through `host.docker.internal:11434`;
- per-domain publication metrics, calibration reliability bins, an automatically generated SVG reliability diagram and raw external-baseline details;
- a real service-level load matrix with at least 10,000 requests per default concurrency level (`1,4,16,32`) and HTML/JSON reports;
- a `publication-suite` target combining the engineering benchmark, regulation-grounded external-baseline comparison and service load matrix.

### Changed

- added explicit legal/policy-prohibition metadata and legal-source provenance to research governance cases and certificates;
- documented evidence scores as thresholded trust scores and surfaced reliability/ECE rather than implying perfect probability calibration;
- upgraded package/container/citation version metadata to 0.4.0;
- narrowed the supported runtime and CI target to Python 3.13 only, including package metadata and Docker images.

### Fixed

- synchronized the runtime `app.__version__` with package/container metadata;
- replaced deprecated `typing.Iterable` imports with `collections.abc.Iterable` so Ruff passes on Python 3.13.

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

[Unreleased]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/vtavakkoli/veriweave-govern/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vtavakkoli/veriweave-govern/releases/tag/v0.1.0
