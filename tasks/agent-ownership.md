# Agent ownership: Claude vs Codex

**Applies to:** all workstreams in `docs/plans/2026-09-21-002-revised-implementation-plan.md` (Pre-Work through Phase 4).
**Purpose:** answer "who owns this task, and can it run in parallel with X" without re-deriving it per task. Every handoff file in `tasks/handoffs/` should state its owner per this doc rather than re-justifying the split inline.

## Criteria

Claude owns a task directly, or designs it and reviews the diff before merge, when the task is:
- **Foundational/gating** — later work assumes it's correct (e.g. a schema migration, the Alembic baseline).
- **A security boundary** — tokens, credentials, IAM policy, auth, anything where a subtle mistake is a vulnerability, not a bug (e.g. magic links, AWS AssumeRole).
- **Irreversible or destructive** — permanent deletion, immutable snapshot semantics, anything that can't be undone by re-running the code (e.g. retention purge, issued-report immutability).
- **A product invariant** — the kind of decision that's easy to violate accidentally and hard to notice (no blended cross-framework score, no destructive re-runs, individual-only approval).
- **Judgment/architecture** — needs full codebase context or consulting-domain judgment (UCC cluster mapping, demo narrative design), not a spec that fully determines the output.

Codex owns implementation, from a Claude-written handoff, when the task is:
- **Mechanical** — CRUD routes, templates, seed scripts, boilerplate models from an exact column spec.
- **Fully spec-able** — the plan doc (or the handoff) already pins down every column, transition, and test scenario; there's no open design question left for the implementer.
- **Contained** — touches a narrow, disjoint file set, so a mistake doesn't ripple into other in-flight work.

**Every task, regardless of owner, gets the adversarial review `tasks/todo.md` already gates on** (`[AR: ...]` per phase) before merge — Codex-built work is reviewed by Claude; Claude-built work is reviewed by Codex or a matched subagent. Claude-owned security/destructive tasks get this review even when Claude also wrote the code, since "whoever built it does not review it" still applies — use a subagent (e.g. `security-sentinel`) as the reviewer in that case.

## How to find dependencies and parallel opportunities

Read the task's `Depends on:` / `Blocks:` lines in its handoff file (or, if no handoff exists yet, the plan doc's per-task file lists — tasks with disjoint file lists and no stated dependency can run in parallel). Don't assume phase order implies task order within a phase — several tasks in every phase are independent once their phase's gating task lands.

## Assignments by phase

### Phase 1 — Schema & Hierarchy
| Task | Owner |
|---|---|
| P1-1 Alembic baseline | Claude, drives directly |
| P1-2 Target schema (15 new tables + FKs) | Claude designs → Codex implements |
| P1-3 One-shot migration script | Claude designs + writes tests → Codex implements |
| P1-4 Portfolio dashboard | Codex, from Claude handoff |
| P1-5 Deprecate blended scoring | Codex, from Claude handoff |
| P1-6 Backup/restore scripts | Codex, standalone |

Chain: P1-1 → P1-2 → {P1-3, P1-5 in parallel} → P1-4. P1-6 independent from day 1.

### Phase 2 — Evidence & Conclusions
| Task | Owner |
|---|---|
| P2-1 Evidence service (hashing, lifecycle state machine, legacy-document migration) | Claude designs + writes tests → Codex implements (handoff: `tasks/handoffs/2026-09-23-p2-1-evidence-service.md`) |
| P2-2 Citation model | Codex, from Claude spec |
| P2-3 Immutable analysis pipeline | Claude designs → Codex implements, Claude reviews |
| P2-4 Consultant approval workflow + optimistic locking | Claude designs locking logic → Codex builds UI/routes |
| P2-5 Magic links (client upload) | Claude designs + reviews security → Codex implements |
| P2-6 Workpaper view | Codex, from Claude spec |

Chain: P2-1 gates everything. After P2-1: {P2-2 → P2-3 → P2-4} and {P2-5} are independent parallel lanes. P2-6 depends on all of the above.

### Phase 3 — Reports & Remediation
| Task | Owner |
|---|---|
| P3-1 Findings and Actions | Claude designs history pattern → Codex implements |
| P3-2 Report snapshots (immutability) | Claude designs → Codex implements |
| P3-3 PDF updates | Codex, from Claude spec, Claude reviews rendered output |
| P3-4 Remediation tracking | Codex, from Claude spec |

P3-1 and P3-2 have no file overlap — run in parallel. P3-3 depends on P3-2's snapshot plumbing for final wiring (content changes can be coded in parallel). P3-4 depends on P3-1.

### Phase 4 — AWS & Validation
| Task | Owner |
|---|---|
| P4-1 AWS evidence adapter | Claude designs IAM/security boundary → Codex implements boto3 plumbing |
| P4-2 Longitudinal synthetic demo | Claude designs narrative/data shape → Codex implements seed script |
| P4-3 Performance benchmarks | Codex, standalone |
| P4-4 Retention/archive/purge | Claude designs → Codex implements, Claude reviews (most destructive code path in the plan) |

All four are independent subsystems — run concurrently once Phase 3 lands.

### Phase 6 — Grounded analysis & deliverables
| Task | Owner |
|---|---|
| P6-1 LLM plumbing | Claude designs → Codex implements, Claude reviews (handoff `tasks/handoffs/2026-09-25-p6-1-llm-plumbing.md`) |
| P6-2a/b/c Test criteria (DPDPA → ISO → NIST) | Claude drafts (regulatory judgment) → **Saqlain signs off every criterion**; P6-2b converter can go to Codex |
| P6-3 v2 claims + grounding, P6-4 v2 judge | Claude designs + writes contract tests → Codex implements, Claude reviews |
| P6-6..P6-10 Deliverables | Claude specs report content/layout → Codex implements |
| P6-11..P6-14 Security, Bedrock, deploy | Claude designs security boundary → Codex implements; reviewed by a security subagent |

P6-1 and P6-2a run in parallel (disjoint files). P6-3 needs P6-1; P6-4 needs P6-3 and the approved DPDPA criteria.
