---
title: "CyberAssess: Design Revamp + Feature Roadmap — Evaluation Prompt"
type: prompt
model: claude-opus-4-8
date: 2026-06-18
status: ready
---

# CyberAssess — Design Revamp & Feature Roadmap Evaluation

## Purpose

This prompt is a brief for **Claude Opus (claude-opus-4-8)** to evaluate and produce a concrete implementation plan covering:

1. A visual and UX revamp of the CyberAssess web portal
2. The highest-leverage product feature gaps to close
3. A sequenced roadmap for a solo developer with limited time

You are starting cold. Everything you need is in this document.

---

## 1. What CyberAssess Is

CyberAssess is an AI-powered multi-framework compliance gap assessment platform. It encodes how a seasoned auditor actually runs an assessment: reads documents first, forms hypotheses, asks targeted questions, triangulates evidence, and produces a board-ready gap report. The core workflow is:

1. **Scope** — select frameworks (DPDPA, ISO 27001, GDPR, HIPAA, NIST CSF, PCI-DSS), answer applicability questions
2. **Document upload** — PDF/DOCX/images uploaded and processed
3. **Desk review** — AI reads documents, extracts evidence, flags signals, pre-fills questionnaire
4. **Context gathering** — 16 questions to derive risk profile
5. **Adaptive questionnaire** — ~30–40 questions (reduced from 157 via document pre-fills, tier depth, and domain screening)
6. **Gap analysis** — multi-call Claude pipeline produces per-requirement findings
7. **Report** — board-level PDF + RFI document

The adaptive assessment engine (Phase 1/2/3) is complete and is the strongest technical differentiator. It reduces a 5-hour assessment to ~90 minutes.

**Current GTM:** White-glove consulting — the founder (Saqlain) conducts the interview, operates the tool, and delivers the PDF. First 5 engagements free, then paid remediation consulting.

**Target customers:** Vendor companies (100–2,000 employees) serving enterprise clients in banking, insurance, healthcare, who will be audited on DPDPA and related frameworks.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13 + FastAPI (ASGI) |
| Database | SQLite via SQLAlchemy 2.0 (synchronous) |
| Templates | Jinja2 (server-rendered HTML) |
| Interactivity | HTMX (no full-page reloads, partial swaps) |
| CSS | Tailwind CSS (CDN-loaded, no build step currently) |
| AI | Anthropic SDK — Claude Sonnet 4.6 with prompt caching |
| PDF | fpdf2 (custom drawing, 942-line pdf_export.py) |
| Auth | None — single-user MVP |

**Critical constraint:** This is **not** a React/Vue/Next.js app. All rendering is server-side Jinja2. Interactivity is via HTMX partial swaps. Any design or UX solution must work within this architecture. No component library (shadcn, Radix, etc.) can be dropped in — everything is hand-rolled Tailwind HTML.

**Tailwind note:** Currently loaded via CDN play script. For dark mode to work properly, Tailwind needs a config-aware build step (`npx tailwindcss`) so the `dark:` variant can be used. This is a prerequisite that must be addressed.

---

## 3. Existing Design System

A design system already exists at `docs/design.md`. Key decisions:

**Philosophy:**
- Revolut-inspired visual language adapted for B2B compliance/audit context
- One signal per element — color communicates meaning, never decoration
- Flat confidence — no drop shadows on content cards (depth via white-card-on-gray-background)
- Single primary: navy `#1e1e50` — all actions, active states, links

**Color palette:**
- Brand/primary: navy `#1e1e50` (hover: `#2b315a`, dark surface: `#141438`)
- Page background: `bg-gray-50`
- Cards: `bg-white border border-gray-200 rounded-xl`
- Semantic status colors: green (compliant), yellow (partial), red (non-compliant), orange (high risk), blue (planned), gray (N/A)
- Navy scale for tints: `navy-50` through `navy-500`

**Typography:** Inter. Text scale from `text-xs` (badges/metadata) to `text-2xl` (page titles). `text-sm` (14px) minimum for body.

**Components:** Three button variants (primary navy, outlined, destructive text-only). Cards with `rounded-xl`. Status badges with `rounded-full`. Tab bar with `border-b-2`. HTMX transition classes in style.css.

**What the design system does not yet define:**
- Dark mode token mapping
- Empty states (what they look like beyond basic padding)
- Notification/toast system
- Sidebar navigation (currently top nav only)
- Mobile breakpoints beyond basic `sm:` classes
- Skeleton loading states
- Keyboard shortcut indicators

---

## 4. Product Gaps (from Founder Review — 2026-06-18)

A founder-level product review was conducted this session. These are the seven most important gaps between the current state ("impressive assessment engine") and a sellable product. They are ranked by importance.

