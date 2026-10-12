# Saqlain's feedback on the UI audit (12 Oct 2026)

Source: the annotated review page https://claude.ai/artifact/KtVkvypbF5FsmB6g9thZyh. Part 1 is Claude's summary of decisions and requirements. Part 2 is Saqlain's notes exactly as written; where the two differ, Part 2 wins.

# Part 1. Summary

## Decisions Saqlain made (do not relitigate)

| Topic | Decision |
|---|---|
| Canvas and glass | Retire both. Opaque surfaces on a neutral background. |
| Accents | Keep the 8, for interaction and branding only. |
| Status colours | Rebuild as four families: severity, outcome, progress, provenance. |
| Control codes | Allowed beside titles in lists. |
| Questionnaire navigation | Single framework: that framework's own domains. Multi-framework: domains from the unified control framework, each requirement covered once. One master set of domains per framework. |
| Draft saving | Automatic, as you type. |
| Review queue order | Pending decisions first, then missing or contradictory evidence; sortable and switchable at any time. |
| Target width | Laptop, about 1440. |
| Navigation | Never two navigation bars stacked under each other. Sub-sections inside a tab need a different pattern. |

## Requirements from Saqlain's notes (inputs to the spec)

- **Questionnaire.** The question area must use the width; no narrow column with a blank side. Per question, in this order of weight: what the control requires, why it is asked, a hint on how to put it to the client. Rework help text and the text hierarchy. The answered state after assessment also needs redesign.
- **Review queue.** Each item is a finding. Title it with the gap itself ("Access reviews do not cover all systems"), not the control name. Show: gap statement, compliance status, risk or impact of the non-compliance, recommendation at full weight with its reasoning, and where the finding came from (what was reviewed, who was spoken to) as a short narrative, not an evidence extract. Remove the duplicate "Evidence" and "Evidence on this control" blocks. Settle one data hierarchy for every screen under Review.
- **Conclusions.** Same content as the queue with review mechanics removed: the final gap, in a table with domain, control ID, risk and status, like a standard assessment sheet. Deterministic layout.
- **RFI.** Much simpler: a tight list with good sorting. An item already added to an RFI is not shown again in the same form.
- **Report.** Opens with an executive summary that sets the context (what the engagement was, what was reviewed, domains in scope), the gaps, where they lie, their criticality and overall posture, well written. Then gaps by domain (weakest and strongest), each with the non-compliance, impact if unresolved and risk, readable by a board. A summary view for the board and a detailed view for auditors and technical teams. Recommendations with their logic, following the flow of the exported report.
- **SoA.** Ask only which controls are not applicable and why; everything else is applicable with a standard justification. It does not need its own tab.
- **Content quality (separate track, flagged by Saqlain).** The content itself is not shaped for its reader: report writing, control wording, unified-framework structure, how AI output reads to a consultant. Each deliverable must suit its audience: workpapers for the auditor, reports for boards and executives. This is beyond layout and needs its own plan; the spec must leave room for it and not treat it as solved by redesign.
- **Pitch to hold to.** The tool is useful to consultants: less effort, and still good reports from what the AI can read.

## Scope note for the migration plan

Several of these change what screens show and how data is shaped (findings titled by gap, provenance narrative, master domains, SoA folded away, report restructured). They are more than a restyle. Section 12's "screen PRs change presentation only" no longer holds for Review, Report, RFI, SoA and Questionnaire; the fresh session revises sections 6 and 7 to separate presentation ports from these product changes and flags which need backend or content work.

# Part 2. Notes as written

## Questionnaire, top of page

So I'm hoping that when you say all of these things, or the point is that you noted down, you also, so I guess one of the bigger problems, like main problems, is that the questions themselves are in this narrow space, and when you scroll down, it just looks awkward that the questions are in this narrow space, and towards the left-hand side, there is so much empty space available, and that's one.

The second thing about that, the section list uses privacy headings, that's just wrong. All frameworks need to have a set of domains, a mix of framework would also have a set of domains. So essentially we just need to make a master framework with set domains so that shouldn't be a problem to change.

The overview scope evidence questionnaire review report, in most tabs there is a second navigation bar right below that. That's unacceptable. We cannot have two navigations right below each other, especially navigation that changes. We need to show a different way to have tabs represented in a given section.

## Questionnaire, after scrolling

So this is the page, this is the review screen or the questionnaire screen that the consultant is going to see. So for a consultant, the most important part is what exactly does the control or the framework requires, like a particular question, context about why that question is being asked, and some hint, which is just basically a hint and direction on how to lead that question so that the consultant can place it better for the person who is answering and explain it better to the person who is answering.

So we need to make the help text a little better, and just the overall text hierarchy of things. And after the assessment is performed, how things are being shown is also pretty bad.

## Review queue

