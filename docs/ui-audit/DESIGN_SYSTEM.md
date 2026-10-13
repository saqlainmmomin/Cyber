# Target design system

Opaque neutral surfaces, readable audit text and a stable app frame replace the current glass system. This is the target contract for migration, not a change to production tokens.

## Second-pass amendment (13 Oct 2026, approved by Saqlain)

Saqlain reviewed the first prototypes, rejected their text hierarchy and both navigation options, and approved the redrawn questionnaire, review queue and stepper. Where this section and the rest of this document disagree, this section wins. The source of truth for values is `docs/ui-audit/prototypes/prototype.css`; the six prototype screens show the intended result.

**Type roles.** Seven roles, each a fixed size, line-height and weight. No other font size is allowed.

| Role | Size / line-height / weight | Used for |
| --- | --- | --- |
| Title | 26px / 1.2 / 600 | The one thing the view is about: page title, or the selected finding's gap title |
| Heading | 20px / 1.35 / 600 | A section; the question being asked |
| Lead | 18px / 1.5 / 400 | The statement to read first: gap statement, executive summary. Recommendation text is Lead at 600 |
| Body | 16px / 1.55 / 400 | Anything read as a sentence |
| UI | 14px / 1.45 / 400 | Controls, rows, navigation |
| Caption | 13px / 1.4 / 400 | Identifiers and supporting facts |
| Overline | 12px / 1.3 / 500, uppercase, 0.06em | Section labels inside a card or finding |

Section labels inside content are overlines. The content under a label carries the weight, never the label. This replaces the earlier rule that all audit content is at least 14px: sentences are 16px or larger, and only identifiers, counts and labels use Caption or Overline.

**Measure.** Reading text is capped at 42rem (about 75 characters at 16px). The question text and table cells may run wider; Saqlain asked for the question to use the full block. This replaces the 56ch cap.

**Grouping.** Space first, a background shape second, a hairline last (tables and dense lists only). Surfaces are white on the grey page with a 1px shadow ring, no border. One shaded block per view marks the thing that matters most (the recommendation, the answer area).

**Status.** A shape and a word in the status colour, never a filled pill: diamond for high or critical, half circle for partial or medium, filled circle for compliant or done, hollow circle for low, neutral or not started. The four status families stay.

**Actions.** One filled button per view. Secondary actions are outlined. A destructive action is plain red text.

**Navigation.** This replaces options A and B and every mention of a Section select.
- A stepper replaces the stage bar: Overview, Scope, Evidence, Questionnaire, Review, Report, numbered, with a tick on completed stages. Every step is a link; it is not a forced wizard.
- The open stage shows its sections inline beside its name as a segmented group (Review: Queue, Conclusions, Findings, Workpaper; Evidence: Documents, Requests, Client links; Scope: Boundaries, Applicability). There is still never a second bar.
- A single context line above the stepper carries the breadcrumb and the period and cut-off. The separate assessment header block is gone.
- The global sidebar can be hidden with a button at the start of the context line. The state persists per user. Domain navigation inside the questionnaire stays visible when the sidebar is hidden.
- At 1340px and below the stepper tightens its gaps so the widest stage (Review, four sections) fits at 1280 with the sidebar open.

**Per screen.**
- Questionnaire: questions in a domain are one-line rows (code, control name, response state); the open question shows the requirement as Heading, then "Rationale" and "Steering the response" side by side, then the answer area as the shaded block. The domain rail shows answered counts.
- Review queue: list grouped into "To decide" and "Decided"; the detail leads with the gap title as Title, then one strip (compliance, risk, decision, proposed by), then gap, impact and the shaded recommendation; evidence, interviews and control sit in a quieter aside.
- Conclusions: assessment sheet table; rows with a gap are heavier than rows without; "With a gap" filter and "Highest risk" sort; an open row uses the review detail layout.
- Evidence requests: "In this RFI" and "Not yet requested" lists with sortable headers, evidence already held as a count and bar, and one filled "Generate RFI version" action.
- Report: executive summary as Lead with the score and gap counts as facts beside it; domain table weakest first; high-risk gaps shown in full, medium-risk gaps as one-line rows that open; auditor detail as a filterable list of all controls.
- Applicability: three counts, the standard justification stated once, the excluded controls with reasons, and a form to exclude another.

## Colour and surface tokens