### Gap 1 — No remediation workflow
The report ends with a gap list. There is no tracked path from "identified gap" → "closed gap." Without this, the output is a one-time PDF, not a workflow. This is the single highest-leverage missing feature for both audiences.

**Minimum viable version:** Per gap item: `status` (open / in_progress / closed), `owner` (text field), `target_date`, `notes`. Not a project management tool. Just enough closure loop.

### Gap 2 — No assessment continuity
Each assessment is an island. No comparison between runs, no delta, no trend. Breaks the re-engagement model. A company has no reason to come back.

**Minimum viable version:** Show delta between two assessments for the same company. One additional view.

### Gap 3 — UCC cluster mappings are empty
The core multi-framework differentiator — "answer once, score across three standards" — is architectural only. The `app/frameworks/mappings/clusters.py` file is empty. The pitch is real, the implementation is not. This is domain/knowledge work, not engineering.

### Gap 4 — No self-serve delivery
Every engagement requires the founder to operate the tool. This caps throughput and does not scale to any commercial model. A consultant must be able to log in independently.

**Requires:** Multi-tenancy basics, client isolation, pricing/billing.

### Gap 5 — No multi-tenancy
Client A's data is not isolated from Client B's. Required before any consultant can safely use the tool for multiple clients. No white-labeling either.

### Gap 6 — Manager review workflow not shipped
AI findings need a human sign-off layer before becoming client-facing output. Planned (P3 in existing execution plan), not built. Without it the product is not professionally defensible.

### Gap 7 — No pricing or billing
There is no way to charge for the product. This is the clearest signal it is currently a consulting accelerator, not a software product.

---

## 5. Design Goals for the Revamp

The founder's stated goals for the design revamp:

1. **Dark mode / light mode toggle** — a proper dark theme, persisted across sessions, toggleable from the UI
2. **Cleaner visual appearance** — reduce visual clutter, improve hierarchy and breathing room
3. **More appealing** — the tool should feel like a premium product, not a side project
4. **Quality of life improvements** — things like keyboard shortcuts, better empty states, progress feedback, copy-to-clipboard, search/filter, collapsible sections
5. **"Cooler to use"** — the interaction experience should feel polished and intentional, not functional-but-bare
6. **Maintain professional character** — this is a B2B compliance tool used by auditors and CISOs. The design improvements must not make it feel like a consumer app. The existing philosophy (flat, confident, navy-primary) is correct and should be extended, not replaced.

The existing design system is a solid foundation. The revamp is an **evolution**, not a replacement.

---

## 6. Key Files (for reference)

```
app/
  templates/
    base.html                        — nav, dark mode toggle lives here
    pages/
      dashboard.html                 — assessment list + create button
      login.html                     — reference implementation for brand feel
    partials/
      scope_form.html                — framework selection + scope questions
      documents_tab.html             — file upload dropzone
      desk_review_running.html       — polling state during desk review
      questionnaire_tab.html         — main questionnaire container
      questionnaire_sections.html    — section list
      section_questions.html         — individual question cards (most UI complexity)
      screening_form.html            — 9-question domain screening
      scope_complete.html            — scope completion state
      report_summary.html            — final gap report view
  static/
    style.css                        — HTMX transition classes, drag-active dropzone, custom scrollbar
docs/
  design.md                          — full design system (color, typography, components, layout)
```

The section_questions.html partial is the most complex UI surface — it renders question cards with tier badges (DEEP/LIGHT), answer sources (document/inferred/human), pre-filled state indicators, collapsible evidence panels, and the GRC 5-option radio scale.

---

## 7. Constraints

- **Solo developer.** No team. Engineering time is the scarcest resource.
- **No build step today.** Tailwind is CDN-loaded. Dark mode via Tailwind `dark:` variants requires switching to a local Tailwind CLI build. This is a one-time setup task, not an ongoing complexity.
- **HTMX-first.** Interactivity via HTMX partial swaps. Minimal custom JS. Any quality-of-life JS should be small, vanilla, and inline-compatible.
- **No new backend frameworks.** FastAPI + Jinja2 stays. No SSE library, no WebSocket upgrade, no background task queue beyond what FastAPI already supports.
- **SQLite stays for now.** No Postgres migration. The database design is not a current constraint.
- **No auth.** Single-user MVP. Multi-tenancy is a future gate, not something to design for now.
- **fpdf2 report is separate.** The PDF report rendering (`pdf_export.py`) is not part of the web UI revamp scope. It has its own rules (all text through `S()` latin-1 sanitizer).

---

## 8. What You Are Being Asked to Produce

Produce a **comprehensive implementation plan** that covers all of the following. Be specific, opinionated, and concrete. Do not hedge. Saqlain is a capable engineer — he does not need hand-holding, he needs direction.

---

### 8.1 — Dark Mode Strategy

Produce a complete dark mode implementation plan for this Jinja2 + HTMX + Tailwind stack.

