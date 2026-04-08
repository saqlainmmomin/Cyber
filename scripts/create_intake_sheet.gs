/**
 * DPDPA Gap Assessment — Google Sheets Intake Form Generator
 *
 * INSTRUCTIONS:
 * 1. Open a new Google Sheet
 * 2. Go to Extensions → Apps Script
 * 3. Paste this entire file into the editor (replace any existing code)
 * 4. Click Run → createIntakeForm
 * 5. Grant permissions when prompted
 *
 * The script creates two sheets:
 *   "Context"    — Phase 1: Organizational context (15 questions)
 *   "Assessment" — Phase 2: 41 DPDPA compliance requirements
 *
 * For each engagement: File → Make a copy, rename to client name.
 */

// ─── Color Palette ────────────────────────────────────────────────────────────
const COLORS = {
  header_bg:    "#1a1a2e",
  header_fg:    "#ffffff",
  section_bg:   "#e8eaf6",
  section_fg:   "#1a237e",
  critical_bg:  "#fce4ec",
  high_bg:      "#fff3e0",
  medium_bg:    "#fffde7",
  low_bg:       "#f1f8e9",
  answer_bg:    "#f8f9fa",
  border:       "#dadce0",
  phase1_bg:    "#e3f2fd",
};

// ─── Answer Dropdowns ─────────────────────────────────────────────────────────
const COMPLIANCE_OPTIONS = [
  "Fully implemented",
  "Partially implemented",
  "Planned (not yet in place)",
  "Not implemented",
  "Not applicable",
];

// ─── Main Entry Point ─────────────────────────────────────────────────────────
function createIntakeForm() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Ensure a placeholder exists FIRST so we never drop to 0 sheets.
  // Reuse it if a previous failed run left it behind (insertSheet throws if name exists).
  let placeholder = ss.getSheetByName("_placeholder_");
  if (!placeholder) {
    placeholder = ss.insertSheet("_placeholder_");
  }

  // Now safe to delete any pre-existing named sheets
  ["Context", "Assessment", "Instructions"].forEach(name => {
    const existing = ss.getSheetByName(name);
    if (existing) ss.deleteSheet(existing);
  });

  // Also clear any leftover default "Sheet1" / blank sheets
  ss.getSheets().forEach(sh => {
    if (sh.getName() !== "_placeholder_") {
      if (sh.getLastRow() === 0 && sh.getLastColumn() === 0) {
        ss.deleteSheet(sh);
      }
    }
  });

  buildInstructionsSheet(ss);
  buildContextSheet(ss);
  buildAssessmentSheet(ss);

  // Remove the placeholder now that real sheets exist
  const tmp = ss.getSheetByName("_placeholder_");
  if (tmp) ss.deleteSheet(tmp);

  // Activate Instructions tab
  ss.setActiveSheet(ss.getSheetByName("Instructions"));

  SpreadsheetApp.getUi().alert(
    "✅ Intake form created!\n\n" +
    "• Instructions tab — how to use this sheet\n" +
    "• Context tab — Phase 1 (15 questions)\n" +
    "• Assessment tab — Phase 2 (41 requirements)\n\n" +
    "Make a copy for each new engagement."
  );
}

// ─── Instructions Sheet ───────────────────────────────────────────────────────
function buildInstructionsSheet(ss) {
  const sh = ss.insertSheet("Instructions");

  const rows = [
    ["DPDPA Gap Assessment — Intake Form", ""],
    ["CyberAssess | Confidential", ""],
    ["", ""],
    ["HOW TO USE THIS FORM", ""],
    ["", ""],
    ["1. File → Make a copy", "Rename the copy to the client company name before starting."],
    ["2. Context tab first", "Complete all Phase 1 questions. These set the risk profile used to weight results."],
    ["3. Assessment tab", "Work through all 41 DPDPA requirements. Use the dropdown in the Answer column."],
    ["4. Notes column", "Capture verbatim quotes from the interviewee. Direct quotes are more defensible."],
    ["5. Evidence column", "Note document name/screenshot file seen. E.g. 'privacy_policy_v2.pdf, section 3'."],
    ["6. After the interview", "Export as XLSX and upload to the CyberAssess API as document evidence."],
    ["", ""],
    ["ANSWER OPTIONS (Phase 2)", ""],
    ["Fully implemented", "Control exists, is enforced, and is documented."],
    ["Partially implemented", "Some elements in place but gaps exist (missing documentation, partial coverage, etc.)"],
    ["Planned (not yet in place)", "Formally planned with owner/timeline but not yet operational."],
    ["Not implemented", "No control exists. Gap confirmed."],
    ["Not applicable", "The requirement does not apply to this organization (state why in Notes)."],
    ["", ""],
    ["CRITICALITY LEGEND (Assessment tab row colours)", ""],
    ["🔴 CRITICAL", "Penalty exposure up to ₹250 crore. Must remediate first."],
    ["🟠 HIGH", "Significant regulatory risk. Remediate within 90 days."],
    ["🟡 MEDIUM", "Operational risk. Remediate within 180 days."],
  ];

  sh.getRange(1, 1, rows.length, 2).setValues(rows);

  // Locate key rows by content so indices stay correct if rows array changes
  function rowOf(label) {
    for (let i = 0; i < rows.length; i++) {
      if (rows[i][0] === label) return i + 1; // 1-based
    }
    return -1;
  }

  const rowAnswerHeader    = rowOf("ANSWER OPTIONS (Phase 2)");
  const rowLegendHeader    = rowOf("CRITICALITY LEGEND (Assessment tab row colours)");
  const rowCritical        = rowOf("🔴 CRITICAL");
  const rowHigh            = rowOf("🟠 HIGH");
  const rowMedium          = rowOf("🟡 MEDIUM");

  // Title formatting
  sh.getRange(1, 1).setFontSize(16).setFontWeight("bold").setFontColor(COLORS.header_bg);
  sh.getRange(2, 1).setFontSize(11).setFontColor("#757575");
  sh.getRange(rowOf("HOW TO USE THIS FORM"), 1).setFontWeight("bold").setFontSize(12);
  if (rowAnswerHeader > 0) sh.getRange(rowAnswerHeader, 1).setFontWeight("bold").setFontSize(12);
  if (rowLegendHeader > 0) sh.getRange(rowLegendHeader, 1).setFontWeight("bold").setFontSize(12);

  // Colour the criticality legend rows
  if (rowCritical > 0) sh.getRange(rowCritical, 1, 1, 2).setBackground(COLORS.critical_bg);
  if (rowHigh     > 0) sh.getRange(rowHigh,     1, 1, 2).setBackground(COLORS.high_bg);
  if (rowMedium   > 0) sh.getRange(rowMedium,   1, 1, 2).setBackground(COLORS.medium_bg);

  sh.setColumnWidth(1, 280);
  sh.setColumnWidth(2, 520);
  sh.setFrozenRows(0);
}