Names are semantic CSS variables. Surface steps are opaque. Borders separate regions; control borders also identify input boundaries. No backdrop blur, gradient, tinted full-page canvas or decorative elevation.

| Token | Light | Dark |
| --- | --- | --- |
| background | #F4F5F7 | #101318 |
| surface | #FFFFFF | #181D25 |
| surface-subtle | #EEF0F3 | #202733 |
| surface-raised | #FFFFFF | #272F3D |
| border | #CFD4DC | #465164 |
| border-control | #707B8C | #8490A4 |
| text | #17202E | #F2F4F8 |
| text-secondary | #3E4B60 | #CCD3DF |
| text-muted | #566174 | #ADB9CC |
| focus | #1F4FD1 | #A6C0FF |

Primary, secondary and muted text may appear only on these four background/surface steps. All 24 text/surface pairs pass 4.5:1. Exact ratios, including all 64 accent-text/surface pairs and 16 button pairs, are in [target contrast](target-contrast.json), computed with the sRGB functions in [contrast.py](tools/contrast.py). Disabled controls retain readable wording; opacity never reduces audit content. Border-control and focus rings use the dedicated values, not the subtle divider.

## Eight accents

Keep today's button hues from design/tokens.json. Dark accent-text is now explicit for every preset, fixing the seven inherited light text pairs. Light button text is white; dark graphite button text is #141824 and other dark button text is white. Accent-text is for links and selected interaction, never status. Buttons retain the base hue in hover state and underline/outline state changes rather than reducing contrast through colour mixing.

| Preset | Light fill | Light text | Light text/white ratio | Dark fill | Corrected dark text | Dark text worst surface ratio |
| --- | --- | --- | --- | --- | --- | --- |
| graphite | #1E2330 | #1E2330 | 15.69 | #E6E9EF | #E6E9EF | 11.07 |
| azure | #0767C2 | #0767C2 | 5.63 | #1C6EC4 | #8EC5FF | 7.42 |
| cobalt | #1F4FD1 | #1F4FD1 | 6.78 | #345DDB | #A6BDFF | 7.27 |
| midnight | #1C3A72 | #1C3A72 | 11.07 | #33508C | #A5BDE9 | 7.09 |
| teal | #0B6E7F | #0B6E7F | 5.91 | #0E7686 | #80CEDB | 7.54 |
| violet | #6A3FD0 | #6A3FD0 | 6.49 | #6A48D6 | #C6A7FF | 6.65 |
| plum | #862D78 | #862D78 | 7.89 | #97398A | #E8A5DF | 6.97 |
| slate | #3C506E | #3C506E | 8.19 | #4A5E80 | #B5C5E0 | 7.71 |

For button text, validate the on-accent/fill pair separately from link text. Selection uses a neutral surface plus border and current-state wording; it need not fill the row with the accent. A focus indicator is a solid 2px outline with 2px gap. Elevated surface supports menus and dialogs only. The content behind an overlay is inert.

## Four status families

A badge accepts a family and a member, not a free-form colour. The same wording is used on list and detail. Semantic roles stay fixed across accents; theme-specific foreground/background pairs improve contrast. Icons supplement text. Never infer compliance from progress or AI provenance.

