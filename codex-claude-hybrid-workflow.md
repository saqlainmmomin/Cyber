---
title: Codex + Claude Hybrid Workflow
created: 2026-04-05
type: reference
tags: [ai, workflow, claude, codex]
---

# Codex + Claude Hybrid Workflow

## Core Decision

Keep `Claude Code` as the primary orchestrator.
Use `Codex` as a specialist, not a co-equal generalist.

The split:

- **Claude Code**: planning, implementation, subagent orchestration, context-heavy work, project memory, house style
- **Codex**: adversarial plan review, diff review, second-pass debugging, independent verification

This fits the existing brain system better than trying to make Codex the default builder.

## Why This Fits My Setup

My current workflow already assumes:

- plan mode by default for non-trivial work
- subagents for research and parallel analysis
- Obsidian as durable memory
- short `CLAUDE.md`, deeper context in linked notes
- verification before marking work done

That architecture is Claude-native.
Claude is the better tool for operating inside a long-lived memory and process system.

Codex adds value when it is used as an external critic:

- less attached to the current implementation path
- good for forcing explicit reasoning on edge cases
- useful as a second pass when Claude is circling

## Recommended Division of Labor

### 1. Claude for Planning and Build

Use Claude for:

- requirements shaping
- implementation planning
- architecture tradeoffs
- code changes
- coordinating subagents
- integrating with Obsidian-backed context

Claude remains the "brain."

### 2. Codex for Plan Critique

Before coding, hand Codex the plan and ask it to look for:

- hidden assumptions
- missing edge cases
- migration and deployment risks
- failure modes
- missing tests

This is not brainstorming.
It is adversarial review before implementation.

### 3. Codex for Diff Review

After Claude implements, use Codex to review:

- correctness
- regressions
- security issues
- performance risks
- data integrity risks
- missing test coverage

Codex should be instructed to ignore low-value style feedback.

### 4. Codex for Stuck Debugging

If Claude has tried one or two fixes and is looping, switch to Codex with:

- failing command
- logs
- changed files
- observed behavior

Ask for root cause plus the smallest robust fix.

### 5. Claude for Final Integration

Once Codex returns findings:

- Claude applies fixes
- Claude runs verification
- Claude updates any durable lessons or workflow notes

## The Practical Workflow

### Phase 1: Plan in Claude

Claude:

- reads local context
- uses vault memory where needed
- creates implementation plan

### Phase 2: Critique the Plan in Codex

Codex reviews the plan before coding starts.

Goal:

- catch blind spots early
- reduce rework
- force better test thinking

### Phase 3: Build in Claude

Claude executes the plan using the existing workflow:

- plan mode
- subagents where useful
- vault-aware context
- verification mindset

### Phase 4: Review in Codex

Codex reviews the resulting diff as a skeptical staff engineer.

### Phase 5: Fix and Verify in Claude

Claude integrates the findings, re-runs tests, and closes the loop.

## Prompt Templates

### Codex Prompt: Review a Plan

```text
Review this implementation plan like a skeptical staff engineer.

Find:
- hidden assumptions
- missing edge cases
- likely regressions
- migration/deployment risks
- test cases that should exist before merge

Do not rewrite the whole plan.
Return only high-signal issues and concrete corrections.
```

### Codex Prompt: Review a Diff

```text
Review this change set for bugs, regressions, security issues, data integrity risks, edge cases, and missing tests.

Prioritize findings by severity.
Ignore low-value style comments unless they materially affect correctness.
Be concrete: point to the exact failure mode.
```

### Codex Prompt: Investigate a Stuck Bug

```text
Claude attempted this fix and it still fails.

Repro:
<command>

Observed behavior:
<error/logs>

Files changed:
<paths>

Investigate root cause.
Do not propose broad rewrites unless necessary.
Return the most likely cause, proof, and the smallest robust fix.
```

## Rules of Use

- Do not use both models for the same broad task at the same time.
- Do not ask Codex to replace the full Claude workflow.
- Use Codex where independence matters more than memory.
- Use Claude where continuity, context, and orchestration matter.
- Default to manual handoff before automating anything.

## What Not to Do

- Do not build an elaborate Claude↔Codex automation loop before proving the manual workflow helps.
- Do not turn Codex into another planning agent when Claude already owns planning.
- Do not save generic internet facts into the vault.
- Save only conclusions that are specific to my workflow and preferences.

## One-Week Trial

Run this manually for one week:

1. Claude writes the plan
2. Codex critiques the plan
3. Claude implements
4. Codex reviews the diff
5. Claude fixes and verifies

Then evaluate:

- Did Codex catch real issues Claude missed?
- Did the review improve outcomes enough to justify the extra step?
- Did the handoff create friction or clarity?

## Current Conclusion

For my setup, the best hybrid is:

**Claude as builder and orchestrator. Codex as critic and verifier.**

That preserves the value of the existing brain system while adding a strong second-pass review layer.
