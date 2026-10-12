# Status inventory and semantic collisions

Source audit, 12 October 2026. These are declared application states and rendering rules, not claims that every state appeared in a capture. Browser confirmation remains pending where the app was unreachable. Model columns generally store strings; the services below define allowed transitions and display labels. No analysis or generation was run.

## Shared tone contract

`app/templates/components/ui.html:25` maps pill tone names to `c-*` classes. `app/static/css/yozora-components.css:73` to `:85` sets their presentation. Pills use 12px primary text, a 6px coloured dot and a translucent tinted background. `status()` uses 13px secondary text plus a dot, a hollow circle, or a half-filled progress circle. Colour therefore supplements wording for pills; queue outcome dots depend on hover titles.

| Tone | Colour token | Light and dark value | Existing semantic uses |
|---|---|---|---|
| critical | critical | #9B1C1C | Critical risk/severity |
| high | high | #D9481E | High risk/severity |
| medium | medium | #F0A030 | Medium risk, outdated evidence, warning, conflict, lock |
| low | low | #3C9D6B | Low risk/severity |
| ok | compliant | #2F9466 | Compliant, available evidence, accepted narrative, complete upload link |
| part | partial | #F0A030 | Partially compliant, partially implemented |
| non | noncompliant | #C0392B | Non-compliant, rejected evidence |
| insuf | insufficient | #9AA3B5 | Insufficient evidence, not drafted, not determined |
| neutral | insufficient | #9AA3B5 | Framework metadata, not applicable, expired/revoked links, superseded versions |
| accent | accent-text | Preset-dependent | Required, scanning, active link, issued RFI, AI origin, navigation, informational alert |

All severity/outcome tokens inherit the same values in dark mode. Pill text remains `--text`, so a coloured dot that fails a non-text contrast check does not imply the label text fails. Conversely a readable label does not make the dot distinguishable. See `contrast-data.json` for both candidate foregrounds and surface bounds.

## State and wording ledger