we need to have a clear prioritization on what infromation should be shown with each of these cards and in what format. rather than having just the domain name  as the title it would make more sense we we can highlight the actual gap or non compliance in the process. Lack of coverage in access review something along these lines so the auditor know immediately what the action item is going to be about. it would have the conclusion ( gap statement). compliance status, if possible risk associated with a non-compliance of the like ( crticality or impact it could have on the org) Reccomendation ( should not really be in a smaller box as this is part of our primary deliverable. reasoning behind a given reccomendation should also be available. I'm not sure why we have evidence and then evidence on this control, both, right? The evidence tab is giving me a link of a file which is the same as the one in evidence on control. The first one is giving me more information, the second one is just saying cited. I don't think we need to have this. I think all we need to do is for a given So for a given finding that we have, right, so before these are approved gaps or non-compliances, these are going to be findings. So for all of these findings that we have we will need to show where does this finding come from- what did we review, who did we speak to in order to find the gap. this should also be a concise narrative rather than just a extract of the evidence. data hirerchy for this needs to be finalied for all screens in the review tab i feel are complicating it too muhc.

## RFI items

we are complicating the page too much, this can be made much much simpler. once a piece of evidence is added to an RFI the auditor should not be shown the same piece of evidence again in the same type of format. this ca be a tight vercel like list with good sorting maybe.

## One conclusion, expanded

In the conclusion, we need to again have a clear hierarchy on what exactly we're trying to convey. So as part of a conclusion, we're trying to say that a particular, like, a given, we're highlighting gaps, right? We're saying what the gaps are in this organization, and we're trying to settle on a compliance level or risk level for a particular non-compliance that they have.

So we show the status. We again need to mention where the gap, like, I think we covered this as part of the earlier tab, the Q tab. It should be the same things, but this time all the review-related details should be taken out, and a final version of the gap should be highlighted, what domain it belongs to. The table format should have the domain, the control ID that relates with the risk vulnerability, like, these are things that any general assessment sheet would have.

So I think we should be able to cover these in a very deterministic way.

## Report

In the report, it is very important that we start by setting the context on what this engagement was about, what was reviewed, what were the domains under scope. This should be the executive summary. It should be the first thing that opens up when you see the report. It summarizes the entire thing, tells you what the gaps are, where they lie, what kind of criticality, and just gives you an idea about the overall posture of the film. This should be a very well-written piece of text.

Below this, we then need to highlight what were the gaps required, what was in a real organization we will have gaps in almost every domain. So we should show what are the gaps by domains, where their organization is the weakest or where they are the strongest. It should tell them for all of these gaps what was the non-compliance that was identified? What would be the impact in case this is not resolved? What is the risk that is associated with it? And all of this has to be communicated in a way that the board itself understands, and they should have a quick summary view and a detailed view for auditors and the technical teams.

What they need to fix is going to be recommendations, or we can have a different heat map for how things need to be implemented. What is the logic behind the recommendation? I think all of that is already part of the final report that we export. But the same kind of flow has to be applied here as well, where we prioritize the right type of information to be shown for the given report.

## Statement of applicability

See the SOA can simply be all we need to do for the SOA is just ask them which of these controls are not applicable to your organization. If they say that okay, cloud is not applicable because we don't use any cloud related services, or they say oh we don't outsource any development, then only that piece becomes not applicable. Everything else is applicable, so the justification can be something standard, so it's easier. Like, we don't need all this for the applicability or the SOA side of things, and I don't think SOA has to be its own whole tab as well.

## Root causes

one more thing would be the content itself is not optimized for what its supposed to be/do. There is clear guidance on what is the best practice when it comes to writing a report, how to write a control, how to make a unified control framework. how  represent the data we have to give the user most benefit not just throw in a bunch of garbage and hope it looks busy and some of it lands. the content is not thoughtful which is something we will have to work on seperately i assume.

## Decision: gradient and glass

**Chosen:** Retire both (recommended)

## Decision: accent colours

**Chosen:** Keep for interaction and branding (recommended)

## Decision: status colours

**Chosen:** Rebuild as four families (recommended)

## Decision: control codes in lists

**Chosen:** Allow beside titles (recommended)

## Decision: questionnaire navigation

**Chosen:** Framework's own structure

frameworks own strucure for individual assessments. for a multi framework assessment we should have domains that come out of our unified control framework where each requirement from all of the standards underscope are covered only once.

## Decision: draft saving

**Chosen:** Save automatically as I type

## Decision: review queue order

**Chosen:** Pending decisions

pending decisions untill there are non left and then missing contradicting evidence ( would be better if i get the opeiton to sort and switch anytime)

## Decision: target screen width

**Chosen:** Laptop, about 1440 wide

## General

So I want this tool to be genuinely useful for consultants. I think that's the entire pitch. That it reduces or it takes less effort to the AI things and you can still get good reports. And like you can still do great work with the type of data that AI can go through and AI can give you. So the content has to be very good. So even the analysis that we're doing for evidences, the output that we get out of it should be something that the consultant can actually useful to the consultant. this goes for all the screens. how RFI is being presented, how questions in the questionnaire are being framed, how the AI responses read to a consultant. how different deliverables across the product's use cater to the eyes that deliverable is meant for. internal work papers optimize dfor the auditor. reports for the boards and executives. etc.