Include:
- How to set up Tailwind CLI build so `dark:` variants work (replace CDN)
- The dark mode trigger mechanism (toggle button in nav, persisted to localStorage, no page reload)
- The dark token mapping for every surface in the existing design system:
  - Page background
  - Cards
  - Navigation bar
  - Tab bar
  - Buttons (primary, secondary, destructive)
  - Badges and status chips
  - Form inputs
  - Semantic status colors (do they change in dark mode, or stay the same?)
  - Running state banners
  - Alerts
  - Text color hierarchy (gray-900 → gray-700 → gray-500 → gray-400 equivalents in dark)
- Whether the navy primary color changes in dark mode (e.g. lightens to remain accessible on dark backgrounds)
- The Tailwind config setup required (`darkMode: 'class'`, custom color extensions for navy scale)
- Template changes required in base.html
- Any CSS custom properties approach vs pure Tailwind utility approach (recommend one)

### 8.2 — Visual Hierarchy & Cleanliness Improvements

Without changing the design system's philosophy (flat, navy primary, professional), identify the most impactful visual improvements.

Specifically evaluate:
- **Dashboard page:** What makes the assessment list feel cluttered or low-quality? What is the ideal card/row design for an assessment list item?
- **Questionnaire section questions:** This is the most-used surface. What specific changes would make it cleaner and easier to navigate?
- **Report summary:** The gap findings page. What visual improvements would make findings easier to scan and act on?
- **Empty states:** Define what "good" empty states look like for: no assessments, no documents uploaded, no questionnaire responses, analysis not yet run.
- **Loading and progress states:** Skeleton loaders vs spinner-only. What is appropriate for each surface?

For each, give specific Tailwind class changes and layout recommendations. Be concrete.

### 8.3 — Quality of Life Features

Rank and specify the following quality of life improvements by impact/effort ratio. For each, give the implementation approach (HTML/HTMX/vanilla JS).

Evaluate each of:
- **Dark/light toggle** (covered in 8.1, just reference here)
- **Keyboard shortcuts** — which ones make sense for this workflow? (e.g. `?` for help modal, `n` for new assessment, section navigation in questionnaire)
- **Copy to clipboard** — where is this useful? (requirement IDs, RFI text, finding descriptions)
- **Toast/notification system** — for save confirmations, analysis complete, errors. What is the lightest implementation?
- **Search and filter** — on the assessment dashboard list. How to implement without a JS framework?
- **Collapsible sections** — which questionnaire sections should collapse by default? How to persist collapsed state?
- **Progress save indicator** — "autosaved" or "last saved 2 minutes ago" on questionnaire
- **Better breadcrumb navigation** — the current tab-based assessment navigation. Evaluate whether a sidebar would be better than the current top tab bar.
- **Sticky section header** in questionnaire — so the current section name + tier stats remain visible while scrolling
- **Assessment status timeline** — a mini visual timeline showing which pipeline steps are complete. Better than the current status badge.

### 8.4 — Feature Gap Prioritization

Given the 7 gaps above and the design constraints, produce a prioritized build list with effort estimates.

For each item, give:
- Priority rank (1 = do first)
- What to build (concrete scope, not vague description)
- Effort estimate (days, not sprints — be honest)
- Which gap it closes
- Dependencies (what must be done first)
- Specific files/models to change

Focus especially on:
- Gap 1 (remediation tracking) — what is the minimum viable implementation?
- Gap 2 (assessment continuity) — what does the simplest delta view look like?
- Gap 6 (manager review) — this is already detailed in `docs/plans/2026-05-08-001-feat-trusted-platform-four-priorities-plan.md`. Does that plan look right? What would you change?

### 8.5 — Sequencing: Design + Features Together

Produce a concrete 12-week sequence that interleaves design work and feature work.

Constraints:
- Design work and feature work can overlap week-to-week (design improvements to a view can ship alongside feature changes to that view)
- The manager review workflow (Gap 6) should ship before the product is used in any real client engagement
- The dark mode system should be set up early (it's foundational and touches every template)
- The UCC cluster mappings (Gap 3) are knowledge work, not engineering — they can be done async during deep engineering weeks

Format: week-by-week plan. Each week: primary focus, deliverables, what gets deferred.

### 8.6 — Things Not to Build

List anything in the quality-of-life or expansion category that would be a distraction at this stage. Explain briefly why for each. Be opinionated.

---

## 9. Output Format

Produce the plan in Markdown with clear section headers matching the 8.1–8.6 structure above. Use tables where they add clarity (effort estimates, token mappings). Use code blocks for Tailwind class strings, JS snippets, and config. Use numbered lists for sequences. Avoid bullet-point soup — use structured prose where decisions need reasoning.

The output should be usable as a working document — something Saqlain can open while coding and follow step by step without re-reading this brief.
