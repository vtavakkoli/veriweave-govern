# Reviewer revision, November 2026

The contribution is an evidence, review, replay and audit envelope around
deterministic authorization. The reported human-bank decision metrics are equal
for VeriWeave, OPA and Cedar. There is no demonstrated decision-quality advantage
over those engines. Gemma's higher reported human-label agreement is retained as
a decision-alignment result, with a different operational role from enforcement.

## Reproduce the new experiments

Use Python 3.13 and install `.[dev]`, then run:

```bash
make revision-validation
python -m research.service_validation
python -m research.experiments --seeds 30 --cases 2000 --write-dataset \
  --output results/revision-2026-11/governbench
```

`revision-validation` runs direct audit tampering, actual service-engine replay,
authenticated evidence fixtures, concurrent reloads and a 100/1,000/10,000-rule
by 1/10/100-evidence matrix. The latter measures the in-process engine and JSONL
append on one process, with 100 sequential requests per cell; it is not a
distributed or HTTP throughput measurement. The separate service-validation
command starts an actual HTTP server, exercises the existing 12 scenarios, and
checks successful replay and rejection of an incorrect historical policy hash.

All new policies, tickets and cryptographic keys are researcher-authored test
fixtures. Authenticating a fixture establishes that the configured connector/key
produced those bytes; it does not establish the truth, legal sufficiency or
production reliability of an organizational document. No new independent human
study or real organizational evidence corpus is claimed.

## Corrections to the original reporting

1. `--cases 2000` generates 2,000 cases per seed. Index residues 2/3/4 train the
   evidence model; 0/1 are evaluated. The 30-seed run therefore generates 60,000
   cases, trains on 36,000 and evaluates **24,000**. The rerun retains the
   reported 0.9888 mean accuracy. Raw held-out predictions and per-seed counts
   are now exported. GovernBench is specification conformance and fault
   injection against shared intended semantics, not independent evidence that
   the policy is correct for real organizations.
2. The original paper defines FRev as `reference=allow, prediction=review / N`.
   Its stated Gemma confusion breakdown is one allow-to-review and three
   deny-to-review errors. That implies **1/150 = 0.0067 FRev**, rather than
   4/150 = 0.0267 (all incorrect review predictions). This is an arithmetic
   correction conditional on the supplied breakdown, not a new LLM run.
3. The original RBAC FRev of 0.7600 is impossible under that definition when
   only 80/150 reference cases are allow. RBAC/ABAC FRev are left unreported in
   the revised table pending the original row-level outputs. Their other
   supplied aggregate metrics are retained as reported, not independently
   recomputed. The original table CSV also contains development-label values
   inconsistent with its human-label LaTeX counterpart; the revised CSV is
   explicitly labelled as a reporting summary.
4. A bootstrap of all-zero unsafe-allow indicators produces a degenerate
   interval and cannot bound risk. Reports now retain unsafe-event counts and
   denominators and use exact Clopper-Pearson intervals. For the supplied
   human-bank totals, zero events among 70 review/deny cases yields a two-sided
   95% interval `[0, 0.051334]` and a one-sided 95% upper bound `0.041893`.
   These binomial calculations assume IID sampling from a fixed case process;
   the constructed bank does not support a deployment-population risk bound.
5. The learned research trust score and the HTTP service adapter are different
   implementations. The synthetic research profile's ECE of 0.2253 remains
   visible. The service's demonstration adapter uses a fixed heuristic. Its
   new attested mode adds source/type/version, HMAC, scope and time validation.
   No calibration or discrimination result is transferred between these modes.

The original `results/paper-2026/paper-results.json` is retained unchanged as a
record of what was submitted. New outputs live in `results/revision-2026-11/`.

## Human-study facts still requiring author completion

The supplied materials provide aggregate human-study results but not the raw
completed workbooks or frozen comparator predictions. They do not document
whether annotators are authors/external participants, actual expertise,
recruitment, pilot/training, case-difficulty selection or casewise confidence
agreement. Equal mean confidence and perfect label agreement cannot fill those
gaps. No identities, qualifications, independence or new annotations have been
invented.

Complete `research/validation/annotator-disclosures.template.json`, retain the
original worksheets, and run `python -m research.annotation_audit --help`.
The audit computes confidence distributions and casewise agreement separately,
hashes the supplied files, rejects duplicate/incomplete records and reports
missing disclosures. See the detailed rubric in `docs/HUMAN_EVALUATION.md`.

Before resubmission, supply those records, recompute the external comparison,
confirm the Gemma confusion breakdown, and obtain independent domain review or
retain the explicitly narrow claims in the manuscript. New naturally occurring
cases and an independently curated evidence corpus remain open validation needs.

## Version and archival status

The manuscript and response are supplied separately for author review. The repository revision is release candidate 0.5.0rc1. The branch commit and accompanying source-checksum
manifest identify its exact implementation. A GitHub commit is not an archival
DOI deposit. No DOI or permanent third-party archive is claimed; deposit the
approved source and raw data in an archive before giving an archival citation.
