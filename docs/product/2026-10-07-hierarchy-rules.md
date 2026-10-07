# Hierarchy rules

Status: draft for owner sign-off, 7 Oct 2026. One page. Applies to every screen a flow slice touches. Tokens and classes come from `design/tokens.json` and `app/static/css/yozora-components.css`. Nothing new was added.

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
- [ ] Scannable: no walls of text. Lists scan, long explanations are collapsed, ids and codes sit below human labels.
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
