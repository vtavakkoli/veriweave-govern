# EU/Austria regulation-grounded validation set

This directory contains a **150-case publication-candidate benchmark** for
runtime governance decisions. It is intentionally separated from GovernBench's
synthetic generator and is designed for expert review rather than automatic
claim generation.

## Composition

- 50 public-administration cases
- 50 enterprise IT / DevOps cases
- 50 data-handling / AI-governance cases
- balanced provisional development labels: 50 `allow`, 50 `review`, 50 `deny`
- six reviewable 25-case partitions

The cases are grounded in a versioned registry of **official primary-law EU and
Austrian sources**. The source snapshot date is **2026-08-17**. Sources include
the EU AI Act as amended by Regulation (EU) 2026/1744, GDPR, Austria's
Datenschutzgesetz (DSG), Informationsfreiheitsgesetz (IFG),
E-Government-Gesetz, the NISG regime in force at the snapshot, and NISG 2026
requirements enacted for later application.

## Critical 2026 AI Act timing

Regulation (EU) 2026/1744 changed the AI Act application schedule before this
benchmark snapshot. The repository therefore does **not** treat Article
6(2)/Annex III Chapter III Sections 1–3 obligations as already applicable on
2026-08-17. Relevant high-risk cases use `evaluation_date=2027-12-03`, after the
2 December 2027 application date, and are explicitly marked
`enacted_future_effective_at_snapshot`.

The source registry also reflects the amended Article 4: providers and deployers
must take measures to **support the development of AI literacy**; the amended
rule does not require guaranteeing a specific level for each individual.

The same temporal method is used for Austria's NISG 2026: future-effective cases
use an evaluation date after 2026-10-01 and remain visibly marked as future law
at the 2026-08-17 snapshot.

## Automated primary-law audit

Before a publication run, execute:

```bash
python -m research.legal_audit
```

The audit checks:

- exactly 150 cases, 50 per domain and 25 per partition;
- balanced provisional labels;
- unique case IDs;
- legal-source provenance for every case;
- primary-law source hosts (`eur-lex.europa.eu` and Austrian RIS);
- source verification and application dates;
- temporal consistency between each case evaluation date and every cited source;
- the post-2026 Digital Omnibus application date for Annex III high-risk rules.

The publication Docker entrypoint runs this audit automatically and stops on a
hard inconsistency. Its machine-readable output is
`results/publication/legal-audit.json`.

## Scientific boundary

`provisional_label`, `provisional_rationale`, and `prohibition_reason` are
researcher-generated hypotheses for benchmark construction. They are **not
human ground truth and not legal advice**.

These cases are realistic, regulation-grounded scenarios. They are not claimed
to be sampled production logs or observed enforcement cases. The paper should
use the phrase **regulation-grounded expert-validation set** until independent
human annotation and adjudication are complete.

The two annotator sheets are blind: they intentionally omit provisional labels,
provisional rationales, prohibition metadata, model predictions and the other
annotator's answers.

## Independent annotation protocol

1. Run the publication benchmark once to generate
   `results/publication/annotator-a.csv` and `annotator-b.csv`.
2. Give each worksheet only to its corresponding annotator. Annotators should
   have sufficient EU/Austrian governance, privacy, public-administration or IT
   risk expertise for the assigned review.
3. Each annotator independently records `allow|review|deny`, confidence 1–5 and
   optional notes after reviewing the case facts, `evaluation_date`,
   `legal_status`, and linked official sources.
4. `allow` means the described action may proceed under the supplied facts and
   evidence; `review` means accountable human/legal/privacy/security review or
   missing evidence is required before execution; `deny` means the action as
   stated should not proceed because it matches a prohibition or an explicitly
   unacceptable disclosure/security condition. These are benchmark decision
   semantics, not a universal legal taxonomy.
5. Do not let annotators inspect `provisional_label`, `provisional_rationale`,
   `prohibition_reason`, predictions, or each other's answers before both sheets
   are frozen.
6. Report raw agreement and Cohen's kappa on the two independent sheets **before
   adjudication**.
7. Resolve disagreements in `results/publication/adjudication.csv`, recording an
   adjudication rationale, adjudicator identifier/pseudonym and date.
8. Re-run the publication profile. The report switches from
   `provisional-regulation-grounded` to `human-adjudicated` only when all 150
   adjudicated labels are present.
9. Preserve the original independent worksheets as immutable research artifacts
   for the paper/reproducibility package.

Do not invent a second annotator, fill consensus labels on behalf of an
annotator, or report Cohen's kappa before two genuinely independent reviews
exist.

## Files

- `public-administration-1.csv` / `public-administration-2.csv`
- `enterprise-it-devops-1.csv` / `enterprise-it-devops-2.csv`
- `data-ai-governance-1.csv` / `data-ai-governance-2.csv`
- `regulatory_sources.json` — snapshot-versioned primary-law registry
- `LEGAL_SNAPSHOT_2026-08-17.md` — human-readable legal timing and verification notes
- `results/publication/legal-audit.json` — generated temporal/source integrity audit
- `results/publication/annotator-a.csv` / `annotator-b.csv` — generated blind worksheets
- `results/publication/adjudication.csv` — generated final gold-label worksheet

Do not commit personal data about annotators or confidential case material.
