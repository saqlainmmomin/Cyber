"""Standing guard: the P5-9 held-out evaluation set stays out of the product.

`validation/companies/*/answer_key.json` holds the planted gaps the P5-9
harness scores against (D-P5-9-C). If application code, or the harness's
client-side route runner, could reach it, the evaluation would measure the
answer key rather than the pipeline. This guard makes that structural: only
the harness's lint, model and scoring modules may name the key.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("answer_key", "validation/companies", "scripts.validation", "scripts/validation")
KEY_READERS = {"lint_pack.py", "models.py", "score.py"}


def _source_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".html", ".j2", ".txt", ".md", ".json"}
    ]


def test_app_never_references_the_evaluation_set():
    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {needle}"
        for path in _source_files(REPO_ROOT / "app")
        for needle in FORBIDDEN
        if needle in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == [], offenders


def test_only_harness_scoring_modules_name_the_answer_key():
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in _source_files(REPO_ROOT / "scripts")
        if "answer_key" in path.read_text(encoding="utf-8", errors="ignore")
        and not (path.parent.name == "validation" and path.name in KEY_READERS)
    ]
    assert offenders == [], offenders
