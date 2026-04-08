# DPDPA Assessment — Interview Protocol

> For internal use by the CyberAssess facilitator. Do not share with the client.

---

## 1. Pre-Interview Setup

**Complete before the call:**
- [ ] Complete the pre-research checklist (`docs/pre-research-checklist.md`)
- [ ] Load the facilitator's guide (`docs/facilitator-guide.md`) — printed or on second screen
- [ ] Open the CyberAssess backend (`uvicorn app.main:app --reload`)
- [ ] Have a blank doc open for session notes and verbatim quotes
- [ ] Confirm the recording/note-taking arrangement with the client (recommended: inform them it is for internal assessment use only)

---

## 2. Recommended Attendees — Client Side

Ask the client to bring the following people. One person can cover multiple roles.

| Role | Why They're Needed |
|------|--------------------|
| **DPO / Privacy Lead** (primary) | Owns the compliance posture; can answer policy and process questions |
| **IT / Security Head** | Can speak to technical controls (encryption, access, breach response) |
| **Legal Counsel** | Can confirm contractual positions (processor agreements, cross-border) |
| **Operations / Product Lead** | Can speak to consent flows, product data handling, user-facing features |

> **If the DPO is unavailable:** Acceptable to proceed with IT/Security + Legal if they have visibility into privacy policy and consent implementation. Document the gap.

---

## 3. Session Framing Script (Opening — 5 minutes)

Use these words (or close to them) to open the session:

> _"Thanks for joining. The purpose of today's session is to conduct a structured DPDPA gap assessment — think of it as a collaborative mapping exercise, not an audit. I am going to ask you a set of questions across six compliance domains. Your job is to tell me what is actually in place today, not what you plan to have._
>
> _There are no wrong answers. If the honest answer is 'we don't have that yet,' that's exactly what I need to know — a gap identified now is a gap we can fix before a regulator finds it. I will be taking notes throughout._
>
> _The output will be a PDF gap report with a compliance score, prioritized gap list, and a remediation roadmap with effort estimates. I will deliver it within 48 hours. Any questions before we start?"_

---

## 4. Handling "I Don't Know"

When a client says they don't know the answer:

1. **Note it as a gap** — mark as "Not Implemented" unless they can get an answer within 24 hours
2. **Ask who would know** — "Is there someone else on your team who would know this? Can we get them on a quick call or have you check and send me a note?"
3. **Flag for follow-up** — add to the session notes as "Action: [client name] to confirm [item] by [date]"
4. **Do not fill in the answer for them** — never suggest an answer or let the client upgrade their response based on intent

> **Rule:** Intent is not compliance. "We plan to" or "we are going to" = Planned, not Implemented.

---

## 5. Probing for Evidence vs. Intent

The highest-value thing you can do is distinguish between **what they say they do** and **what they can show you**. For every "Yes, we have that" answer:

**Ask for evidence:**
- "Can you show me that?" (screen share, document share)
- "Where would I find that documented?"
- "What does that look like in practice?"
- "When was this last reviewed or tested?"

**Evidence tiers (note in the session):**
| Tier | Example | Weight |
|------|---------|--------|
| **Tier 1 — Verifiable** | Showed me the consent screen / shared the policy doc / pulled up the audit log | Strongest |
| **Tier 2 — Referenced** | "It's in our SOPs, I can send it after the call" | Moderate — flag for document review |
| **Tier 3 — Asserted** | "Yes, we do that" with no document or system to point to | Weakest — note as asserted intent |

When evidence is Tier 3, note in the report as "based on disclosed information; not independently verified."

---

## 6. Managing Scope Creep

Clients will often want to elaborate or go off-topic. Keep the session moving:

- "That's useful context — let me note that. For the purposes of this question, can I mark you as [answer]?"
- "We will capture that in the evidence log — let us come back to it if we have time at the end"
- Target: **75 minutes total** for the full session (20 min context, 50 min compliance, 5 min close)

---

## 7. Sensitive Areas — How to Handle

**Data breaches:** Clients may be reluctant to disclose unreported incidents.
> _"For the breach notification questions, I am asking about your process and preparedness, not asking you to disclose specific incidents. If you have had an incident in the past, I just need to know whether your process was followed."_

**Children's data:** Some clients do not realise they collect children's data (e.g., family apps, school tools).
> _"Do any users of your platform identify as parents or guardians? Do you have any features used by or designed for children?"_

**SDF designation:** Clients may be uncertain.
> _"You don't need to have been officially designated — I'm asking whether, based on data volumes and sensitivity, you think you could be subject to SDF obligations."_

---

## 8. Closing the Session (5 minutes)

Use these steps to close:

1. **Summarize open items:** "I have [N] follow-up items — can you send those to me by [date]?"
2. **Confirm report recipient:** Name and email for PDF delivery
3. **Set delivery timeline:** "You will receive the report within 48 hours — by [specific date]"
4. **Set follow-up call:** "Once you have reviewed the report, I would like to schedule a 30-minute call to walk through the findings and talk about remediation priorities. Can we pencil in a time now?"
5. **Frame next steps:** _"The report will prioritize gaps by risk level. The highest-priority items are the ones a regulator or enterprise client would be most likely to ask about first. We can talk through how to address those efficiently."_

---

## 9. Post-Session Checklist

- [ ] Compile all session notes into the CyberAssess questionnaire response format
- [ ] Request and review any documents the client offered to send
- [ ] Run the assessment through the CyberAssess backend
- [ ] Review AI-generated gap descriptions — verify they reference company-specific context
- [ ] Review PDF output before sending — check for generic boilerplate
- [ ] Deliver the PDF report within 48 hours of the session
- [ ] Book the remediation follow-up call
