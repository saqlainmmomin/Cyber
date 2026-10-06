---
globs: ["app/services/**", "app/utils/**", "app/dpdpa/**", "app/frameworks/**", "app/routers/**"]
---
# Backend rules

- **All PDF text through `S()`** (latin-1 sanitizer) — missing it crashes fpdf2.
- **Every LLM call site is OpenRouter-tiered** (`app/services/llm_client.py`); prompt-cache passthrough unverified. Vision OCR uses `llm_model_vision`.
- **DPDPA framework lives in Python dicts**, not the database — version-controlled, prompt-embeddable.
- **PDF sections are additive-only** — don't rewrite existing pages.
- **Every LLM call has a wall-clock deadline** (`llm_request_deadline_seconds`, 600 s, one retry): httpx's own timeout never fires on OpenRouter keep-alive stalls.
- **Non-DPDPA scope profiling isn't implemented** — questionnaire exclusion is a no-op for ISO/GDPR/HIPAA/NIST/PCI.
