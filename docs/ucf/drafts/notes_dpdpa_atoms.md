# DPDPA atoms, round 1 notes (draft, unsigned): 98 atoms, 41 records, ids and references unchanged

## (a) Compound questions and how they were split
The five questions in questionnaire.py that bundle the most separate obligations:

1. CH2.CONSENT.2 asks "itemise each purpose" and "record consent per purpose": -a itemize, -b record.
2. CH2.NOTICE.1 asks for one notice covering data, purpose, withdrawal and rights, complaint route, standalone readability (the pack's signed criteria add language): -a timing, -b data, -c purposes, -d withdraw and rights, -e complain to Board, -f standalone, -g language.
3. CH2.MINIMIZE.3 asks for a schedule, deletion procedures and the minimum retention of logs: -a schedule, -b erasure procedure, -c minimum retention, -d settings match schedule.
4. CB.TRANSFER.1 asks for "only to non-restricted countries" and "maintain an inventory": -a, -b.
5. CB.TRANSFER.2 asks for tracking notifications, no transfer to restricted countries, and sectoral law: -a, -b, -c.
Also split, but lighter: CONSENT.3 (withdraw, then stop processing), SECURITY.2 (encrypt at rest, in transit, least privilege), SECURITY.3 (contract exists, safeguards clause, instructions clause), GRIEVANCE.2, CORRECT.2, BN.NOTIFY.3 (one atom per plan stage), BN.NOTIFY.4.

## (b) Tag per record
| Tag | Records (count) |
|---|---|
| overlap-with-security-base | CH2.SECURITY.1, CH2.SECURITY.2, CH2.SECURITY.3, CH2.MINIMIZE.2, CH2.MINIMIZE.3, CH3.CORRECT.2, BN.NOTIFY.1, BN.NOTIFY.2, BN.NOTIFY.3, BN.NOTIFY.4 (10) |
| privacy-only | the other 31: CH2.CONSENT.1-5, CH2.NOTICE.1-3, CH2.PURPOSE.1-2, CH2.MINIMIZE.1, CH2.ACCURACY.1, CH3.ACCESS.1, CH3.CORRECT.1, CH3.GRIEVANCE.1-2, CH3.NOMINATE.1, CH4.CHILD.1-3, CH4.SDF.1-4, CM.RECORDS.1-2, CM.GRANULAR.1-2, CB.TRANSFER.1-3 (31) |

Borderline: CB.TRANSFER.3 (localization) tagged privacy-only as the plan lists cross-border there. CH4.SDF.2 and SDF.4 (audit) are privacy-only but may meet an internal-audit control in the security base. CH2.ACCURACY.1 may touch data integrity controls.

## (c) Pack versus Act, flags only (no id or reference changed)
None of these forces an id change. Several change a stored reference; Saqlain to verify. Most are noted in the signed criteria basis fields.

- CH2.CONSENT.3: stored 6(4), 6(6); criteria say withdrawal is s.6(4) and the Consent Manager text is s.6(7).
- CH2.CONSENT.4: stored 6(8)-(9); Consent Manager registration may start at s.6(7).
- CH2.NOTICE.3: stored 6(3), 8(9) and r.9; an earlier pack version cited s.5(1). Criteria say the contact duty sits in 6(3), 8(9), r.9.
- CH2.MINIMIZE.1: stored s.6(1); the repo previously cited s.4(1). The Act has no general minimization duty for s.7 uses.
- CH2.SECURITY.1: criteria say the duty is s.8(5), not s.8(4). Check the record's stored reference.
- CH2.SECURITY.2: the Rules accept any of four measures; the pack requires encryption specifically.
- CH3.CORRECT.2: pack scopes erasure to data "no longer necessary"; the Act allows a request at any time, with retention only for purpose or law.
- CH4.CHILD.1 and CH4.CHILD.2: the pack once swapped s.9(2) and s.9(3). Current stored refs (9(3), 9(2)) match the criteria; confirm.
- CH4.CHILD.3: stored "Section 9"; age and guardian checks come from Rules r.10 to r.12, not a Section 9 subsection.
- CH4.SDF.3 and CH4.SDF.4: stored (c)(i) and (c)(ii) are right; the repo once cited a non-existent s.10(2)(d). The Rules r.13(3) duty has no home record.
- CB.TRANSFER.2: the Act uses a restricted-country model (s.16(1)); the pack's signed criteria require transfer contracts, which is practice. The sectoral-law clause is s.16(2), not stored.
- CB.TRANSFER.3: localization is not in s.16(1) text; stored "Section 16" is broad. Confirm the source.
- BN.NOTIFY.1: the 72-hour period comes from the Rules, not s.8(6). BN.NOTIFY.3 (incident response plan) and BN.NOTIFY.4 (register) are practice or Rules-derived, not s.8(6) text; stored 8(4)-(6) and 8(6) may be loose.
- CM.RECORDS.2: the pack's "refresh after a reasonable period" has no basis in the Act; not atomized.
- CH2.CONSENT.2 and CM.GRANULAR.1 duplicate each other; kept as separate records.
