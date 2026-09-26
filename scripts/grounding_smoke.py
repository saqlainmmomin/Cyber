"""Live smoke for the dormant v2 grounding stages using synthetic fixtures."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.config import settings
from app.frameworks.registry import FrameworkRegistry
from app.services.grounding import SourceDocument, run_stages_0_1
from app.services.grounding.claims import claim_id


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frameworks", default="dpdpa,iso27001")
    parser.add_argument("--fixtures", default="tests/grounding_fixtures")
    parser.add_argument(
        "--out",
        default=str(Path(tempfile.gettempdir()) / "cyberassess-grounding-smoke.json"),
    )
    parser.add_argument("--no-structured", action="store_true")
    return parser.parse_args()


def _sources(directory: Path) -> list[SourceDocument]:
    result = []
    for index, path in enumerate(sorted(directory.glob("*.txt")), start=1):
        with path.open(encoding="utf-8", newline="") as handle:
            text = handle.read()
        result.append(
            SourceDocument(
                source_id=f"ev:smoke-{index}",
                evidence_id=f"smoke-evidence-{index}",
                evidence_version_id=f"smoke-{index}",
                legacy_document_id=None,
                filename=path.name,
                category="other",
                mime_type="text/plain",
                text=text,
            )
        )
    return result


def main() -> int:
    args = _arguments()
    if not settings.openrouter_key:
        print("OPENROUTER_KEY is required for the live grounding smoke", file=sys.stderr)
        return 2
    if args.no_structured:
        settings.v2_structured_output = False
    framework_ids = tuple(item.strip() for item in args.frameworks.split(",") if item.strip())
    sources = _sources(Path(args.fixtures))
    claim_set = run_stages_0_1(sources, framework_ids)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(claim_set.to_json(), encoding="utf-8")

    chunks = {chunk.chunk_id: chunk for chunk in claim_set.chunks}
    source_map = {source.source_id: source for source in sources}
    in_scope = {
        control.id
        for framework_id in framework_ids
        for control in FrameworkRegistry.get(framework_id).all_controls()
    }
    valid = True
    for claim in claim_set.claims:
        source = source_map[claim.source_id]
        chunk = chunks[claim.chunk_id]
        valid = valid and claim.quote == source.text[claim.start:claim.end]
        valid = valid and chunk.start <= claim.start < claim.end <= chunk.end
        valid = valid and bool(claim.requirement_ids)
        valid = valid and set(claim.requirement_ids) <= in_scope
        valid = valid and claim.claim_id == claim_id(
            claim.source_id, claim.start, claim.end, claim.statement
        )

    print(json.dumps(claim_set.metrics, indent=2, sort_keys=True))
    print("calls:")
    for record in claim_set.llm_calls:
        print(
            record.get("stage"),
            record.get("batch"),
            record.get("input_tokens"),
            record.get("output_tokens"),
            record.get("latency_ms"),
            record.get("finish_reason"),
            record.get("status"),
        )
    print("verified claims:")
    for claim in claim_set.claims:
        print(claim.claim_id, claim.framework_ids, claim.support, claim.quote[:120])
    print("rejections:", json.dumps(claim_set.metrics["rejected_by_reason"], sort_keys=True))
    print("output:", args.out)

    required_sources = {source.filename for source in sources if source.filename != "injected_vendor_letter.txt"}
    has_claim_for = {claim.filename for claim in claim_set.claims}
    finish_ok = all(record.get("finish_reason") == "stop" for record in claim_set.llm_calls)
    if not valid or claim_set.status != "complete" or not finish_ok or not required_sources <= has_claim_for:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
