# Legal snapshot — 2026-08-17

This note records the legal timing assumptions used to construct the
EU/Austria publication-validation dataset. It is a reproducibility artifact,
not legal advice.

## 1. EU AI Act after the 2026 Digital Omnibus

Primary amendment:

- Regulation (EU) 2026/1744, CELEX 32026R1744:
  https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R1744

The amendment entered into force on 27 July 2026 and changes two benchmark-
critical points:

1. **Article 4 — AI literacy.** The amended rule requires providers and
   deployers to take measures to support development of AI literacy of staff and
   other persons operating/using AI systems on their behalf, considering
   knowledge, experience, education, training and context. It explicitly states
   that providers/deployers do not have to guarantee a specific level for every
   individual.
2. **Article 113 — high-risk application dates.** Chapter III Sections 1, 2 and
   3 apply from **2 December 2027** for systems classified as high-risk under
   Article 6(2) and Annex III, and from **2 August 2028** for Article 6(1) and
   Annex I systems.

Consequently, this repository does not describe Annex III high-risk deployer
obligations as current law on 2026-08-17. The curated Annex III cases are
explicit temporal scenarios evaluated on 2027-12-03.

Core Article 5 prohibited-practice cases remain separately represented as
current-law cases where the scenario is intentionally constructed to match a
specific prohibition already applicable at the snapshot. Annotators must still
check the exact facts and exceptions rather than infer a prohibition from the
family name alone.

## 2. GDPR

Primary text:

- Regulation (EU) 2016/679:
  https://eur-lex.europa.eu/eli/reg/2016/679/oj

The benchmark uses selected current provisions including Article 5 processing
principles, Article 22 solely automated significant decisions, Article 25 data
protection by design/default, Article 32 security of processing and Article 35
DPIA requirements. These provisions are used conservatively: a case does not
claim that every automated or high-impact processing operation is prohibited.
Where an exception, lawful basis, proportionality analysis or safeguard could
change the outcome, the benchmark generally routes the case to `review`.

## 3. Austrian data protection and e-government

Primary Austrian RIS texts:

- Datenschutzgesetz (DSG):
  https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10001597
- E-Government-Gesetz (E-GovG):
  https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20003230

The dataset uses the Austrian constitutional confidentiality protection in DSG
Article 1 § 1 and the E-GovG § 1 framing for electronic communication and
safeguards around increased automated data processing.

## 4. Austrian Informationsfreiheitsgesetz (IFG)

Primary text:

- Informationsfreiheitsgesetz:
  https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20012537

The benchmark uses § 4 proactive-publication concepts and § 6 secrecy interests,
including protection of personal data and business secrets. Mixed-content cases
are routed to review for proportionality/redaction analysis instead of assuming
that an entire record must either be disclosed or withheld.

## 5. Austrian NISG transition

Current-law source at the snapshot:

- NISG:
  https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20010536

Future-effective enacted source:

- NISG 2026:
  https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=20013065

The dataset distinguishes the NISG regime in force on 2026-08-17 from NISG 2026
requirements that become applicable on 2026-10-01. NISG 2026 readiness cases
therefore use an evaluation date after 2026-10-01 and are marked
`enacted_future_effective_at_snapshot`.

## 6. Benchmark decision semantics

The labels are governance decisions, not legal judgments in the abstract:

- `allow`: the described action can proceed under the supplied facts/evidence;
- `review`: accountable human, legal, privacy, security or governance assessment
  or missing evidence is required before execution;
- `deny`: the action as stated matches a prohibition or an explicitly
  unacceptable disclosure/security condition.

Researcher-authored labels are provisional. The publication report must remain
`DRAFT — HUMAN VALIDATION REQUIRED` until two independent annotators complete
all cases and an adjudicated label is supplied for every case.

## 7. Machine-checkable controls

`python -m research.legal_audit` verifies that:

- all six partitions total 150 cases and 50 cases per domain;
- source IDs resolve to the versioned registry;
- registered legal sources use primary-law hosts;
- evaluation dates do not predate cited source application dates;
- the Annex III date remains 2027-12-02 unless the source snapshot is explicitly
  updated;
- the source snapshot and verification dates are internally consistent.

A future repository update that changes the legal snapshot should update the
registry, this note, affected cases, tests and paper methodology together.
