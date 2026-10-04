# Deliverables quality scope (V3-C): make the shipped deck match the approved mockup

**Written:** 4 Oct 2026. **Status:** scoping, awaiting Saqlain's go. **Owner:** Claude designs and reviews; Codex builds; Saqlain approves by looking at renders.

## Where P6-8 and P6-9 actually are
Merged: P6-9 SoA, roadmap, prior-period (#86), P6-8 B1 PDF (#80), B2 (#92), P6-10 narrative (#95), V3-A data capture (#94), V3-B deck, PPTX and XLSX (#101). `CLAUDE.md` still says "Next: P6-8 B2 and P6-10"; that line is stale. There is no unbuilt P6-8 or P6-9 feature left. What is left is quality.

## The bar (Saqlain, 4 Oct)
Awe-inspiring. A non-technical, non-cyber reader understands the story from the page alone. A technical reader still finds every detail they expect. These two do not trade off: the first layer is visual and plain-language, the second layer is dense tables and registers behind it.

## What I checked
Rendered the shipped v3 deck from the golden fixture (`tests/golden/p6_8_v3_deck_document.json`, 25 slides) and compared it with the approved `docs/product/2026-10-01-board-report-mockup/board-deck-PROPOSED.pdf`. V3-B's own Results say no one looked at the PDF in a browser or viewer; the tests check structure only.

**Verdict: the structure is right and the finish is not.** Slide order, tables and derived numbers are good. The shipped deck drops most of what made the mockup look finished.

| Area | Mockup | Shipped | Fix |
|---|---|---|---|
| Cover | Artwork panel, draft badge, framework chips, period/cut-off/version/snapshot row | Flat navy slab, small text, footer garbled to `????` on the Devanagari cover path | Rebuild cover to mockup; fix the fpdf2 cover path footer |
| Contents | Clean list with page numbers | Title block overlaps the number column ("04", "05" clipped) | Layout bug |
| Overview | Scope cards with badges, approach steps, 5 coloured KPI tiles | 3 navy tiles, no approach, no period tiles | Restore |
| "How to read the ratings" | Dedicated slide (outcomes, risk levels, 3 dimensions, horizons) | Missing | Add: this is the main aid for a non-technical reader |
| Executive summary | Donut, 5 coloured outcome tiles, stacked bars, top-three-risks cards | Two bars and a text line; the boilerplate "Narrative paragraphs are drafted from..." repeats on several slides | Restore donut, tiles, risk cards; show the boilerplate once, in the methodology |
| Domain status | Per-domain bars with percentages and pills | Text rows with tiny pills, no bars | Restore bars |
| Risk profile | Donut per severity, domain bars, overall donut | Four text boxes and tiny bullets | Restore |
| Board asks | Large numbered decision cards plus attention counters | Small cards, half the slide empty | Restore |
| Roadmap | Horizon columns | Present and decent | Polish type size |
| Prior period | Scores with deltas | Plain text with a literal "None" | Rebuild with delta arrows; no "None" |
| Sign-off, limits | Designed blocks | Two large empty boxes; a wall of 8pt text | Resize, split limits into two readable columns |
| General | Section badge shows section number, content fills the slide | Badge shows slide number; 30 to 40 percent of most slides empty; table type about 7pt | Fix badge, scale content, enforce a minimum type size |

## Plan

1. **V3-C1 (Claude, now): write the visual contract.** Per slide: layout, the data it reads, minimum font sizes (body 11pt or more on a 13.33in slide, table 9pt or more), fill rule (content covers at least 80 percent of the body area), plain-language headline sentence per slide computed from the document. No new data fields; everything comes from the existing v3 sidecar. Add render tests: page count, no overlap of text boxes, no empty bottom third, contrast.
2. **V3-C2 (Codex, one worktree, `app/templates/` board template and CSS only).** Rebuild the template to the contract: cover, contents, overview, ratings legend, executive summary, domain status, risk profile, board asks, prior period, sign-off, limits. Charts are inline SVG (donuts, bars), so they render identically in WeasyPrint and need no new dependency.
3. **V3-C3 (Codex or Claude): PPTX and XLSX parity.** PPTX mirrors the new slides with native charts; XLSX gets the same executive summary sheet look, frozen header rows, conditional fills for severity, a legend sheet. Open both in LibreOffice or Numbers and look.
4. **Gate: Saqlain looks at pages, not tests.** Same pixel-gate habit as Yozora: I render the golden document plus a second, thinner document (few findings, one framework, no prior period) so the deck is checked for sparse as well as dense data, and send page images. Two-pass design rule applies: one design pass now, one before exposure.
5. **Plain-language layer.** Two sentences per slide for a non-technical reader come from the deterministic derivations in `board_derive.py` where possible; the P6-10 narrative stays the only LLM-written text and stays consultant-approved. Technical depth stays in the observations table, requirement register, SoA and XLSX.

## Guards
Snapshots stay write-once; v1 and v2 sidecars are not re-rendered; no numeric priority in client output; framework copy conditional; `S()` for every fpdf2 string (the Devanagari cover path); additive changes to existing fpdf2 PDF sections. File-set guards need per-PR allowances as before. No attribution lines in any commit or PR body.

## Sequencing with Yozora
V3-C touches the board template, CSS and board exports only, so it runs in parallel with S3 to S6 without file collisions. S7 (report tab) later links to it and reads it; no overlap.

## Questions
1. Approve V3-C as the next deliverables job, ahead of Track 4?
2. The mockup sets the target. Anything in it you want changed before Codex builds (colours, the cover art, the "Draft until issued" badge, slide count)?
3. Do you want one more reference, such as another consultancy deck you admire, to feed the contract?

## Decision (4 Oct): V3-C is the next deliverables job; the mockup may change, driven by research

### Research findings (web, 4 Oct)
Sources: NACD cyber board-reporting toolkit, Decryption Digest CISO board template, McKinsey chart technique write-up (Analyst Academy), Resilience on the heat-map critique, Datawrapper, Observable and Peltier Tech on radar charts, dumbbell vs slope chart guides, waffle chart guides, impact-effort matrix guides, 2026 annual report design trends.

1. **Action titles.** Every slide title states the takeaway ("Consent and breach notification are the weakest areas"), not the topic. Bold the numbers that carry the title; keep everything else neutral grey and colour only what matters (McKinsey).
2. **Fixed, plain structure for boards.** Risk posture on one page readable in 30 seconds; top 3 risks as cards; the decision as a risk decision, not a purchase; a trend arrow beside every metric; define every acronym; deck works as a pre-read (Decryption Digest, NACD).
3. **Heat maps and likelihood matrices do not fit us.** They need subjective likelihood estimates; our engine is deterministic and never invents likelihood. Keep severity counts and the impact-effort view instead. This is a strength to say out loud in the methodology.
4. **No radar charts.** No shared baseline, order-dependent shape, implies continuity between unrelated domains. Use sorted horizontal bars with the rating thresholds drawn behind them (a bullet chart).
5. **Part-to-whole for non-technical readers: waffle (10 by 10) or one stacked bar, not donuts.** Squares are countable ("43 of 120 requirements"), people estimate them more accurately than pie or donut slices. Our 120 requirements map to a 120-cell grid.
6. **Before and after: dumbbell chart per domain** (gap size is the story) for prior-period comparison; a slope chart only for the two-framework headline.
7. **Initiatives: a 3 by 3 effort-versus-benefit matrix** (we already capture complexity and benefit per initiative) with Quick wins and Big bets labelled, plus the Short, Medium, Long horizon roadmap as swimlanes by responsibility (client, consultant, shared).
8. **Selective, colour-blind-safe colour.** Status colours reserved for status, always with an icon or label; one accent for emphasis; validate the palette with the dataviz validator for light and print.

### Proposed changes to the mockup
| Mockup element | Change |
|---|---|
| Donut on executive summary and risk profile | Replace with 10 by 10 waffle plus counts, or a single stacked bar |
| Per-framework stacked bars | Keep, add the rating threshold bands and a trend arrow |
| Domain status rows | Sorted bullet bars with thresholds, weakest first |
| Risk profile four boxes | Severity tiles with count, the three biggest domains named, no donut |
| Prior-period slide | Dumbbell per domain with delta labels |
| Roadmap kanban cards | Swimlane by responsibility, keeping horizon columns |
| Initiatives table dots | Add the effort-benefit matrix beside the table |
| Titles | Action titles generated deterministically from the document |
| New | "How to read this report" slide (outcomes, severities, the three rating dimensions) up front; a one-page executive pre-read; source footnote on every chart |
| Radar, heat map | Not used, by design |

### Limits of this research
Web search returns text, not images. I found no public consultancy sample worth copying pixel for pixel, and Vanta, Drata and Secureframe dashboards sit behind sign-ups. To see actual designs I need either a browser pass over chosen galleries (Behance report layouts, Information is Beautiful, ARC Awards infographics, Datawrapper chart gallery) or you point me at examples you like.

### Next
Re-render the mockup deck to these changes (one design pass), you approve the pages, then the V3-C1 contract is written from the approved pages and Codex builds.

## Design pass rendered (4 Oct)
`docs/product/2026-10-04-board-deck-v3c-mockup/`: `render_deck.py` (presenter prototype, action titles computed from the document), `deck_template.html`, `deck.pdf` (golden mockup document, 30 pages) and `deck-sparse.pdf` (one framework, three findings, no prior period, 24 pages); page PNGs under `pages/`. Status palette re-stepped and validated (outcomes worst CVD dE 12.1; compliant moved to teal `#0E8F86`). Awaiting Saqlain's page review.
- **New data field needed:** per-domain prior scores for the dumbbell (read from the prior snapshot's stored document); mocked and tagged on the slide.
- **Approved 4 Oct.** Saqlain approved the pages, including the dumbbell. The sparse-deck spacing is fixed by a vertical-rhythm rule: `lay` in `view()` scales row heights to the body height, the body is a space-between column, the roadmap lanes fill the body, a single board ask becomes one tall card, and a first report shows a baseline chart.
- **Backend for the dumbbell:** handed off in `tasks/handoffs/2026-10-04-v3c-prior-domain-scores.md`, running in parallel.
- **Next:** write the V3-C1 visual contract from these pages, then the Codex build (V3-C2).