| Family | Wording/member | Icon | Light foreground | Light background | Ratio | Dark foreground | Dark background | Ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Severity | Critical | Octagon alert | #8F1717 | #FDE8E8 | 7.77 | #FFC1C1 | #401B21 | 9.77 |
| Severity | High | Triangle alert | #9A3412 | #FFF0E6 | 6.56 | #FFC9A8 | #40271E | 9.28 |
| Severity | Medium | Triangle alert | #744900 | #FFF4CF | 7.08 | #FFE09A | #3A3018 | 10.14 |
| Severity | Low | Circle down | #25553D | #E6F3EA | 7.51 | #B9E7CA | #19372B | 9.46 |
| Outcome | Compliant | Check circle | #20563C | #E5F3EA | 7.46 | #B9E7CA | #19372B | 9.46 |
| Outcome | Partially compliant | Circle half | #744900 | #FFF4CF | 7.08 | #FFE09A | #3A3018 | 10.14 |
| Outcome | Non-compliant | X circle | #8F1717 | #FDE8E8 | 7.77 | #FFC1C1 | #401B21 | 9.77 |
| Outcome | Insufficient evidence | File question | #45546B | #EDF0F5 | 6.73 | #CED8E8 | #283243 | 8.98 |
| Outcome | Not applicable | Minus circle | #45546B | #EDF0F5 | 6.73 | #CED8E8 | #283243 | 8.98 |
| Progress | Pending | Clock | #744900 | #FFF4CF | 7.08 | #FFE09A | #3A3018 | 10.14 |
| Progress | Draft / Saving / Running | Loader | #294B7A | #E8F0FC | 7.68 | #BED5FF | #1D304C | 8.96 |
| Progress | Saved / Complete / Approved / Issued | Check | #20563C | #E5F3EA | 7.46 | #B9E7CA | #19372B | 9.46 |
| Progress | Failed / Rejected | X | #8F1717 | #FDE8E8 | 7.77 | #FFC1C1 | #401B21 | 9.77 |
| Progress | Blocked / Locked / Expired | Lock | #45546B | #EDF0F5 | 6.73 | #CED8E8 | #283243 | 8.98 |
| Progress | Edited and approved / Reopened | History | #294B7A | #E8F0FC | 7.68 | #BED5FF | #1D304C | 8.96 |
| Provenance | AI proposed | Sparkless diamond | #58377E | #F1EBFA | 7.96 | #D8C0F4 | #30223F | 8.95 |
| Provenance | Document supported | File text | #294B7A | #E8F0FC | 7.68 | #BED5FF | #1D304C | 8.96 |
| Provenance | Interview recorded | Message square | #45546B | #EDF0F5 | 6.73 | #CED8E8 | #283243 | 8.98 |
| Provenance | Auditor verified | User check | #20563C | #E5F3EA | 7.46 | #B9E7CA | #19372B | 9.46 |
| Provenance | Source unresolved / Superseded | File warning | #744900 | #FFF4CF | 7.08 | #FFE09A | #3A3018 | 10.14 |

Not assessed is outcome-neutral; Available, Superseded and Excluded are evidence lifecycle/provenance labels, not Compliant. Missing and Contradictory evidence are explicit warning labels in the provenance family. Uploaded and Processing are progress. Needs attention is an aggregate flag with a reason, not a compliance rating. Findings Open/In progress/Resolved and action Pending/In progress/Done use progress; preserve exact domain wording. Low risk never means compliant. Multiple labels may coexist.

## Type roles

Inter 400/500/600, local files. All audit content is at least 14px. Type does not shrink to fit a table. Numbers use tabular figures. Prose uses 56ch maximum, with a target of 60 to 80 characters per line. Inter’s digit 0 is wider than an average letter: the previous 72ch cap rendered up to 98 characters. Use 56ch in each role’s own font size, including 14px guidance and bold requirements; verify full lines remain at most 80 characters at both laptop widths. Short paragraphs do not need artificial padding to reach 60 characters.

| Role | Size/line height | Weight | Use |
| --- | --- | --- | --- |
| Page title | 24/32px | 600 | Task title, not repeated client name |
| Section title | 20/28px | 600 | Domain or finding section |
| Item title / control requirement | 16/24px | 600 | Gap title or question requirement |
| Body / gap / recommendation / report | 16/26px | 400 | Primary reading |
| Secondary body / guidance / criteria / quotes | 14/22px | 400 | Audit context; never muted below readable contrast |
| Table / badge / label / input | 14/20px | 400 | Decision-bearing fields |
| Identifier / timestamp / optional table meta | 12/18px | 400 | Only these may be below 14px |
| Score | 28/36px | 600 | Framework-specific summary; no decorative ring required |

Use real h1/h2/h3 order. Body weight remains 400, emphasis 600. Guidance has visible labels; hints do not resemble disabled content. Quote and criteria roles retain normal contrast. No all-caps headings.

## Spacing and density

Scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px. Default row 48px minimum; compact row 40px minimum; both grow for wrapping. Table cells 12px horizontal and 8px vertical. Surface padding 20px; section gap 24px; page gutters 24px. Buttons 36px minimum, small buttons 32px; client upload targets 44px. Radius: control 6px, surface 8px, overlay 10px, badge 999px. Shadows only overlays. Z-index: base 0, sticky 10, dropdown 20, dialog 40, toast 50. Motion 140ms colour/opacity, none under reduced motion.

## Width modes

Sidebar is 224px. Main gets viewport minus sidebar. Outer gutters are 24px per side. Inventory and task workspace share the same outer width, but different region allocation. These are target arithmetic values; prototype DOM geometry remains host verification.

