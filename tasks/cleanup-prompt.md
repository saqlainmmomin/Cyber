# CyberAssess Cleanup — Session Prompt

Paste this into a fresh Claude Code session from `~/dpdpa-gap-tool/`:

---

I need to clean up CyberAssess so it reflects its multi-framework identity rather than its DPDPA-only origins. The tool evolved from a single-framework DPDPA gap tool into a 6-framework compliance maturity platform, but the codebase still has DPDPA-specific assumptions baked in. Read the vault note at `01-projects/cyberassess.md` for full architecture context.

## What needs to change

### 1. UI text and branding
The web portal (Jinja2 templates in `app/templates/`) still says "DPDPA Assessment" or "DPDPA Gap Assessment" in several places. It should say "CyberAssess" or "Compliance Assessment" generically. Grep for `DPDPA` across all templates, page titles, breadcrumbs, and headings. The framework name should only appear where the user has actually selected DPDPA as one of their frameworks — not as a default label.

### 2. Scope questions are DPDPA-only
The initial scope questions (in `app/dpdpa/scope_questions.py` and rendered via `app/routers/web.py`) are entirely DPDPA-specific. The tool supports 6 frameworks (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS) — each needs its own relevant scope questions. The framework definitions live in `app/frameworks/definitions/`. The vault note's "Deferred" section already flags this: "Per-framework scope questions in UI (currently only DPDPA scope shown)."

What I want:
- Each framework should have its own set of scope questions relevant to that standard
- When a user creates an assessment and selects frameworks, only the relevant scope questions should appear
- The existing DPDPA scope questions stay for DPDPA — they just stop being the only ones
- Look at how the framework registry (`app/frameworks/registry.py`) works and follow the same pattern: each framework defines its own scope questions in its definition file, the registry aggregates them

### 3. The personal site describes CyberAssess like this (from `~/personal-site/src/components/WorkList.astro`):

**Auditor reading:** "CyberAssess reads the evidence before it asks a single question. Every uploaded document is reviewed first — the tool arrives with a picture of what's already answered, what's partial, and what's missing. Questions then adapt to what actually requires human judgement. Controls that map to multiple frameworks are assessed once, not once per standard."

**Builder reading:** "Six compliance frameworks defined as Python dicts — version-controlled, embeddable directly into Claude's system prompt, never stored in the database. A framework abstraction layer maps overlapping controls into Unified Control Clusters so the questionnaire de-duplicates at the data level."

The tool should match this description end-to-end. Anywhere the code assumes single-framework (DPDPA) when the architecture is designed for multi-framework — fix it.

### 4. Context questions
The 16 context questions in `app/dpdpa/context_questions.py` are also DPDPA-flavored. Some are universal (company size, industry) but others are India-specific. Make these framework-aware — universal context questions that apply regardless of framework, plus per-framework context where needed.

## Ground rules
- Don't break the existing DPDPA flow. Everything that works for DPDPA today should still work.
- Don't restructure the database schema. This is a UI/text/routing cleanup, not a data model change.
- Match the existing code style (Jinja2 + HTMX, no SPAs, full server round-trips).
- Run the app and verify the pages render before marking done. The app starts with `uvicorn app.main:app --reload`. **Important: needs Python 3.13 — install via `brew install python@3.13` if not available.** System Python 3.9 and Homebrew Python 3.14 both have issues.

---