// ─── Context Sheet (Phase 1) ──────────────────────────────────────────────────
function buildContextSheet(ss) {
  const sh = ss.insertSheet("Context");

  // Column headers
  const headers = ["ID", "Section", "Question", "Answer / Selection", "Notes / Verbatim Quote", "Evidence Seen"];
  sh.getRange(1, 1, 1, headers.length).setValues([headers]);
  styleHeaderRow(sh, 1, headers.length);

  const ctx = contextQuestions();
  let row = 2;

  ctx.sections.forEach(section => {
    // Section sub-header
    sh.getRange(row, 1, 1, headers.length).merge()
      .setValue(section.title)
      .setBackground(COLORS.section_bg)
      .setFontColor(COLORS.section_fg)
      .setFontWeight("bold")
      .setFontSize(10);
    row++;

    section.questions.forEach(q => {
      sh.getRange(row, 1).setValue(q.id);
      sh.getRange(row, 2).setValue(section.title);
      sh.getRange(row, 3).setValue(q.question).setWrap(true);
      sh.getRange(row, 4).setBackground(COLORS.answer_bg).setWrap(true)
        .setNote(q.options ? "Options:\n• " + q.options.join("\n• ") : "Free text");
      sh.getRange(row, 5).setBackground("#ffffff");
      sh.getRange(row, 6).setBackground("#ffffff");

      // Add dropdown for single-select questions
      if (q.type === "single" && q.options) {
        const rule = SpreadsheetApp.newDataValidation()
          .requireValueInList(q.options, true)
          .setAllowInvalid(false)
          .build();
        sh.getRange(row, 4).setDataValidation(rule);
      }

      sh.getRange(row, 1, 1, headers.length).setBackground(COLORS.phase1_bg);
      sh.getRange(row, 4).setBackground(COLORS.answer_bg);
      row++;
    });
  });

  // Column widths
  sh.setColumnWidth(1, 110);
  sh.setColumnWidth(2, 160);
  sh.setColumnWidth(3, 380);
  sh.setColumnWidth(4, 220);
  sh.setColumnWidth(5, 280);
  sh.setColumnWidth(6, 220);
  sh.setFrozenRows(1);
  sh.setRowHeights(2, row - 2, 48);
}

