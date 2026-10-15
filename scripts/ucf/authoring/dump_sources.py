#!/usr/bin/env python3.13
"""Dump the existing framework definitions (records, signed criteria, curated questions, evidence requests)
to JSON so authoring briefs can use them. Run from the repo root with Python 3.13.
Output dir: $UCF_SRC_DIR (default /tmp/ucf_src)."""
import json, os, sys
sys.path.insert(0, ".")
from app.frameworks.definitions.iso27001 import ISO27001_DEFINITION as I
from app.frameworks.definitions.nist_csf import NIST_CSF_DEFINITION as N
from app.frameworks.definitions.dpdpa import DPDPA_DEFINITION as D

out = os.environ.get("UCF_SRC_DIR", "/tmp/ucf_src")
os.makedirs(out, exist_ok=True)
for key, d in (("iso27001", I), ("nist_csf", N), ("dpdpa", D)):
    recs = []
    for dk, dom in d.domains.items():
        for sk, sec in dom.sections.items():
            for c in sec.controls:
                q = d.questions.get(c.id)
                recs.append(dict(
                    id=c.id, title=c.title, desc=c.description, ref=c.reference, crit=c.criticality,
                    domain=dk, domain_title=dom.title, section=sk, section_title=sec.title, tags=c.tags,
                    question=q.question if q else "", guidance=q.guidance if q else "",
                    criteria=[dict(id=t.id, stmt=t.statement, kind=t.kind, hint=t.evidence_hint, basis=t.source_basis)
                              for t in c.test_criteria]))
    json.dump(recs, open(f"{out}/{key}_records.json", "w"), indent=1)
    json.dump([dict(type=e.document_type, label=e.label, reason=e.reason, required=e.required, maps_to=list(e.maps_to))
               for e in d.evidence_requests], open(f"{out}/{key}_evidence.json", "w"), indent=1)
    print(key, len(recs), "records")
