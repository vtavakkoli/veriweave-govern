# EU/Austria regulation-grounded validation set

This directory contains a **150-case publication-candidate benchmark** for runtime governance decisions. It is intentionally separated from GovernBench's synthetic generator.

## Composition

- 50 public-administration cases
- 50 enterprise IT / DevOps cases
- 50 data-handling / AI-governance cases
- balanced provisional development labels: 50 `allow`, 50 `review`, 50 `deny`

The cases are grounded in a versioned registry of official EU and Austrian sources. The snapshot date is **2026-08-17**. Sources include the EU AI Act, GDPR, Austria's Datenschutzgesetz (DSG), Informationsfreiheitsgesetz (IFG), E-Government-Gesetz, the NISG rules in force at the snapshot, and the enacted NISG 2026 requirements that become effective on 2026-10-01.

## Scientific boundary

`provisional_label`, `provisional_rationale`, and `prohibition_reason` are researcher-generated hypotheses for benchmark construction. They are **not human ground truth and not legal advice**.

The two annotator sheets are blind: they intentionally omit those provisional fields. An IEEE paper must describe the set as *regulation-grounded* until both independent annotation sheets and the adjudication file are complete.

## Independent annotation

1. Run the publication benchmark once to generate `results/publication/annotator-a.csv` and `annotator-b.csv`.
2. Give each file only to its corresponding annotator.
3. Each annotator independently records `allow|review|deny`, confidence 1–5 and optional notes after reviewing the case and the linked official sources.
4. Do not let annotators inspect `provisional_label`, `provisional_rationale`, `prohibition_reason`, predictions, or each other's answers before completion.
5. Resolve disagreements in `results/publication/adjudication.csv`, documenting the rationale.
6. Re-run the publication profile. The report switches from `provisional-regulation-grounded` to `human-adjudicated` only when all 150 adjudicated labels are present.
7. Report Cohen's kappa from the two independent sheets before adjudication.

## Temporal law handling

The source registry stores both `status_on_2026_08_17` and `applicable_from`. Cases based on NISG 2026 use an evaluation date after 2026-10-01 and are marked as future-effective at the snapshot. This prevents future requirements from being silently represented as already applicable on the source-verification date.

## Files

- `eu_at_reggov_150.csv` — master research set; contains provisional hypotheses.
- `regulatory_sources.json` — verified official-source registry.
- `results/publication/annotator-a.csv` / `annotator-b.csv` — generated blind independent review sheets.
- `results/publication/adjudication.csv` — generated final gold-label worksheet.

Do not commit personal data about annotators or confidential case material.