| Mode | 1440 content px | 1280 content px | Allocation |
| --- | --- | --- | --- |
| Inventory | 1168 | 1008 | Full-width table; grow wrapped rows, no horizontal page scrolling |
| Task workspace | 1168 | 1008 | Questionnaire rail 196 + gap 20 + work 952/792; inner padding 20 each side leaves 910/750, including 1px borders |
| Review task | 1168 | 1008 | Queue 280 + gap 20 + detail 868/708 |
| Document | 880 | 880 | Centered document outer box; body <=56ch; surrounding margin carries no decision controls |

The board report uses the task workspace outer width for two columns of domain gaps; every text block retains the 56ch reading cap. Other document pages keep the 880px outer box.

At 1280, keep five conclusions columns and wrap gap text; no fixed-width cards. Right-side evidence is an on-demand Sheet, not a third permanent questionnaire column. For smaller staff viewports collapse sidebar to drawer below 1100px; below 900px stack list and detail. Only the client upload is a required 390px product screen. Do not promise the static staff prototypes as mobile deliverables.

## Navigation model

Global sidebar: Home, Clients, Engagements, Review, Evidence, Reports; Settings and working identity at bottom. Breadcrumb identifies client, engagement and assessment once. Assessment header names the task, shows framework focus, assessment period and evidence cut-off. Stage links: Overview, Scope, Evidence, Questionnaire, Review, Report. Exactly one horizontal stage bar.

Two alternatives replace levels two and three. **Choice pending Saqlain.** Option A keeps one labelled Section select in the content toolbar, shown on the original five screens and Scope. Review choices are Queue, Conclusions, Findings, Workpaper. Evidence choices flatten Inventory, Requests: Items, Requests: Versions, Requests: Client links, Desk review and Reuse. Scope choices are Boundaries and Applicability. Report sections are Summary, Domains, Versions, Comparison, Narrative and Board inputs; Board summary and Auditor detail use a separate two-option view toggle at the top right.

Option B exposes the active assessment under Engagements in the sidebar, with its stage sections as nested links. review-queue-sidebar.html demonstrates Review: Queue, Conclusions, Findings, Workpaper; Queue has aria-current. There is no Section select in this option. The horizontal stage bar stays. I recommend B for frequent assessment work because destinations remain visible and switching takes one click. A is more compact when the sidebar must hold many engagements.

Stage navigation and nested links use aria-current. The Option A select navigates routes or URL state and is not a fake tablist; native Select maps to shadcn Select. Neither option adds a horizontal navigation bar. Domain rail stays local item navigation. URLs encode section, framework and selected finding; history restores those and scroll position. Entering an assessment replaces engagement tabs.

## P1 to P10 rulings

| Rule | Ruling | New rule |
| --- | --- | --- |
| P1 | Keep | Sentence case; proper framework codes may retain prescribed case. |
| P2 | Change | Allow control codes beside meaningful titles. No decorative numbered navigation. |
| P3 | Change | Keep context that answers a real auditor question; label why and how explicitly. |
| P4 | Change | Size, weight, spacing and dividers carry hierarchy; semantic colour and icons supplement it. |
| P5 | Keep | One primary next action per state; decision alternatives remain secondary/destructive. |
| P6 | Change | Retire every gradient and glass surface, including primary button highlight. |
| P7 | Change | Four semantic families with theme-specific AA pairs; never tied to firm accent. |
| P8 | Keep | Never combine scores across frameworks. Show period/cut-off; conditional framework copy; no client numeric priority. |
| P9 | Keep | Tokens own colours, type, spacing, radius and layers; no arbitrary screen-level values. |
| P10 | Keep | Every status has words; icons reinforce. Colour alone never conveys a decision. |

Evidence: UI-001/002/003/008/009/012/013/025 and measured small audit text, narrow questionnaire and stacked navigation. Canvas and glass are retired by decision; no aesthetic preference is presented as runtime evidence.

## Greyscale acceptance

Remove colour in the host screenshot pass. Identify task title, gap statement and attached next action without reading metadata. Queue outcomes and risk remain written. Selected item has border and aria-current, approved records say Approved, provenance has a labelled region. Scan 50 controls by domain, code, gap and status; read a 400-word conclusion at the body role. These are acceptance tasks for users and host review, not claims of usability proven by this docs run.
