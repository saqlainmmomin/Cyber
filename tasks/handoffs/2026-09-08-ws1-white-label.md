# WS #1 — Static white-label config (handoff for Codex)

**Plan reference:** `tasks/multi-framework-demo-plan.md` §3 WS #1.
**Branch:** open `ws/1-white-label` off `main`.
**Effort:** 1 day.
**Precondition:** none.

## 1. Goal

Replace every client-visible occurrence of "CyberAssess" / "DPDPA Compliance Gap Assessment" / hardcoded product branding with values read from configuration, so a consulting firm's name, logo, and primary color appear in the navbar, PDF cover, PDF header/footer, RFI documents, and page titles. Default values preserve current branding (backward-compat). Deployment overrides via env vars.

## 2. Files in scope

| File | Change |
|---|---|
| `app/config.py` | Add three settings: `firm_name`, `firm_logo_path`, `firm_primary_hex`. |
| `.env.example` | Add the three vars with commented example values. |
| `app/main.py` | Inject `settings` into Jinja globals so `{{ settings.firm_name }}` works in every template. |
| `app/templates/base.html` | Navbar brand text reads from `settings.firm_name`. |
| `app/templates/pages/login.html` | Header reads from `settings.firm_name`. |
| `app/utils/pdf_export.py` | Cover title, header, footer read from settings. Logo embedded on cover if `firm_logo_path` set. Primary color used for accent rules. |
| `app/utils/rfi_export.py` | Cover title + footer read from settings. |
| `app/utils/evidence_checklist_export.py` | Cover title + footer read from settings. |
| `tests/test_white_label.py` (new) | See §5. |

**Do NOT touch** any other file. If you find another surface still hardcoded, open a follow-up issue, don't extend the PR.

## 3. Interfaces (must exist after the change)

### `app/config.py`

```python
class Settings(BaseSettings):
    # ... existing fields ...
    firm_name: str = "CyberAssess"
    firm_logo_path: str | None = None          # absolute path OR relative to repo root
    firm_primary_hex: str = "#2563eb"          # Tailwind primary-600
```

### Jinja context

Every template rendered by `TemplateResponse` receives `settings` (already a common pattern; if not, add it to a single `templates.env.globals` assignment in `app/main.py` after `Jinja2Templates()` is constructed).

### PDF layer

- `pdf_export.py`'s cover-generation function accepts `settings` (or reads a module-level `get_settings()`); the string previously written as `"CyberAssess Compliance Gap Assessment"` becomes `f"{settings.firm_name} Compliance Gap Assessment"`.
- If `settings.firm_logo_path` is set, embed it at `y=<current cover-title-y> - 25mm`, max width 40mm. If unset, skip silently.
- Accent rule colors that were the hardcoded blue → `settings.firm_primary_hex` (route through the existing `S()` sanitizer if it touches text; for `set_draw_color`, parse the hex to RGB).

### Framework labels are NOT branding

Do NOT rename "DPDPA", "ISO 27001", "NIST CSF" anywhere — those are framework identifiers and stay. Only *product* branding changes.

## 4. Non-goals

- No settings-management UI. Config-file / env-var only.
- No multi-firm dynamic branding. One firm per deployment.
- No full theming — one primary hex, that's it. No secondary color, no font override.
- No logo upload endpoint. `firm_logo_path` is a filesystem path the operator provisions.
- No template refactor beyond the surfaces listed above.
- No changes to framework definitions or any file under `app/frameworks/` or `app/services/`.

## 5. Test to pass

Add `tests/test_white_label.py`:

```python
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

def test_default_branding_preserved(monkeypatch):
    # No env overrides → navbar still says "CyberAssess"
    from app.main import app
    client = TestClient(app)
    r = client.get("/login")
    assert r.status_code == 200
    assert "CyberAssess" in r.text

def test_navbar_uses_configured_firm_name(monkeypatch):
    monkeypatch.setenv("FIRM_NAME", "Momin & Co")
    # Reimport so the settings object picks up the env
    import importlib, app.config, app.main
    importlib.reload(app.config); importlib.reload(app.main)
    from app.main import app as reloaded
    client = TestClient(reloaded)
    r = client.get("/login")
    assert "Momin & Co" in r.text
    assert "CyberAssess" not in r.text

def test_pdf_cover_uses_configured_firm_name(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRM_NAME", "Momin & Co")
    # Generate a PDF from the smallest fixture that pdf_export can consume;
    # if you need a fixture, write one that calls the cover-page function directly
    # with a minimal Assessment stub. Extract text with pypdf and assert.
    from pypdf import PdfReader
    pdf_bytes = _generate_smoke_pdf()   # helper you add
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "".join(p.extract_text() for p in reader.pages)
    assert "Momin & Co" in text
    assert "CyberAssess" not in text

def test_no_hardcoded_product_name_in_client_surfaces():
    """Grep gate: fails if 'CyberAssess' appears outside allowed files."""
    allowed = {
        "app/config.py",                              # default value lives here
        "app/templates/pages/login.html",             # NO — must go through settings
        # If a legitimate exception arises, list it here with a comment.
    }
    result = subprocess.run(
        ["git", "grep", "-l", "CyberAssess",
         "app/templates/", "app/utils/pdf_export.py",
         "app/utils/rfi_export.py", "app/utils/evidence_checklist_export.py"],
        capture_output=True, text=True,
    )
    hits = set(result.stdout.strip().splitlines()) - allowed
    assert not hits, f"Hardcoded 'CyberAssess' still in: {hits}"
```

The grep test is the load-bearing one. If it fails, the branding isn't actually configurable.

## 6. Done criteria

All must be true before you claim done:

1. `pytest -q` green, including `tests/test_white_label.py`.
2. `uvicorn app.main:app --reload` boots without error.
3. With env unset: `GET /login` shows "CyberAssess" in navbar. (backward compat)
4. With `FIRM_NAME="Momin & Co" FIRM_LOGO_PATH=app/static/img/momin-test.png FIRM_PRIMARY_HEX="#8b0000"`:
   - Navbar shows "Momin & Co".
   - New-assessment page shows "Momin & Co" title.
   - Generated PDF cover shows "Momin & Co", embeds the logo, accent rules render dark red.
5. `git grep 'CyberAssess' app/templates/ app/utils/pdf_export.py app/utils/rfi_export.py app/utils/evidence_checklist_export.py` returns zero lines.

You need to provide a real (or placeholder) PNG at `app/static/img/momin-test.png` — a 200×80 black rectangle is fine.

## 7. Rollback

```bash
git revert <commit-sha-of-ws1-merge>
```

No schema changes, no data migrations, no dependencies added. Revert is safe at any point.

## 8. Adversarial review (post-PR)

Reviewer: Claude (or `code-simplicity-reviewer` subagent).

Review prompt:
```
Adversarial review of ws/1-white-label. Verify:
1. All done criteria in tasks/handoffs/2026-09-08-ws1-white-label.md §6 hold.
2. Grep gate has no false-negative exclusions (Codex didn't quietly add an
   allowed path to hide a residual hardcoded string).
3. Backward-compat: an existing deployment with no new env vars renders
   identically to before (open the login page, open a generated PDF cover,
   compare screenshots visually or via text extraction).
4. Single most likely production failure mode.

Output: PASS / FAIL with numbered failures. No hedging.
```