| Entity / stored state | Display wording | Tone or marker | Appears / source |
|---|---|---|---|
| Evidence quarantined | Scanning | Accent pill; progress circle in inventory/detail | `services/evidence_inventory.py:43`, `components/ui.html:31`, `partials/document_list.html:35`, `pages/evidence_detail.html:5` |
| Evidence active | Available | ok in inventory/detail; accent in workpaper | Same sources; `components/workpaper_entry.html:65` |
| Evidence rejected | Rejected | non | Same inventory and evidence macro |
| Evidence invalidated | Out of date | medium | Same inventory and evidence macro |
| Evidence archived | Not shown in ordinary list | No evidence pill | `services/evidence.py:26`, `services/evidence_inventory.py:49`, `components/ui.html:32` |
| Evidence version superseded | Superseded; Superseded version | neutral pill; warning with icon on citation | `services/evidence.py:27`, `components/ui.html:34`, `components/conclusion_card.html:82` |
| Legacy evidence | Legacy (not migrated) | neutral | `components/ui.html:36`, `partials/document_list.html:69` |
| Outcome compliant | Compliant | ok | `services/conclusion_review.py:22`, `components/conclusion_card.html:2` |
| Outcome partially_compliant | Partially compliant | part | Same sources |
| Outcome non_compliant | Non-compliant | non | Same sources |
| Outcome insufficient_evidence | Insufficient evidence | insuf | Same sources |
| Outcome not_applicable | Not applicable | neutral | Same sources |
| Risk critical / high / medium / low | Critical / High / Medium / Low | Matching risk tone | `services/conclusion_review.py:34`, `components/conclusion_card.html:4`, `pages/findings.html:8` |
| Conclusion pending | Pending | Hollow circle, secondary text | `services/conclusion_review.py:47`, `components/conclusion_card.html:17` |
| Conclusion approved | Approved | Check icon, secondary text | Same sources |
| Conclusion edited | Edited and approved | Pen icon, secondary text | Same sources; also `services/report_content.py:26` |
| Conclusion rejected | Rejected | X icon, secondary text | Same sources |
| Revision reopened | Reopened in decision history; current card returns to Pending | Decision-history text | `services/analysis_pipeline.py:62`, `services/conclusion_review.py:122`, `components/conclusion_card.html:5` |
| AI proposed / consultant edited | AI proposed / Edited by consultant | Same `.ai` outlined badge and accent diamond | `components/conclusion_card.html:28`, `yozora-components.css:223` |
| Conclusion locked | Locked | medium warning, lock icon | `components/conclusion_card.html:31`, withheld-proposal alert below |
| Conflict | This conclusion changed since you loaded it | medium alert | `components/conclusion_card.html:35` |
| Finding open | Open | Hollow status circle | `services/findings.py:29`, `pages/findings.html:93` |
| Finding in_progress | In progress | Half-filled progress circle | Same sources |
| Finding resolved | Service: Resolved; findings table: Verified; date column: Done | Check icon | `services/findings.py:49`, `pages/findings.html:93` |
| Finding accepted_risk | Accepted risk | Hollow status circle | Same service labels; table calls `status` without tone |
| Action open / in_progress | Open / In progress | Hollow / progress circle where `status` macro is used | `services/findings.py:42`, `pages/remediation_tracker.html`, `partials/remediation_panel.html` |
| Action closed | Closed, awaiting verification | Plain workflow status text; closure evidence is separate | `services/findings.py:45`, `services/report_content.py:30` |
| Action verified | Closed and verified | Workflow status text | Same sources; service requires a separate verification transition |
| Action priority 1 / 2 / 3 / 4 | Do first / Next / Planned / Backlog | Priority words, independent of status | `services/findings.py:58` |
| Upload request item | Received-count summary / Not received; rejected uploads shown separately | Checked / empty request marker; Rejected non pill | `partials/magic_links.html:49`, `components/ui.html:221` |
| Magic link active | Active; Complete if all requested items received | accent / ok | `routers/magic.py:215` to `:232`, `partials/magic_links.html:42` |
| Magic link expired / revoked | Expired / Revoked | neutral | Same sources; `services/magic_links.py:380` derives expiry/revocation |
| RFI client link active / expired / revoked | Active / Expired / Revoked | accent / neutral | `partials/rfi_links.html:94`; completion wording differs from legacy link panel |
| RFI required / optional | Required / Recommended | accent / neutral | `pages/rfi.html:70`, `services/rfi_requests.py:36` |
| Evidence request requested | Added to the draft RFI. Generate a new RFI version to send it. | Explanatory text | `services/rfi_evidence_requests.py:31`, `components/requirement_card_body.html` |
| Evidence request issued | Sent in RFI vN as RFI-NNN. | Explanatory text | `services/rfi_evidence_requests.py:32` |
| Snapshot draft / superseded | Draft / Draft (superseded) | neutral | `pages/report_snapshots.html:11`, `pages/rfi.html:168` |
| Snapshot issued | Issued / Issued (current) | neutral / accent in snapshots; both accent on RFI | Same two templates |
| Report release false | Not approved for release / Report not yet approved for release | Blocking explanatory copy | `services/report_content.py:39`, `services/approved_report.py:64` |
| Report released | Released + date | Completion text / done-state | `services/assessment_stage.py:157`, `pages/report_snapshots.html` |
| Framework score state scored / not_scored / pending_review / unavailable / failed | Score / Not scored / pending review / unavailable / failure explanation | Score text or warning; no single status tone registry | `services/approved_report.py:33`, `partials/report_summary.html`, `services/scoring.py` |
| Narrative accepted | Accepted; additional warning if stale | ok + warning | `pages/narrative.html:99` |
| Narrative draft / none | Draft, not accepted / Not drafted | accent / insuf | Same template; `services/narrative.py` |
| SoA applicability applicable / excluded / not_assessed / pending | Applicable / Excluded / Not determined / Awaiting decision | accent for applicable; neutral otherwise | `services/soa.py:23`, `pages/soa.html:11` |
| SoA implementation outcomes | Implemented / Partially implemented / Not implemented / Not determined: insufficient evidence / Not applicable | Outcome tone | `services/soa.py:29`, `pages/soa.html:7` |
| Questionnaire active / skipped / pre_filled / deepened | Question content / excluded or skipped question / pre-filled answer / attention | Source hint or `.warn`; deep tier: Deep review | `partials/section_questions.html:38` to `:92`, `services/question_engine.py` |
| Answer inferred / document pre-fill | Source-specific pre-fill wording, confidence text | AI pre-fill controls and provenance hint | Same section template; confirmed answer count in `services/assessment_stage.py:94` |
| Desk review pending / analyzing / completed / error | Pre-fill pending / running / completion / failure | Progress or warning state | `models/desk_review.py:23`, `models/assessment.py:37`, `pages/desk_review.html`, `partials/desk_review_running.html`, `partials/desk_review_error.html` |
| Analysis running / completed / failed | Analysis running / completion / failure | Progress / error copy | `services/analysis_pipeline.py:53`, `services/assessment_stage.py:132` |
| Assessment persisted stages | New / Scoping / Documents Uploaded / Context Gathered / Questionnaire Done / Analyzing… / Completed / Error | Neutral portfolio pill | `services/portfolio.py:23`, `partials/engagement_list.html:10` |
| Assessment derived stage | Scope / Evidence / Questionnaire / Review / Report plus counts and next step | Stage navigation and explanatory text | `services/assessment_stage.py:48`; semantic stage differs from stored status |
| Engagement active / archived | Active / Archived; read-only banner for archived | Neutral metadata / medium lock warning | `models/engagement.py:19`, `pages/evidence_inventory.html:45`, `pages/firm_settings.html` |
| AWS source not_enabled / collected | Not enabled / Collected; Truncated separate qualifier | neutral / accent | `partials/aws_evidence_panel.html:26` |
| AWS vendor compliance | PASSED / FAILED / WARNING / NOT_AVAILABLE / NONE | Source data, not CyberAssess outcome | `services/aws_evidence.py:413`; source evidence details |
| Toast success / error / information | Operation-specific message | Check / alert icon; error live alert, others status | `components/ui.html:143`, `app/static/js/app.js` |
| UI empty / loading / error / blocked | Context-specific explanatory copy and next step | Empty container / skeleton / alert | `components/ui.html:85`, `:131`; design fixtures |

