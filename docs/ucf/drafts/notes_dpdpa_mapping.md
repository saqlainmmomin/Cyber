# DPDPA mapping notes, round 2 (draft, unsigned)
119 rows (100 full, 19 partial) for 98 atoms. 43 new controls: 8 remainder slots (GOV-70, OPS-70, SUP-70, AST-70, AST-71, INC-70, INC-71, INC-72), 35 privacy-only (PNC 13, PRT 7, PUR 4, PGV 4, PSC 7). The validator shows only NIST-side failures.

## Suggested changes to base controls (controls_iso.csv untouched)
- UC-GOV-04 is the only home for the generic "reasonable safeguards" atoms (SECURITY.1-a, -b). A base control for "security measures applied to risk-rated data" would carry them more honestly.
- UC-INC-04 names notifying "authorities and other parties"; add affected individuals so INC-71 is a smaller remainder.
- UC-AST-07 and UC-AST-08: add per-category retention triggers to AST-07 and erasure on request to AST-08 so AST-70 and AST-71 shrink.
- UC-OPS-01: add "access to sensitive data" to the logged events, and a review step.
- UC-RSK-08 carries a record of processing; PURPOSE.2 and CM.RECORDS may fold into it later (not mapped, PUR-02 stands alone).
- UC-SUP-03 does not say "every party that processes data has a signed contract"; SUP-01 register could carry that.

## Atoms not placed cleanly
- SECURITY.1-a, -b: umbrella asks. Mapped partial to GOV-04, OPS-01; backups (RES-04) partial with remainder_immaterial.
- BN.NOTIFY.3-a, -c: detection and investigation have no exact base control; mapped to INC-01 as full, which is generous.
- BN.NOTIFY.3 TC3 (find affected individuals and channels) is tested under INC-71, not an atom of its own.
- CONSENT.3-b (processors stop processing) sits in PNC-12; SUP-70 also requires stop and erase terms in contracts.
- SECURITY.2 criteria accept masking and tokenization; only encryption is mapped (CRY-01). AST-09 not added.
- SDF.4 (privacy audit) is close to RSK-09; kept in PGV-04 because the test differs.
- Inactivity erasure (conditional, 3 years, 48-hour warning) has no atom; park it as AST-70 key_settings and applicability.

## Primary judgment calls
SECURITY.1 (GOV-04 over OPS-70), MINIMIZE.2 and MINIMIZE.3 (AST-08, AST-07 over slots), SECURITY.3 (SUP-03 on -a), CORRECT.2 (PRT-04 over AST-08), BN.NOTIFY.1/2/4 (base INC-04, INC-03 over slots), CB.TRANSFER.2 (PSC-05 on -b), ACCESS.1 (PRT-02 over PRT-01).

## Question reuse plan (curated text seeds the control's `question`)
- CONSENT.1 -> PNC-05 (split: PNC-06, PNC-07, PNC-02 need new wording); CONSENT.2 -> PNC-08 and PNC-09 (split compound); CONSENT.3 -> PNC-11, PNC-12; CONSENT.4 -> PNC-13; CONSENT.5 -> PSC-02.
- NOTICE.1 -> PNC-01 (compound, language split to PNC-02); NOTICE.2 -> PNC-03; NOTICE.3 -> PNC-04.
- PURPOSE.1 -> PUR-01; PURPOSE.2 -> PUR-02; MINIMIZE.1 -> PUR-03; ACCURACY.1 -> PUR-04.
- MINIMIZE.2 -> AST-70; MINIMIZE.3 -> AST-71 (compound: log retention goes to OPS-70).
- SECURITY.1 -> GOV-70 and OPS-70; SECURITY.2 -> CRY-01 and IAM-09 (base wording preferred); SECURITY.3 -> SUP-70.
- ACCESS.1 -> PRT-02 (request channel to PRT-01); CORRECT.1 -> PRT-03; CORRECT.2 -> PRT-04; GRIEVANCE.1/2 -> PRT-05/06; NOMINATE.1 -> PRT-07.
- CHILD.1 -> PSC-03; CHILD.2 -> PSC-04; CHILD.3 -> PSC-01; SDF.1 to SDF.4 -> PGV-01 to PGV-04.
- CM.RECORDS.1 -> PNC-09; CM.RECORDS.2 -> PNC-10; CM.GRANULAR.1 -> PNC-08; CM.GRANULAR.2 -> PNC-06.
- CB.TRANSFER.1 -> PSC-05 (inventory to PSC-06); TRANSFER.2 -> PSC-05 and PSC-07 (compound); TRANSFER.3 -> PSC-07.
- BN.NOTIFY.1 -> INC-70; BN.NOTIFY.2 -> INC-71; BN.NOTIFY.3 -> INC-01 (base wording); BN.NOTIFY.4 -> INC-72.
- The five compound questions (CONSENT.2, NOTICE.1, MINIMIZE.3, TRANSFER.1, TRANSFER.2) each yield one question per target control; do not reuse the bundled text.
