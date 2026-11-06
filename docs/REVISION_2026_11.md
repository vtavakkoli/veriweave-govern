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

## Qualified expert annotation and confidentiality

The authors confirm that annotation was completed by qualified domain experts
with professional expertise relevant to the segments under review: public
administration, enterprise IT/DevOps, and data/AI governance. Their identities
remain confidential and are represented only as Annotator A and Annotator B.
The manuscript reports domain-level qualifications and the blinded annotation
procedure without publishing names or identifying biographies. The earlier
wording that treated their domain qualifications as unconfirmed is superseded.

The supplied materials contain aggregate human-study results rather than the
completed row-level worksheets and frozen comparator predictions. Reproducing
those historical metrics requires the existing pseudonymized records, not the
annotators' public identities. The annotation-audit tool can compute confidence
distributions and casewise agreement using anonymous case and annotator IDs.
Equal aggregate means do not establish casewise confidence equality.

The disclosure template records the confirmed expert qualification and the
confidentiality policy. Any additional protocol facts must come from actual
study records and can be described without identifying participants. No specific
degrees, employers, years of experience or participant relationships are inferred
from the qualification statement.

Before resubmission, supply the existing records, recompute the external
comparison and confirm the Gemma confusion breakdown. The 150-case bank is an
evaluation set for frozen predictions, rather than training/fine-tuning data;
the evidence calibrator is trained separately on synthetic cases. The authors
confirm that the human-review budget is fixed and cannot be increased for this
resubmission. Additional independent case collection would require separate
resources and is not a promised experiment for the present scoped revision.
Retain the narrow claims and report uncertainty for the existing bank. Sample
adequacy is tied to an estimand, precision and sampling design, not a universal
case-count cutoff. The 70 non-allow cases, rather than all 150 cases or 300
ratings, determine the conditional unsafe-allow opportunity count. Naturally
occurring cases and independently curated evidence remain possible separately
funded work for broader claims. The protocol and numerical records can be verified in pseudonymized form while
preserving the experts' identities.

## Version and archival status

The manuscript and response are supplied separately for author review. The repository revision is release candidate 0.5.0rc1. The branch commit and accompanying source-checksum
manifest identify its exact implementation. A GitHub commit is not an archival
DOI deposit. No DOI or permanent third-party archive is claimed; deposit the
approved source and raw data in an archive before giving an archival citation.
