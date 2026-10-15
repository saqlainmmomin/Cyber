# NIST CSF mapping notes (round 2)

Draft, unsigned. Written by the NIST drafting agent. 307 rows, 27 new controls (UC-xxx-40 to 69 range).

## Suggested base-control changes (controls_iso.csv not edited)
- UC-RSK-06: add "each entry has a named owner" to the goal (GV.OC-03-b is partial with an immaterial remainder).
- UC-PPL-03: add "checks that awareness worked, for example knowledge checks or phishing simulations" (PR.AT-01-d, immaterial remainder).
- UC-AST-01: say the inventory covers software, services and systems, and records location and classification for information (ID.AM-02, ID.AM-07 map there as req_smaller).
- UC-OPS-01 and UC-OPS-02: log retention sits in -01 and log protection in -02; PR.PS-04-c asks for both in one atom and is mapped only to -02.
- UC-GOV-06 goal does not say the policy reflects organizational context (GV.PO-01-b mapped req_smaller).
- UC-SUP-03: goal could name the scope of access and data granted to the supplier (GV.SC-06-b maps there, soft).

## Atoms not placed cleanly (judgment, mapped full but soft)
- Round 3: INC-42 (recovery and closure, 8 atoms) and OPS-41 (alert analysis, 8 atoms) relieve INC-03 and OPS-03. RC.RP-03/04/05 stay on RES-42 and RES-01/02 (integrity and objectives are other tests); RC.CO atoms stay on GOV-14.
- GV.SC-06-b (relationship planning): SUP-03.
- DE.CM-01-c (rogue device and wireless detection): OPS-03.
- DE.AE-07-b (asset context in analysis): OPS-41.
- DE.AE-06-c (responder access to log platform): OPS-41.
- DE.CM-03-c (personnel told they are monitored): AST-02 acceptable use.
- PR.PS-04-c: two asks (retention, protection) in one atom.
- PR.PS-06-d: GOV-17 is generic; no development-specific measurement control exists.
- ID.AM-07-c: classification scheme plus labels maps only to AST-05.
- ID.IM-01-a: self-assessment is mapped to the internal audit control, which is narrower.
- GV.OC-02-c, GV.RM-07 (opportunities): mapped to GOV-02 and GOV-10 as the nearest homes.

## Primary judgment calls
- GV.RR-01: primary on -c (GOV-05 leadership), not -a (GOV-07 roles), because the record is about leaders owning risk and culture.
- PR.DS-01: primary on -b (CRY-01 encryption).
- ID.AM-07: primary on -b (AST-01 inventory, not classification).
- ID.IM-03: primary on -a (INC-05 lessons learned).
- GV.RM-02: primary on -a, the new appetite slot (no base control holds it).
- DE.AE-02, DE.AE-03, DE.AE-06, RS.MA-05, RC.RP-01, RC.RP-06: primary moved with atom -a to the new OPS-41 and INC-42 slots.
- GV.RR-04, PR.PS-03, PR.PS-05: primary is the partial row to the base control; the slot completes it.
- GV.PO-01: primary is GOV-06 policy set (atom -a), not the enforcement row.

## Slot design
- Pure remainder slots (only reached through partial base rows): IAM-40, IAM-41, PPL-40, INC-40.
- Mixed slots (remainder for some atoms, NIST-only for others): RSK-42, AST-41, AST-43, CRY-40, NET-40.
- GOV-41 is a shared communication slot: four atoms ask that a specific artifact reach the people who act on it, and no base control owns that.
- Equal/full rows to slots mean the slot goal was written for that atom; this is by design, not an overclaim.
