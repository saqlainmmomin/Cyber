# Hierarchy rules

Status: draft for owner sign-off, 7 Oct 2026. One page. Applies to every screen a flow slice touches. Tokens and classes come from `design/tokens.json` and `app/static/css/yozora-components.css`. Nothing new was added. Builders follow this page together with `yozora-design-system.md`, whose Patterns section points here.

## 1. Type scale

| Role | Use | Token and class |
|---|---|---|
| Page title | One per screen | `h1` (28, weight 500) in `.page-head` |
| Section heading | Groups on a page | `h2` (16, 600), or `h3` (14, 600) inside a card |
| Primary value or status | The thing to see first: a status, a count, what is missing | `.big-n` (16, 500), `.pill`, `.status`, `.stat` |
| Body | Normal reading text | 14, `--text` |
| Secondary or meta | Help text, dates, ids, codes | `.sub` or `.t-sub` (13, `--muted`); codes 12 muted |

Hierarchy comes from size, weight and spacing only. No caps, no extra colours.

## 2. One obvious next action

- Each screen state has one `.btn.primary`. It sits last in the page header actions, or inside the next-step banner. Never a disabled primary.
- Every other action is `secondary` or `ghost`, and smaller where it helps.
- When the next step is a different screen, use the `next_step` macro at the top of the content.

## 3. Done state for every step

Nothing finishes silently. A finished step shows all three:
1. The item shows a check (`done_state` macro, or a `.pill` that says "Done").
2. A toast confirms the save (`toast("Scope saved")` into `data-global-toasts`).
3. The stepper stage gets its tick (`stepper` stage with `state: "done"`).

## 4. How an evidence or RFI item is written

Human label first, in the title. Id or code goes in small muted text, in detail views only. Then one plain sentence saying why we ask.

- Good: **Information security policy.** "Shows who approves security rules and how often they are reviewed." `A.5.1`
- Bad: **A.5.1 ISMS-POL-01.** "Evidence for control A.5.1."
- Good: **List of cloud providers.** "We use it to decide which cloud controls apply."
- Bad: **EV-0042 Cloud inventory.** "Required."

## 5. Design-pass checklist

Copy into the PR once per screen.

```
Screen: <name>
- [ ] Orientation: in 3 seconds I can tell where I am, what is done and what to do next. There is one clear primary action.
- [ ] Priority: status, counts and what is missing come first and are the most prominent. Supporting text is smaller and lighter.
- [ ] Scannable: no walls of text. Reasons are `--text-2`, not muted. Meta is muted. One status pill plus one marker per item. Ids and codes sit below human labels.
- [ ] Done states: completed steps show a check, a toast and a stepper tick. Nothing finishes silently.
- [ ] Wording: only the frameworks in this assessment are named.
Before/after screenshots (demo company): attached
```

## 6. Macro usage

Both live in `app/templates/components/ui.html`.

```
{% from "components/ui.html" import done_state, next_step %}
{{ next_step("Prepare the RFI", rfi_url, "Prepare RFI", "12 items suggested from your scope") }}
{{ done_state("Scope complete", "Saved 7 Oct 2026") }}
```

`detail` is optional on both. In `done_state` it is a short fact (a date or count), not a sentence. `next_step` renders the only primary button, so do not add another.

## 7. Dense lists and long text

Applies to every list, table and question card. It amends the earlier use of `.help` for question guidance: guidance is a reason (tier 2), not a hint.

1. **Three text tiers.**
   - Title: `--text`, weight 500 (`.t-title`, or `<b>` in `.rows .txt`).
   - Reason, the sentence the user must read to act (what to provide, why we ask, how to answer): `--text-2`, never `--muted`. The target is 14px with a 70ch cap, which arrives as a `.reason` class in the next design pass. Until then use `.sub` with `--text-2`, as the approved RFI mockup does.
   - Meta (ids, dates, counts, group, source): `.sub`, muted. `.help` (12px) is for field hints only.
2. **List row (`.rows`).** Title, one reason, one meta line. Status and actions sit in a right column, top-aligned, and wrap below the text on narrow screens. Framework tags are `.chip`s on the meta line.
3. **Question card (`.qcard`).** The question, its guidance as a reason, then the answers. Supporting detail (confidence, notes, evidence) stays under the answers.
4. **Badges.** At most one status `.pill` and one other marker (`.warn` or `.ai`) per item. Framework tags are `.chip`s, or plain text when there are more than two.
5. **Table or list.** Use a table when items share three or more comparable fields, with numbers in `td.n`. Otherwise use `.rows`.
6. **Never truncate a reason.** Ellipsis is only for names whose full text is one click away. A reason longer than about 25 words is a content bug against its generator, not something to fix in CSS.

Open until after the full-app test: collapsing question-card detail by default; the `.reason` class and 70ch cap; lint tests for tiers and badge count; the focus-ring fix; an inline-style policy.