## Confirmed source collisions and their workflow impact

1. `medium` and `part` resolve to the exact same colour. A medium-severity risk and a partially implemented control cannot be distinguished by hue. Retain explicit type labels and distinguish severity from outcome by placement and shape.
2. `neutral` and `insuf` are the exact same colour. Insufficient evidence competes with harmless framework metadata, excluded controls and inactive links. Evidence insufficiency needs a visible missing-support label and next action, independent of neutral metadata.
3. `low` and `ok` use similar green values but describe risk severity and positive workflow outcomes. Avoid relying on a green dot to imply that low-risk non-compliance is compliant.
4. The accent tone represents Required, Scanning, Active, Issued, AI proposed, informational alerts and navigation. These are independent semantic axes. Required is an obligation, not a lifecycle state; AI proposed is origin, not approval. Keep origin, outcome, decision and requirement as separate fields with readable labels.
5. Available evidence is green in inventory and detail but accent-coloured in workpaper. Use one evidence availability presentation across contexts. This is a template shortcut, not a limitation of HTMX.
6. AI proposed and Edited by consultant share the `.ai` badge with the same accent diamond. Human approval is a secondary 13px icon label above it. The human decision must receive stronger structural placement, while origin remains supporting metadata.
7. A resolved finding is labelled Resolved in the service, Verified in its table and Done in the date cell. Reserve Verified for verified closure and use a stable finding lifecycle label, plus a separate closure verification fact where needed.
8. RFI snapshots style Issued as accent on the RFI page but neutral on the versions page unless current. Separate current-version selection from issued lifecycle. Old issued reports are still issued.
9. Legacy client links show Complete while versioned RFI links still show Active. Completion, expiry and access validity should be displayed as independent facts. A complete but expired request is possible.
10. Assessment Completed is derived from analysis-stage progression and is separate from consultant approval, release and board snapshot creation. Do not imply Completed means released. The newer stage service provides stronger task-specific notes; migrate that explicit workflow model.
11. Queue outcome indicators are 8px dots with hover `title` text while decision state is reflected in `.decided` styling (`pages/review_queue.html:47`). Keyboard users need visible outcome/decision labels or equivalent accessible descriptions without hover.
12. Backend fields are largely free-form strings and each template carries mappings. Porting these dictionaries independently would preserve drift. Use a shared typed display registry per semantic axis with labels, icons, tones and allowed transitions derived from service contracts.

## Recommended semantic direction for review

Keep a restrained set of visual tones: neutral context, active/information, positive confirmed state, attention and blocking failure. Keep severity ordinal and explicitly labelled, with a distinct field from outcome. Display evidence availability, compliance outcome, human decision, release lifecycle and provenance as separate facts rather than interchangeable pills. This is a recommendation for the Phase 12 stop point, not a final component or design specification.

Prioritise truthful labels and transition semantics before palette polish. Validate status text and non-text indicators in both themes and all eight presets. A screenshot alone cannot prove backend lifecycle integrity; the sources above establish the meanings and transitions.