// ─── Assessment Sheet (Phase 2) ───────────────────────────────────────────────
function buildAssessmentSheet(ss) {
  const sh = ss.insertSheet("Assessment");

  const headers = ["ID", "Chapter", "Section", "DPDPA Ref", "Criticality", "Question", "Probe", "Answer", "Notes / Verbatim Quote", "Evidence Seen"];
  sh.getRange(1, 1, 1, headers.length).setValues([headers]);
  styleHeaderRow(sh, 1, headers.length);

  const reqs = allRequirements();
  let row = 2;
  let lastChapter = "";

  reqs.forEach(req => {
    // Chapter sub-header when chapter changes
    if (req.chapter_title !== lastChapter) {
      sh.getRange(row, 1, 1, headers.length).merge()
        .setValue(`📋  ${req.chapter_title}  —  Chapter weight: ${req.chapter_weight}`)
        .setBackground(COLORS.section_bg)
        .setFontColor(COLORS.section_fg)
        .setFontWeight("bold")
        .setFontSize(10);
      row++;
      lastChapter = req.chapter_title;
    }

    const bgColor = criticalityColor(req.criticality);
    const critLabel = criticalityLabel(req.criticality);

    sh.getRange(row, 1).setValue(req.id);
    sh.getRange(row, 2).setValue(req.chapter_title);
    sh.getRange(row, 3).setValue(req.section_title);
    sh.getRange(row, 4).setValue(req.section_ref);
    sh.getRange(row, 5).setValue(critLabel).setFontWeight("bold");
    sh.getRange(row, 6).setValue(req.question).setWrap(true);
    sh.getRange(row, 7).setValue(req.probe || "").setWrap(true).setFontColor("#616161").setFontStyle("italic");
    sh.getRange(row, 8).setBackground(COLORS.answer_bg);
    sh.getRange(row, 9).setBackground("#ffffff");
    sh.getRange(row, 10).setBackground("#ffffff");

    // Compliance dropdown
    const rule = SpreadsheetApp.newDataValidation()
      .requireValueInList(COMPLIANCE_OPTIONS, true)
      .setAllowInvalid(false)
      .build();
    sh.getRange(row, 8).setDataValidation(rule);

    // Row background by criticality
    sh.getRange(row, 1, 1, headers.length).setBackground(bgColor);
    sh.getRange(row, 8).setBackground(COLORS.answer_bg);

    row++;
  });

  // Column widths
  sh.setColumnWidth(1, 120);
  sh.setColumnWidth(2, 170);
  sh.setColumnWidth(3, 160);
  sh.setColumnWidth(4, 110);
  sh.setColumnWidth(5, 90);
  sh.setColumnWidth(6, 380);
  sh.setColumnWidth(7, 280);
  sh.setColumnWidth(8, 200);
  sh.setColumnWidth(9, 280);
  sh.setColumnWidth(10, 220);
  sh.setFrozenRows(1);
  sh.setRowHeights(2, row - 2, 60);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function styleHeaderRow(sh, row, numCols) {
  const range = sh.getRange(row, 1, 1, numCols);
  range.setBackground(COLORS.header_bg)
    .setFontColor(COLORS.header_fg)
    .setFontWeight("bold")
    .setFontSize(10);
  sh.setRowHeight(row, 32);
}

function criticalityColor(c) {
  switch (c) {
    case "critical": return COLORS.critical_bg;
    case "high":     return COLORS.high_bg;
    case "medium":   return COLORS.medium_bg;
    default:         return COLORS.low_bg;
  }
}

function criticalityLabel(c) {
  switch (c) {
    case "critical": return "🔴 CRITICAL";
    case "high":     return "🟠 HIGH";
    case "medium":   return "🟡 MEDIUM";
    default:         return "⚪ LOW";
  }
}

// ─── Phase 1 — Context Questions ─────────────────────────────────────────────
function contextQuestions() {
  return {
    sections: [
      {
        title: "Data Landscape",
        questions: [
          {
            id: "CTX.DATA.1",
            question: "What categories of personal data does your organization collect?",
            type: "multi",
            options: [
              "Identity data (name, DOB, address, ID numbers)",
              "Financial data (bank accounts, cards, transactions)",
              "Health / medical data",
              "Biometric data (fingerprints, face, voice)",
              "Location data (GPS, IP-derived)",
              "Behavioral / usage data",
              "Children's data (under 18)",
              "Other",
            ],
          },
          {
            id: "CTX.DATA.2",
            question: "What is your primary mechanism for collecting personal data?",
            type: "single",
            options: ["Web forms", "Mobile app", "Third-party APIs", "Physical forms", "Automated tracking (cookies, pixels)"],
          },
          {
            id: "CTX.DATA.3",
            question: "Do you use third-party data processors or SaaS vendors who handle personal data on your behalf?",
            type: "single",
            options: ["Yes", "No", "Unsure"],
          },
          {
            id: "CTX.DATA.4",
            question: "Do you transfer personal data outside India?",
            type: "single",
            options: ["Yes", "No", "Unsure"],
          },
          {
            id: "CTX.DATA.4a",
            question: "If yes to CTX.DATA.4 — which regions/countries do you transfer data to?",
            type: "free",
          },
        ],
      },
      {
        title: "Existing Posture",
        questions: [
          {
            id: "CTX.POSTURE.1",
            question: "Do you have a dedicated privacy or Data Protection Officer function?",
            type: "single",
            options: ["Full-time DPO / privacy function", "Part-time or shared responsibility", "No"],
          },
          {
            id: "CTX.POSTURE.2",
            question: "Do you have an existing information security program?",
            type: "single",
            options: ["ISO 27001 certified", "SOC 2 certified", "Internal policy only (no external certification)", "None"],
          },
          {
            id: "CTX.POSTURE.3",
            question: "Have you undergone any privacy or security audit in the past 2 years?",
            type: "single",
            options: ["External audit conducted", "Internal audit only", "No"],
          },
          {
            id: "CTX.POSTURE.4",
            question: "Do you have a documented privacy policy published to users?",
            type: "single",
            options: ["Yes, recently updated (within 12 months)", "Yes, but outdated (older than 12 months)", "No"],
          },
        ],
      },
      {
        title: "Risk Exposure",
        questions: [
          {
            id: "CTX.RISK.1",
            question: "Which of the following apply to your organization? (tick all that apply)",
            type: "multi",
            options: [
              "Processes children's data (under 18)",
              "Healthcare, finance, or critical infrastructure sector",
              "Handles sensitive personal data",
              "Designated or likely Significant Data Fiduciary (SDF)",
              "None",
            ],
          },
          {
            id: "CTX.RISK.2",
            question: "Roughly how many data principals (individuals whose data you hold) are affected?",
            type: "single",
            options: ["Under 10,000", "10,000 to 1 million", "1 million to 10 million", "Over 10 million"],
          },
          {
            id: "CTX.RISK.3",
            question: "In the last 2 years, have you experienced any data breach or security incident?",
            type: "single",
            options: ["Yes, and it was reported to authorities", "Yes, but it was not reported", "No", "Unsure"],
          },
        ],
      },
      {
        title: "Initiative Context",
        questions: [
          {
            id: "CTX.INIT.1",
            question: "What is the primary driver for this assessment?",
            type: "single",
            options: [
              "Regulatory audit preparation",
              "Investor or board requirement",
              "Customer due diligence / vendor questionnaire",
              "Proactive compliance initiative",
              "Post-incident review",
            ],
          },
          {
            id: "CTX.INIT.2",
            question: "What is your target compliance timeline?",
            type: "single",
            options: ["Under 3 months", "3 to 6 months", "6 to 12 months", "No hard deadline"],
          },
          {
            id: "CTX.INIT.3",
            question: "What is your approximate budget band for remediation?",
            type: "single",
            options: [
              "Under Rs. 5 lakh",
              "Rs. 5 lakh to Rs. 25 lakh",
              "Rs. 25 lakh to Rs. 1 crore",
              "Above Rs. 1 crore",
              "Not yet defined",
            ],
          },
        ],
      },
    ],
  };
}

// ─── Phase 2 — All 41 DPDPA Requirements ─────────────────────────────────────
function allRequirements() {
  return [
    // ── Chapter 2: Obligations of Data Fiduciary (weight 30%) ──────────────
    // Consent Management
    { id: "CH2.CONSENT.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Consent Management", section_ref: "Section 6(1)-(2)", criticality: "critical",
      question: "Does your organization obtain free, specific, informed, and unambiguous consent from data principals before processing their personal data?",
      probe: "Can you show me an example of a consent screen or form a user would see?" },
    { id: "CH2.CONSENT.2", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Consent Management", section_ref: "Section 6(3)", criticality: "high",
      question: "When processing data for multiple purposes, do you obtain separate (itemised) consent for each purpose?",
      probe: "If you process data for multiple purposes (e.g., service delivery AND marketing), do users consent to each separately?" },
    { id: "CH2.CONSENT.3", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Consent Management", section_ref: "Section 6(6)-(7)", criticality: "critical",
      question: "Can data principals withdraw their consent as easily as they gave it, and do you stop processing upon withdrawal?",
      probe: "Walk me through how a user would withdraw consent today — what steps, how long does it take?" },
    { id: "CH2.CONSENT.4", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Consent Management", section_ref: "Section 6(8)-(9)", criticality: "medium",
      question: "If you use a Consent Manager, is it registered with the Data Protection Board and does it provide a transparent consent management platform?",
      probe: "" },
    { id: "CH2.CONSENT.5", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Consent Management", section_ref: "Section 9(1)", criticality: "critical",
      question: "Do you obtain verifiable parental or guardian consent before processing personal data of children (under 18) or persons with disabilities?",
      probe: "How do you verify a user is 18 or older before collecting their data?" },

    // Notice
    { id: "CH2.NOTICE.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Notice Requirements", section_ref: "Section 5(1)", criticality: "critical",
      question: "Do you provide a clear privacy notice to data principals at or before the time of collecting their personal data, describing what data is collected and why?",
      probe: "Can you show me the privacy notice a user sees when they first sign up?" },
    { id: "CH2.NOTICE.2", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Notice Requirements", section_ref: "Section 5(2)", criticality: "high",
      question: "For personal data collected before the DPDPA came into effect, have you provided a retrospective notice to data principals?",
      probe: "For users who registered before DPDPA came into force — have they received any retrospective communication?" },
    { id: "CH2.NOTICE.3", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Notice Requirements", section_ref: "Section 5(1)", criticality: "medium",
      question: "Does your privacy notice include contact details of a Data Protection Officer or designated grievance officer?",
      probe: "Where in your notice does a user find who to contact with a privacy question?" },

    // Purpose Limitation
    { id: "CH2.PURPOSE.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Purpose Limitation", section_ref: "Section 4(1)", criticality: "critical",
      question: "Is personal data processed only for the specific purpose for which consent was obtained or a legitimate use applies?",
      probe: "Has there ever been a case where you used user data for a purpose beyond what was originally disclosed? How was it handled?" },
    { id: "CH2.PURPOSE.2", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Purpose Limitation", section_ref: "Section 7", criticality: "high",
      question: "Have you documented all cases where you process personal data without consent under the legitimate use provisions (Section 7)?",
      probe: "" },

    // Data Minimization
    { id: "CH2.MINIMIZE.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Data Minimization & Storage Limitation", section_ref: "Section 4(1)", criticality: "high",
      question: "Do you limit the collection of personal data to only what is necessary for the stated purpose?",
      probe: "" },
    { id: "CH2.MINIMIZE.2", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Data Minimization & Storage Limitation", section_ref: "Section 8(7)", criticality: "high",
      question: "Is personal data erased once the purpose for which it was collected is no longer being served?",
      probe: "What happens to a user's data when they close their account?" },
    { id: "CH2.MINIMIZE.3", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Data Minimization & Storage Limitation", section_ref: "Section 8(7)", criticality: "medium",
      question: "Do you maintain documented data retention schedules with systematic deletion procedures?",
      probe: "Do you have a documented retention schedule? Can I see it?" },

    // Accuracy
    { id: "CH2.ACCURACY.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Data Accuracy", section_ref: "Section 8(3)", criticality: "medium",
      question: "Do you make reasonable efforts to ensure personal data remains complete, accurate, and not misleading?",
      probe: "" },

    // Security
    { id: "CH2.SECURITY.1", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Security Safeguards", section_ref: "Section 8(4)", criticality: "critical",
      question: "Have you implemented reasonable technical and organizational security safeguards to protect personal data from breaches?",
      probe: "What security certifications or penetration tests have you done in the last 12 months?" },
    { id: "CH2.SECURITY.2", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Security Safeguards", section_ref: "Section 8(4)", criticality: "critical",
      question: "Is personal data encrypted at rest and in transit, with access controls based on the principle of least privilege?",
      probe: "Is data encrypted at rest in your primary database and in backups?" },
    { id: "CH2.SECURITY.3", chapter_title: "Obligations of Data Fiduciary", chapter_weight: "30%", section_title: "Security Safeguards", section_ref: "Section 8(2)", criticality: "high",
      question: "Do you have valid contracts with all Data Processors that include obligations for security safeguards and processing instructions?",
      probe: "Do your vendor contracts (AWS, CRM, analytics tools) include data processing agreements?" },

    // ── Chapter 3: Rights of Data Principal (weight 20%) ───────────────────
    { id: "CH3.ACCESS.1", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Right to Access Information", section_ref: "Section 11(1)", criticality: "high",
      question: "Can data principals request and receive a summary of their personal data and the processing activities you undertake on it?",
      probe: "How would a user request a copy of their personal data today? Walk me through the process." },
    { id: "CH3.CORRECT.1", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Right to Correction & Erasure", section_ref: "Section 12(1)", criticality: "high",
      question: "Can data principals request correction of inaccurate or misleading personal data and completion of incomplete data?",
      probe: "If a user says their information is wrong, what's the process to get it corrected?" },
    { id: "CH3.CORRECT.2", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Right to Correction & Erasure", section_ref: "Section 12(2)", criticality: "high",
      question: "Can data principals request erasure of personal data that is no longer necessary for the original purpose?",
      probe: "If a user asks to be deleted, what systems does their data get removed from?" },
    { id: "CH3.GRIEVANCE.1", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Grievance Redressal", section_ref: "Section 13(1)", criticality: "critical",
      question: "Do you have an accessible grievance redressal mechanism with a designated person or officer to handle data principal complaints?",
      probe: "Is there a named person responsible for privacy complaints? Is their contact published?" },
    { id: "CH3.GRIEVANCE.2", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Grievance Redressal", section_ref: "Section 13(2)", criticality: "high",
      question: "Do you respond to data principal grievances within a reasonable timeframe and inform them of their right to approach the Data Protection Board?",
      probe: "What is your SLA for responding to a privacy complaint? Is it documented?" },
    { id: "CH3.NOMINATE.1", chapter_title: "Rights of Data Principal", chapter_weight: "20%", section_title: "Right of Nomination", section_ref: "Section 14", criticality: "medium",
      question: "Can data principals nominate another individual to exercise their rights in the event of death or incapacity?",
      probe: "" },

    // ── Chapter 4: Special Provisions (weight 20%) ──────────────────────────
    { id: "CH4.CHILD.1", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Children's Data Protection", section_ref: "Section 9(2)", criticality: "critical",
      question: "Does your organization refrain from tracking, behavioural monitoring, or targeted advertising directed at children?",
      probe: "Do any of your marketing or targeting systems use age as a signal?" },
    { id: "CH4.CHILD.2", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Children's Data Protection", section_ref: "Section 9(3)", criticality: "critical",
      question: "Do you ensure that processing of children's personal data does not have a detrimental effect on their well-being?",
      probe: "" },
    { id: "CH4.CHILD.3", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Children's Data Protection", section_ref: "Section 9", criticality: "high",
      question: "Do you have age verification mechanisms to identify children and apply appropriate data protections?",
      probe: "How do you identify if a user is under 18 at sign-up?" },
    { id: "CH4.SDF.1", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Significant Data Fiduciary (SDF) Obligations", section_ref: "Section 10(2)(a)", criticality: "critical",
      question: "If your organization is (or may be) designated as a Significant Data Fiduciary, have you appointed a Data Protection Officer based in India?",
      probe: "Has your organization been assessed for Significant Data Fiduciary designation?" },
    { id: "CH4.SDF.2", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Significant Data Fiduciary (SDF) Obligations", section_ref: "Section 10(2)(b)", criticality: "high",
      question: "Have you appointed an independent Data Auditor to evaluate your compliance with the DPDPA?",
      probe: "" },
    { id: "CH4.SDF.3", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Significant Data Fiduciary (SDF) Obligations", section_ref: "Section 10(2)(c)", criticality: "high",
      question: "Do you conduct periodic Data Protection Impact Assessments (DPIAs) for your processing activities?",
      probe: "" },
    { id: "CH4.SDF.4", chapter_title: "Special Provisions", chapter_weight: "20%", section_title: "Significant Data Fiduciary (SDF) Obligations", section_ref: "Section 10(2)(d)", criticality: "high",
      question: "Do you conduct periodic compliance audits of your data processing activities as prescribed?",
      probe: "" },

    // ── Consent Management (Detailed) (weight 10%) ──────────────────────────
    { id: "CM.RECORDS.1", chapter_title: "Consent Management (Detailed)", chapter_weight: "10%", section_title: "Consent Records & Lifecycle", section_ref: "Section 6", criticality: "high",
      question: "Do you maintain auditable records of when, how, and for what purpose consent was obtained from each data principal?",
      probe: "Where is consent stored? Can you pull up a record showing when a specific user gave consent?" },
    { id: "CM.RECORDS.2", chapter_title: "Consent Management (Detailed)", chapter_weight: "10%", section_title: "Consent Records & Lifecycle", section_ref: "Section 6", criticality: "medium",
      question: "Do you have a process to refresh or re-obtain consent when processing purposes change?",
      probe: "" },
    { id: "CM.GRANULAR.1", chapter_title: "Consent Management (Detailed)", chapter_weight: "10%", section_title: "Granular Consent Controls", section_ref: "Section 6(3)", criticality: "high",
      question: "Can data principals provide or withhold consent at a granular per-purpose level?",
      probe: "" },
    { id: "CM.GRANULAR.2", chapter_title: "Consent Management (Detailed)", chapter_weight: "10%", section_title: "Granular Consent Controls", section_ref: "Section 6(1)", criticality: "critical",
      question: "Is access to your services independent of consent to non-essential data processing (i.e., no consent bundling or dark patterns)?",
      probe: "Is consent to non-essential data (e.g., analytics, marketing) a condition for using the app?" },

    // ── Cross-Border Data Transfer (weight 10%) ─────────────────────────────
    { id: "CB.TRANSFER.1", chapter_title: "Cross-Border Data Transfer", chapter_weight: "10%", section_title: "Transfer Restrictions & Controls", section_ref: "Section 16(1)", criticality: "critical",
      question: "Do you transfer personal data only to countries not restricted by the Central Government, and maintain an inventory of cross-border data flows?",
      probe: "Which countries does your data land in? AWS region, CRM vendor location?" },
    { id: "CB.TRANSFER.2", chapter_title: "Cross-Border Data Transfer", chapter_weight: "10%", section_title: "Transfer Restrictions & Controls", section_ref: "Section 16", criticality: "high",
      question: "Do you have contractual or legal safeguards in place for data transferred outside India?",
      probe: "" },
    { id: "CB.TRANSFER.3", chapter_title: "Cross-Border Data Transfer", chapter_weight: "10%", section_title: "Transfer Restrictions & Controls", section_ref: "Section 16", criticality: "high",
      question: "Where mandated, do you store certain categories of personal data within India (data localisation)?",
      probe: "" },

    // ── Breach Notification (weight 10%) ────────────────────────────────────
    { id: "BN.NOTIFY.1", chapter_title: "Breach Notification", chapter_weight: "10%", section_title: "Breach Detection & Notification", section_ref: "Section 8(6)", criticality: "critical",
      question: "Do you have procedures to notify the Data Protection Board of India in case of a personal data breach?",
      probe: "If a breach happened tonight, who is the first person notified internally? Do you have a runbook?" },
    { id: "BN.NOTIFY.2", chapter_title: "Breach Notification", chapter_weight: "10%", section_title: "Breach Detection & Notification", section_ref: "Section 8(6)", criticality: "critical",
      question: "Do you have procedures to notify affected data principals in case of a personal data breach?",
      probe: "" },
    { id: "BN.NOTIFY.3", chapter_title: "Breach Notification", chapter_weight: "10%", section_title: "Breach Detection & Notification", section_ref: "Section 8(4)-(6)", criticality: "high",
      question: "Do you have a documented incident response plan covering detection, containment, investigation, notification, and remediation?",
      probe: "Do you have a documented incident response plan? When was it last tested?" },
    { id: "BN.NOTIFY.4", chapter_title: "Breach Notification", chapter_weight: "10%", section_title: "Breach Detection & Notification", section_ref: "Section 8(6)", criticality: "medium",
      question: "Do you maintain a register of all personal data breaches including facts, effects, and remedial actions?",
      probe: "" },
  ];
}

// ─── Prestige Constructions — Pre-filled Answers ──────────────────────────────
// Source: Prestige privacy policy (public) + internal assessment context (Apr 2026)
// Run this AFTER createIntakeForm() to populate answers for the Prestige engagement.
// Adds answers and analyst notes; leaves Evidence Seen column blank for the interview.
//
// HOW TO RUN:
//   Extensions → Apps Script → select fillPrestigeAnswers → Run
// ──────────────────────────────────────────────────────────────────────────────
function fillPrestigeAnswers() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // ── Context answers ─────────────────────────────────────────────────────────
  // Sheet columns: A=ID, B=Section, C=Question, D=Answer, E=Notes, F=Evidence
  const ctxAnswers = {
    "CTX.DATA.1":    { answer: "Identity data (name, DOB, address, ID numbers), Financial data (bank accounts, cards, transactions), Behavioral / usage data",
                       note:   "Policy confirms forms, website, social, site visits. Internal context: physical store holds Aadhaar copies, PAN, bank details — sensitive personal data category applies." },
    "CTX.DATA.2":    { answer: "Web forms",
                       note:   "Primary digital channel is web forms + email. Also physical forms at property visits. Multiple collection points." },
    "CTX.DATA.3":    { answer: "Yes",
                       note:   "Policy: 'sharing with vendor partners for operational needs; third-party service providers.' No DPDPA-compliant DPAs confirmed." },
    "CTX.DATA.4":    { answer: "Unsure",
                       note:   "Policy: 'not explicitly detailed.' Third-party SaaS tools (CRM, marketing platforms) may route data offshore — not inventoried." },
    "CTX.DATA.4a":   { answer: "",
                       note:   "Unknown. Ask about CRM provider, email platform, cloud hosting region." },
    "CTX.POSTURE.1": { answer: "No",
                       note:   "Internal context confirms no designated DPO or grievance officer. Policy does not name one." },
    "CTX.POSTURE.2": { answer: "Internal policy only (no external certification)",
                       note:   "Policy lists encryption, firewalls, IDS, audits — but no ISO 27001 or SOC 2 certification mentioned." },
    "CTX.POSTURE.3": { answer: "No",
                       note:   "No audit history referenced in policy or internal context. SEBI guidelines mentioned but no evidence of compliance audit." },
    "CTX.POSTURE.4": { answer: "Yes, but outdated (older than 12 months)",
                       note:   "Policy exists but version date unknown. Age threshold stated as 'under 13' — DPDPA requires under 18. Indicates policy predates or was not updated for DPDPA." },
    "CTX.RISK.1":    { answer: "Handles sensitive personal data",
                       note:   "Physical store holds Aadhaar, PAN, banking details = sensitive personal data under DPDPA. Real estate sector; SEBI-listed entity (elevated regulatory exposure)." },
    "CTX.RISK.2":    { answer: "10,000 to 1 million",
                       note:   "~1000 employees. Active real estate developer with large customer base across residential/commercial projects. Estimate: tens of thousands of leads/customers in CRM." },
    "CTX.RISK.3":    { answer: "No",
                       note:   "No breach history disclosed. Permission leaks in internal sales tool noted — treat as unconfirmed latent risk." },
    "CTX.INIT.1":    { answer: "Proactive compliance initiative",
                       note:   "Unsolicited assessment — Prestige has not initiated this engagement. Frame deliverable as proactive readiness review." },
    "CTX.INIT.2":    { answer: "No hard deadline",
                       note:   "DPDPA rules not yet fully notified. Recommend 6–12 month window given depth of gaps." },
    "CTX.INIT.3":    { answer: "Not yet defined",
                       note:   "Unsolicited engagement — no budget discussion yet. Remediation scope will drive estimate." },
  };

  // ── Assessment answers ───────────────────────────────────────────────────────
  // Sheet columns: A=ID, B=Chapter, C=Section, D=Ref, E=Criticality, F=Question, G=Probe, H=Answer, I=Notes, J=Evidence
  const asmAnswers = {
    "CH2.CONSENT.1": { answer: "Partially implemented",
                       note:   "Policy claims checkboxes + explicit consent. No consent management platform, no audit trail. Withdrawal only via contact form — not equivalent to ease of giving consent." },
    "CH2.CONSENT.2": { answer: "Not implemented",
                       note:   "Marketing and operational processing bundled. No evidence of per-purpose itemised consent. Policy groups all purposes under a single consent." },
    "CH2.CONSENT.3": { answer: "Partially implemented",
                       note:   "Withdrawal path: contact the organisation. Not self-serve. Likely days-long turnaround. Does not meet 'as easy as giving' standard." },
    "CH2.CONSENT.4": { answer: "Not implemented",
                       note:   "No consent manager mentioned. No DPB registration. Not applicable if volume is under threshold — but threshold not yet notified." },
    "CH2.CONSENT.5": { answer: "Not implemented",
                       note:   "Policy says 'under 13' — DPDPA mandates parental consent for under 18. Age threshold is wrong. No verifiable verification mechanism described." },
    "CH2.NOTICE.1":  { answer: "Partially implemented",
                       note:   "Public privacy policy exists. No evidence of a just-in-time notice at point of data collection (web forms, site visit forms). Policy is high-level, not purpose-specific." },
    "CH2.NOTICE.2":  { answer: "Not implemented",
                       note:   "No retrospective notice to existing customers/leads referenced anywhere in policy or internal context." },
    "CH2.NOTICE.3":  { answer: "Not implemented",
                       note:   "No DPO or grievance officer named in policy. Contact section shows generic sales/admin numbers — not a designated privacy contact." },
    "CH2.PURPOSE.1": { answer: "Partially implemented",
                       note:   "Policy lists purposes but bundles service delivery, marketing, and vendor sharing. Vendor sharing 'for operational needs' is broad — lacks specificity required by Section 4(1)." },
    "CH2.PURPOSE.2": { answer: "Not implemented",
                       note:   "No documentation of legitimate use cases under Section 7. No registry of processing activities without consent." },
    "CH2.MINIMIZE.1": { answer: "Partially implemented",
                        note:   "Retention clause present. However physical storage of Aadhaar + PAN + banking details for all site visitors suggests over-collection beyond the stated purpose of lead management." },
    "CH2.MINIMIZE.2": { answer: "Partially implemented",
                        note:   "Policy: 'retained only as long as necessary.' No specifics on what happens to data when a lead goes cold or a transaction completes. No account deletion mechanism visible." },
    "CH2.MINIMIZE.3": { answer: "Not implemented",
                        note:   "No documented retention schedule. Physical documents (Aadhaar/PAN copies) almost certainly have no formal retention or destruction policy." },
    "CH2.ACCURACY.1": { answer: "Partially implemented",
                        note:   "Policy grants right to correct. No systematic data quality programme. Physical document copies likely never refreshed." },
    "CH2.SECURITY.1": { answer: "Partially implemented",
                        note:   "Policy lists encryption, firewalls, IDS, 'regular security audits.' No third-party certification. Internal context: permission leaks in sales tool — gaps in access control confirmed." },
    "CH2.SECURITY.2": { answer: "Partially implemented",
                        note:   "Encryption stated. Permission leaks in internal tool = access control failure. Physical PII stored in facility — encryption of physical media not addressed." },
    "CH2.SECURITY.3": { answer: "Partially implemented",
                        note:   "Vendors 'contractually obligated to maintain confidentiality.' These are confidentiality clauses, not DPDPA-compliant Data Processing Agreements (DPAs) specifying processing instructions, audit rights, breach notification." },
    "CH3.ACCESS.1":  { answer: "Partially implemented",
                       note:   "Right to access stated in policy. No mechanism, portal, or SLA described. Contact-based only — not scalable." },
    "CH3.CORRECT.1": { answer: "Partially implemented",
                       note:   "Right to correct stated. No self-serve mechanism. Contact-based only." },
    "CH3.CORRECT.2": { answer: "Partially implemented",
                       note:   "Right to erasure stated. No clear process. Physical document destruction not addressed. CRM and downstream vendor copies not addressed." },
    "CH3.GRIEVANCE.1": { answer: "Not implemented",
                         note:   "No designated grievance officer or DPO. Generic corporate contact details only. Critical gap — Section 13 requires a named, accessible contact." },
    "CH3.GRIEVANCE.2": { answer: "Not implemented",
                         note:   "No SLA, no escalation path to DPB mentioned, no documented process. Policy-level right acknowledged but operationally hollow." },
    "CH3.NOMINATE.1": { answer: "Not implemented",
                        note:   "Right of nomination under Section 14 not mentioned anywhere in policy." },
    "CH4.CHILD.1":   { answer: "Not implemented",
                       note:   "Policy states marketing campaigns across multiple platforms. No age-gating or exclusion of children from behavioural targeting confirmed. High risk given CRITICAL classification." },
    "CH4.CHILD.2":   { answer: "Not implemented",
                       note:   "No child wellbeing assessment conducted or referenced." },
    "CH4.CHILD.3":   { answer: "Not implemented",
                       note:   "Policy mentions age verification 'under 13' — wrong threshold for DPDPA (under 18). Mechanism described as process-based only; no technical enforcement." },
    "CH4.SDF.1":     { answer: "Not applicable",
                       note:   "Prestige is likely not designated as SDF. Real estate sector; no indication of >10M data principals or government designation. Confirm post-DPDPA rules notification." },
    "CH4.SDF.2":     { answer: "Not applicable",
                       note:   "SDF-only obligation. Mark N/A pending SDF designation assessment." },
    "CH4.SDF.3":     { answer: "Not implemented",
                       note:   "Internal context: 'No DPIA or periodic compliance audits conducted.' DPIAs are best practice regardless of SDF status for high-risk processing (sensitive data, children's data)." },
    "CH4.SDF.4":     { answer: "Not applicable",
                       note:   "SDF-only obligation. However internal compliance reviews are zero — even non-SDF fiduciaries should maintain audit evidence." },
    "CM.RECORDS.1":  { answer: "Not implemented",
                       note:   "Internal context: 'No formal consent management or audit trail system.' Cannot produce a consent record for any individual. Critical evidence gap." },
    "CM.RECORDS.2":  { answer: "Not implemented",
                       note:   "No consent refresh process. Marketing purposes appear permanent — no mechanism to update consent when processing scope changes." },
    "CM.GRANULAR.1": { answer: "Not implemented",
                       note:   "No per-purpose consent controls. Single bundled consent covers service delivery, marketing, and vendor sharing." },
    "CM.GRANULAR.2": { answer: "Not implemented",
                       note:   "No evidence that service access is separated from marketing consent. Likely dark pattern — checkbox may be pre-ticked or required. Confirm in interview." },
    "CB.TRANSFER.1": { answer: "Not implemented",
                       note:   "Policy: cross-border transfers 'not explicitly detailed.' No inventory of data flows. Third-party SaaS tools (CRM, email) likely route data offshore without documentation." },
    "CB.TRANSFER.2": { answer: "Not implemented",
                       note:   "Vendor contracts have confidentiality clauses but no standard contractual clauses or adequacy assessment for cross-border transfers." },
    "CB.TRANSFER.3": { answer: "Not applicable",
                       note:   "No data localisation mandate currently applies to real estate sector. Confirm when DPDPA rules are notified." },
    "BN.NOTIFY.1":   { answer: "Partially implemented",
                       note:   "Policy commits to 72-hour DPB notification. No documented runbook, no named incident owner, no tested procedure. Commitment without operationalisation." },
    "BN.NOTIFY.2":   { answer: "Partially implemented",
                       note:   "Policy commits to notifying affected individuals. Same gap: no process, no template, no SLA beyond 'as soon as possible.'" },
    "BN.NOTIFY.3":   { answer: "Not implemented",
                       note:   "No incident response plan documented or referenced. Internal sales tool permission leaks have not triggered any incident review." },
    "BN.NOTIFY.4":   { answer: "Not implemented",
                       note:   "No breach register. No breach history disclosed — but absence of register means any past incidents are untracked." },
  };

  // ── Fill Context sheet ───────────────────────────────────────────────────────
  const ctxSheet = ss.getSheetByName("Context");
  if (!ctxSheet) {
    SpreadsheetApp.getUi().alert("Context sheet not found. Run createIntakeForm() first.");
    return;
  }
  const ctxData = ctxSheet.getDataRange().getValues();
  for (let r = 0; r < ctxData.length; r++) {
    const id = ctxData[r][0];
    if (ctxAnswers[id]) {
      ctxSheet.getRange(r + 1, 4).setValue(ctxAnswers[id].answer);  // col D = Answer
      ctxSheet.getRange(r + 1, 5).setValue(ctxAnswers[id].note);    // col E = Notes
    }
  }

  // ── Fill Assessment sheet ────────────────────────────────────────────────────
  const asmSheet = ss.getSheetByName("Assessment");
  if (!asmSheet) {
    SpreadsheetApp.getUi().alert("Assessment sheet not found. Run createIntakeForm() first.");
    return;
  }
  const asmData = asmSheet.getDataRange().getValues();
  for (let r = 0; r < asmData.length; r++) {
    const id = asmData[r][0];
    if (asmAnswers[id]) {
      asmSheet.getRange(r + 1, 8).setValue(asmAnswers[id].answer);  // col H = Answer
      asmSheet.getRange(r + 1, 9).setValue(asmAnswers[id].note);    // col I = Notes
    }
  }

  SpreadsheetApp.getUi().alert(
    "✅ Prestige answers loaded!\n\n" +
    "• Context tab — 15 questions pre-filled\n" +
    "• Assessment tab — 41 requirements pre-filled\n\n" +
    "Evidence Seen columns are intentionally blank.\n" +
    "Review Notes column — add or override before running the analysis."
  );
}
