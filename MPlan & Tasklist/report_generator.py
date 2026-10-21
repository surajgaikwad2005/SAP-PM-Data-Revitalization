"""Standalone PDF report generator for Agent C (SAP PM Task List / Maintenance Plan validation).

Reads the ALREADY-WRITTEN `SAP_PM_Agent_Findings_Summary.xlsx` workbook (Summary + Flag_Breakdown
sheets) and renders a client-style assessment report (HTML -> PDF via xhtml2pdf), modeled on the
Petronas "FL Criticality Mapping for Bokor" reference document structure.

This module does NOT touch validation.py and does NOT re-run the pipeline. It is a pure
post-processing / reporting step that can be re-run quickly against an existing Excel output.

Entry point:
    generate_pdf_report(summary_path: str, output_path: str) -> None

Several values in the generated report are deliberately generic PLACEHOLDERS because this
codebase has no real source of truth for them (approval signatures, specific review-team names,
a formal document-number registry). Every such placeholder is called out in the module-level
PLACEHOLDER_NOTES list below and should be reviewed by the user before the report is treated as
client-ready.
"""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

import pandas as pd

from output_writer import PAIN_POINT_NAMES

# ---------------------------------------------------------------------------
# Placeholders used in this report — flagged here (and in the final chat report
# back to the user) so nothing fabricated slips through unnoticed.
# ---------------------------------------------------------------------------
PLACEHOLDER_NOTES = [
    "Document number scheme 'AGENTC.BOKOR.R.001' is invented for this report — no real "
    "document-numbering registry exists in this codebase.",
    "Prepared/Reviewed/Approved-by table has blank name/signature/date cells — fill in by hand.",
    "Document status is fixed to 'For Review' — never claim 'Approved' since no approval occurred.",
    "Document Risk Assessment checklist defaults all 6 questions to 'No' as a hand-editable "
    "template — these are NOT real assessed answers.",
    "Conclusion & Way Forward next-steps reference a generic '[Client Review Team]' placeholder "
    "instead of a real team name (e.g. the reference doc's own 'SKA PMMS'/'JDA3' are NOT reused "
    "here since they may not be this engagement's real team names).",
    "Revision History 'Revised By' cell is left blank — no real author name is fabricated.",
]

DOCUMENT_NUMBER = "AGENTC.BOKOR.R.001"
REPORT_TITLE = "Agent C - Task List & Maintenance Plan Validation Report for Bokor"
CLIENT_REVIEW_TEAM_PLACEHOLDER = "[Client Review Team]"

ACCENT_DARK = "#1F3864"
ACCENT_MID = "#2E5395"
ACCENT_LIGHT = "#D9E2F3"
BORDER_COLOR = "#8EA9DB"

PAIN_POINTS = ["PP1", "PP2", "PP3", "PP4", "PP5", "PP6", "PP7"]

# Real companion workbooks produced by output_writer.py (referenced in the Appendices section).
COMPANION_WORKBOOKS = [
    ("SAP_PM_Agent_Recommendations.xlsx", "Full row-level detail for every record checked across all seven pain points, including suggested values and evidence."),
    ("SAP_PM_Agent_Findings_Summary.xlsx", "Curated findings-only view per pain point (this report's source data), plus the Summary and Flag_Breakdown sheets."),
]

# Real current status/flag vocabulary per pain point, sourced from output_writer.py's own column
# builders (PP_COLUMN_BUILDERS / PP_COLUMN_ORDER) — not guessed.
GLOSSARY_TERMS = [
    ("PP1", "Task List Naming", "Validates Task List Group naming conventions (prefix/naming structure) for consistency."),
    ("PP2", "Work Centre", "Validates that operation Work Centre (OPWKCEN) assignments match the expected work performed."),
    ("PP3", "Orphan Task List", "Identifies Task List Groups with no linked Maintenance Item / Maintenance Plan in the Knowledge Graph."),
    ("PP4", "Duplicate Task List", "Identifies Task List Groups that substantially or exactly duplicate another Task List Group's scope."),
    ("PP5", "Manhours", "Validates planned WORK (manhours) against PERSON x DURATION arithmetic and historical/JMS/OREDA evidence."),
    ("PP6", "Strategy / Frequency", "Validates Maintenance Strategy and Frequency assignments on Maintenance Items against Knowledge Graph evidence."),
    ("PP7", "Hanging Maintenance Item", "Identifies Maintenance Items with no resolvable Maintenance Plan assignment."),
    ("TLGRP", None, "SAP Task List Group identifier — the primary key grouping operations into a single maintenance task list."),
    ("TLGRPCOUNT", None, "SAP Task List Group Counter — disambiguates multiple task lists sharing the same TLGRP."),
    ("TLOPNO", None, "SAP Task List Operation Number — identifies an individual operation within a task list."),
    ("OPWKCEN", None, "SAP Operation Work Centre — the work centre responsible for executing a given operation."),
    ("WORK", None, "Planned total work (manhours) for an operation, as recorded in SAP."),
    ("PERSON", None, "Number of persons planned for an operation, as recorded in SAP."),
    ("DURATION", None, "Planned duration of an operation (paired with PERSON to derive WORK)."),
    ("KG", None, "Knowledge Graph — the live, queryable graph of SAP PM master data and supporting evidence that Agent C reasons over."),
    ("OREDA", None, "Offshore and Onshore Reliability Data — an industry reliability/maintenance benchmark dataset used as supporting evidence."),
    ("JMS", None, "Job Management System workpack records, used as historical execution evidence for manhour validation."),
    ("PITSTOPS", None, "PITSTOPS task-list evidence connector, used as a supporting data source for cross-referencing task-list content."),
    ("PREFIX_MISMATCH", None, "PP1 flag: the Task List Group's naming prefix does not match the expected convention."),
    ("NAMING_MISMATCH", None, "PP1 flag: the Task List Group name does not match the expected naming structure."),
    ("ORPHAN_TASK_LIST", None, "PP3 flag: the Task List Group has no linked Maintenance Item / Maintenance Plan."),
    ("VALID", None, "Status indicating the record was checked and no issue was found."),
    ("REVIEW_REQUIRED", None, "Status indicating the record requires manual review (e.g. ambiguous or borderline evidence)."),
    ("CONFLICT", None, "PP5 status: the planned WORK conflicts with available historical/JMS/OREDA evidence."),
    ("CANNOT_VERIFY", None, "Status indicating no usable evidence was found in any source to confirm or refute the current value."),
    ("EXACT_DUPLICATE", None, "PP4 flag: two Task List Groups are functionally identical."),
    ("STRONG_OVERLAP", None, "PP4 flag: two Task List Groups share a high degree of operational overlap."),
    ("PARTIAL_OVERLAP", None, "PP4 flag: two Task List Groups share some, but not most, operational content."),
    ("HANGING_MAINTENANCE_ITEM", None, "PP7 status: a Maintenance Item has no resolvable Maintenance Plan."),
]

RISK_ASSESSMENT_QUESTIONS = [
    "Does this report require changes to other controlled documents?",
    "Does this report require any resource adjustment (headcount, budget, schedule)?",
    "Does this report require any software or hardware change?",
    "Does this report require consultation with other stakeholders before action is taken?",
    "Does this report require additional training for affected personnel?",
    "Are there any other notes or considerations relevant to this report's risk profile?",
]


def _esc(value) -> str:
    """HTML-escape a value, treating None/NaN as an empty string."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return html.escape(str(value))


def _read_summary_workbook(summary_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the Summary and Flag_Breakdown sheets from the Findings Summary workbook."""
    summary_df = pd.read_excel(summary_path, sheet_name="Summary")
    breakdown_df = pd.read_excel(summary_path, sheet_name="Flag_Breakdown")
    return summary_df, breakdown_df


def _records_checked_map(summary_df: pd.DataFrame) -> dict[str, int]:
    return dict(zip(summary_df["Pain_Point"], summary_df["Records_Checked"]))


# ---------------------------------------------------------------------------
# Section builders — each returns an HTML string.
# ---------------------------------------------------------------------------

def _build_cover_section(generated_at: datetime) -> str:
    date_str = generated_at.strftime("%d %B %Y")
    rows = ""
    for role in ("Prepared by", "Reviewed by", "Approved by"):
        rows += f"""
        <tr>
            <td class="label-cell">{role}</td>
            <td class="blank-cell">&nbsp;</td>
            <td class="blank-cell">&nbsp;</td>
            <td class="blank-cell">&nbsp;</td>
        </tr>"""

    return f"""
    <div class="cover-page">
        <table class="title-block">
            <tr><td class="title-block-inner">
                <div class="doc-title">{_esc(REPORT_TITLE)}</div>
                <div class="doc-subtitle">Automated Data-Quality Assessment Report</div>
            </td></tr>
        </table>

        <table class="meta-table">
            <tr><td class="meta-label">Document Number</td><td class="meta-value">{_esc(DOCUMENT_NUMBER)}</td></tr>
            <tr><td class="meta-label">Document Status</td><td class="meta-value"><span class="status-pill">For Review</span></td></tr>
            <tr><td class="meta-label">Report Generated On</td><td class="meta-value">{date_str}</td></tr>
            <tr><td class="meta-label">Facility</td><td class="meta-value">Bokor</td></tr>
            <tr><td class="meta-label">Agent</td><td class="meta-value">Agent C &mdash; Task List / Maintenance Plan Validation</td></tr>
        </table>

        <div class="section-heading">Document Authorization</div>
        <table class="data-table authorization-table">
            <tr>
                <th>Role</th>
                <th>Name</th>
                <th>Signature</th>
                <th>Date</th>
            </tr>
            {rows}
        </table>
        <p class="note-text">Name, signature, and date fields above are intentionally left blank for
        completion by the responsible reviewers. No approval has occurred at the time of this
        report's generation.</p>

        <div class="section-heading">Distribution</div>
        <p>This document is intended for distribution to the Bokor Plant Maintenance data quality
        review stakeholders and {_esc(CLIENT_REVIEW_TEAM_PLACEHOLDER)}.</p>
    </div>
    """


def _build_classification_section(generated_at: datetime) -> str:
    date_str = generated_at.strftime("%d %B %Y")
    return f"""
    <div class="section-break">
        <h2>Document Classification</h2>

        <h3>Security Classification</h3>
        <table class="data-table">
            <tr><th>Classification</th><th>Applicable</th></tr>
            <tr><td>Public</td><td class="center">No</td></tr>
            <tr><td class="highlighted-row">Internal Use</td><td class="center highlighted-row">Yes</td></tr>
            <tr><td>Confidential</td><td class="center">No</td></tr>
            <tr><td>Restricted</td><td class="center">No</td></tr>
        </table>

        <h3>Document Structure</h3>
        <table class="data-table">
            <tr><th>Level</th><th>Description</th><th>Applicable</th></tr>
            <tr><td>Level 1</td><td>Policy</td><td class="center">No</td></tr>
            <tr><td>Level 2</td><td>Process</td><td class="center">No</td></tr>
            <tr><td>Level 3</td><td>Procedure</td><td class="center">No</td></tr>
            <tr><td class="highlighted-row">Level 4</td><td class="highlighted-row">Data</td><td class="center highlighted-row">Yes</td></tr>
        </table>

        <h3>Revision History</h3>
        <table class="data-table">
            <tr><th>Version</th><th>Date</th><th>Description</th><th>Revised By</th></tr>
            <tr>
                <td class="center">0</td>
                <td class="center">{date_str}</td>
                <td>Initial automated report generation</td>
                <td class="blank-cell">&nbsp;</td>
            </tr>
        </table>
    </div>
    """


def _build_risk_assessment_section() -> str:
    rows = ""
    for q in RISK_ASSESSMENT_QUESTIONS:
        rows += f"""
        <tr>
            <td>{_esc(q)}</td>
            <td class="center">No</td>
            <td class="blank-cell">&nbsp;</td>
        </tr>"""
    return f"""
    <div class="section-break">
        <h2>Document Risk Assessment</h2>
        <p class="note-text">The checklist below is a hand-editable template. All answers default to
        "No" and have not been independently assessed &mdash; the responsible reviewer should confirm
        or correct each answer before this report is finalized.</p>
        <table class="data-table">
            <tr><th>Assessment Question</th><th>Answer</th><th>Remarks</th></tr>
            {rows}
        </table>
    </div>
    """


def _build_glossary_section() -> str:
    rows = ""
    for term, full_name, definition in GLOSSARY_TERMS:
        label = f"{term} &mdash; {_esc(full_name)}" if full_name else _esc(term)
        rows += f"""
        <tr>
            <td class="glossary-term">{label}</td>
            <td>{_esc(definition)}</td>
        </tr>"""
    return f"""
    <div class="section-break">
        <h2>Terms and Definitions</h2>
        <table class="data-table glossary-table">
            <tr><th style="width: 32%;">Term</th><th>Definition</th></tr>
            {rows}
        </table>
    </div>
    """


def _build_introduction_section() -> str:
    return f"""
    <div class="section-break">
        <h2>Introduction</h2>
        <p>Agent C is an automated data-quality validation agent for SAP Plant Maintenance (PM)
        Task List and Maintenance Plan master data at the Bokor facility. It reasons over a live
        Knowledge Graph (KG) built from SAP PM extracts and supporting evidence sources (historical
        Job Management System records, OREDA reliability benchmarks, and PITSTOPS task-list content)
        to validate seven distinct pain-point categories spanning task list naming, work centre
        assignment, orphaned task lists, duplicate task lists, planned manhours, maintenance
        strategy/frequency, and hanging maintenance items. This report summarizes the current
        results of that automated assessment.</p>
    </div>
    """


def _build_objectives_section() -> str:
    return f"""
    <div class="section-break">
        <h2>Objectives</h2>
        <p>The objective of this assessment is to surface data-quality issues in Bokor's SAP PM
        Task List and Maintenance Plan records across all seven defined pain-point categories, to
        quantify the scale of each issue against the full record population checked, and to provide
        the relevant planning and maintenance teams with a clear, evidence-backed basis for
        corrective action &mdash; without requiring manual review of the full underlying dataset.</p>
    </div>
    """


def _build_scope_section(generated_at: datetime, records_checked: dict[str, int]) -> str:
    timestamp_str = generated_at.strftime("%d %B %Y, %H:%M:%S")
    rows = ""
    for pp in PAIN_POINTS:
        name = PAIN_POINT_NAMES.get(pp, pp)
        count = records_checked.get(pp, 0)
        rows += f"""
        <tr>
            <td class="center">{pp}</td>
            <td>{_esc(name)}</td>
            <td class="center">{count:,}</td>
        </tr>"""
    return f"""
    <div class="section-break">
        <h2>Scope</h2>
        <p><strong>Report generated on {timestamp_str}.</strong> This timestamp reflects when this
        PDF report was produced from the existing Findings Summary workbook; it is not necessarily
        the Knowledge Graph's own data-extraction or "as-of" date, since no such date is currently
        tracked in the pipeline output.</p>
        <p>The table below shows the real, current number of records checked for each pain point,
        as recorded in the Findings Summary workbook at report-generation time.</p>
        <table class="data-table">
            <tr><th>Pain Point</th><th>Name</th><th>Records Checked</th></tr>
            {rows}
        </table>
    </div>
    """


def _percent(count: int, total: int) -> str:
    if not total:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def _build_result_subsection(
    pp: str, records_checked: int, breakdown_rows: pd.DataFrame,
) -> str:
    name = PAIN_POINT_NAMES.get(pp, pp)
    rows = breakdown_rows[breakdown_rows["Pain_Point"] == pp].copy()

    # "(no finding)" is a real Flag_Breakdown value meaning the record was checked and no issue
    # was flagged for that column — treat it distinctly from genuine finding/status values.
    no_finding_mask = rows["Value"].astype(str).str.strip().str.lower() == "(no finding)"
    flagged_rows = rows[~no_finding_mask]
    no_finding_count = int(rows.loc[no_finding_mask, "Count"].sum()) if no_finding_mask.any() else 0
    flagged_total = int(flagged_rows["Count"].sum()) if not flagged_rows.empty else 0

    if rows.empty:
        narrative = (
            f"<p>Based on the assessment of {records_checked:,} records for {_esc(name)}, "
            f"no findings of this type were identified in the current assessment.</p>"
        )
        table_html = ""
    elif flagged_rows.empty:
        # Only "(no finding)" rows present — every checked record passed cleanly.
        narrative = (
            f"<p>Based on the assessment of {records_checked:,} records for {_esc(name)}, "
            f"{no_finding_count:,} ({_percent(no_finding_count, records_checked)}) were found to have "
            f"no issue of this type. No findings of this type were identified in the current "
            f"assessment.</p>"
        )
        table_html = ""
    else:
        flagged_rows = flagged_rows.sort_values("Count", ascending=False)
        top_value = flagged_rows.iloc[0]["Value"]
        top_count = int(flagged_rows.iloc[0]["Count"])
        clean_count = no_finding_count
        narrative = (
            f"<p>Based on the assessment of {records_checked:,} records for {_esc(name)}, "
            f"{clean_count:,} ({_percent(clean_count, records_checked)}) were found to have no issue "
            f"of this type, while {flagged_total:,} ({_percent(flagged_total, records_checked)}) were "
            f"flagged, most commonly as <strong>{_esc(top_value)}</strong> "
            f"({top_count:,} records, {_percent(top_count, records_checked)}).</p>"
        )
        table_rows = ""
        display_rows = pd.concat([flagged_rows, rows[no_finding_mask]]) if no_finding_mask.any() else flagged_rows
        for _, r in display_rows.iterrows():
            count = int(r["Count"])
            table_rows += f"""
            <tr>
                <td>{_esc(r['Value'])}</td>
                <td class="center">{count:,}</td>
                <td class="center">{_percent(count, records_checked)}</td>
            </tr>"""
        table_html = f"""
        <table class="data-table">
            <tr><th>Value</th><th>Count</th><th>% of Records Checked</th></tr>
            {table_rows}
        </table>"""

    return f"""
    <div class="result-subsection">
        <h3>{pp} &mdash; {_esc(name)}</h3>
        {narrative}
        {table_html}
    </div>
    """


def _build_result_section(records_checked: dict[str, int], breakdown_df: pd.DataFrame) -> str:
    subsections = "".join(
        _build_result_subsection(pp, records_checked.get(pp, 0), breakdown_df) for pp in PAIN_POINTS
    )
    return f"""
    <div class="section-break">
        <h2>Result</h2>
        {subsections}
    </div>
    """


def _build_conclusion_section(records_checked: dict[str, int], breakdown_df: pd.DataFrame) -> str:
    items = ""
    for pp in PAIN_POINTS:
        name = PAIN_POINT_NAMES.get(pp, pp)
        rows = breakdown_df[breakdown_df["Pain_Point"] == pp].copy()
        no_finding_mask = rows["Value"].astype(str).str.strip().str.lower() == "(no finding)"
        flagged_rows = rows[~no_finding_mask]

        if flagged_rows.empty:
            items += (
                f"<li>No findings of this type were identified for {pp} ({_esc(name)}) in the "
                f"current assessment &mdash; no action required at this time.</li>"
            )
            continue

        flagged_rows = flagged_rows.sort_values("Count", ascending=False)
        top_value = flagged_rows.iloc[0]["Value"]
        top_count = int(flagged_rows.iloc[0]["Count"])
        items += (
            f"<li>{top_count:,} records flagged <strong>{_esc(top_value)}</strong> under {pp} "
            f"({_esc(name)}) &mdash; recommended for review by {_esc(CLIENT_REVIEW_TEAM_PLACEHOLDER)}.</li>"
        )

    return f"""
    <div class="section-break">
        <h2>Conclusion &amp; Way Forward</h2>
        <ol class="conclusion-list">
            {items}
        </ol>
    </div>
    """


def _build_appendices_section() -> str:
    rows = ""
    for filename, description in COMPANION_WORKBOOKS:
        rows += f"""
        <tr>
            <td>{_esc(filename)}</td>
            <td>{_esc(description)}</td>
        </tr>"""
    return f"""
    <div class="section-break">
        <h2>Appendices</h2>
        <p>The full, row-level detail supporting every finding summarized in this report is
        available in the following companion workbooks, located in the pipeline's <code>output/</code>
        directory:</p>
        <table class="data-table">
            <tr><th>Workbook</th><th>Contents</th></tr>
            {rows}
        </table>
    </div>
    """


_CSS = f"""
@page {{
    size: A4;
    margin: 2.2cm 1.6cm 2.4cm 1.6cm;
    @frame footer_frame {{
        -pdf-frame-content: footer_content;
        bottom: 1cm;
        margin-left: 1.6cm;
        margin-right: 1.6cm;
        height: 1cm;
    }}
}}

body {{
    font-family: Helvetica, Arial, sans-serif;
    font-size: 10pt;
    color: #1A1A1A;
    line-height: 1.45;
}}

h1, h2, h3 {{
    color: {ACCENT_DARK};
    font-family: Helvetica, Arial, sans-serif;
}}

h2 {{
    font-size: 15pt;
    border-bottom: 2px solid {ACCENT_DARK};
    padding-bottom: 4px;
    margin-top: 0;
}}

h3 {{
    font-size: 12pt;
    color: {ACCENT_MID};
    margin-bottom: 4px;
}}

.section-break {{
    page-break-before: always;
}}

.cover-page {{
    text-align: left;
}}

.title-block {{
    width: 100%;
    border: 2px solid {ACCENT_DARK};
    margin-bottom: 18px;
}}

.title-block-inner {{
    background-color: {ACCENT_DARK};
    color: #FFFFFF;
    padding: 22px;
    text-align: center;
}}

.doc-title {{
    font-size: 18pt;
    font-weight: bold;
    color: #FFFFFF;
}}

.doc-subtitle {{
    font-size: 11pt;
    color: {ACCENT_LIGHT};
    margin-top: 6px;
}}

.meta-table {{
    width: 100%;
    margin-bottom: 20px;
    border: 1px solid {BORDER_COLOR};
}}

.meta-table td {{
    padding: 6px 10px;
    border: 1px solid {BORDER_COLOR};
}}

.meta-label {{
    font-weight: bold;
    width: 35%;
    background-color: {ACCENT_LIGHT};
    color: {ACCENT_DARK};
}}

.status-pill {{
    font-weight: bold;
    color: {ACCENT_DARK};
}}

.section-heading {{
    font-size: 13pt;
    font-weight: bold;
    color: {ACCENT_DARK};
    margin-top: 16px;
    margin-bottom: 6px;
    border-bottom: 1px solid {BORDER_COLOR};
}}

.note-text {{
    font-style: italic;
    color: #444444;
    font-size: 9pt;
}}

table.data-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 14px;
}}

table.data-table th {{
    background-color: {ACCENT_DARK};
    color: #FFFFFF;
    padding: 6px 8px;
    text-align: left;
    border: 1px solid {ACCENT_DARK};
    font-size: 9.5pt;
}}

table.data-table td {{
    padding: 5px 8px;
    border: 1px solid {BORDER_COLOR};
    font-size: 9.5pt;
    vertical-align: top;
}}

table.data-table tr:nth-child(even) td {{
    background-color: #F3F6FB;
}}

.highlighted-row {{
    background-color: {ACCENT_LIGHT} !important;
    font-weight: bold;
}}

.center {{
    text-align: center;
}}

.blank-cell {{
    background-color: #FAFAFA;
}}

.label-cell {{
    font-weight: bold;
    background-color: {ACCENT_LIGHT};
    color: {ACCENT_DARK};
}}

.glossary-term {{
    font-weight: bold;
    color: {ACCENT_DARK};
}}

.result-subsection {{
    margin-top: 10px;
    margin-bottom: 18px;
}}

.conclusion-list li {{
    margin-bottom: 8px;
}}

#footer_content {{
    font-size: 8pt;
    color: #666666;
    text-align: center;
    border-top: 1px solid {BORDER_COLOR};
    padding-top: 4px;
}}
"""


def _build_footer_frame() -> str:
    return f"""
    <div id="footer_content">
        {_esc(REPORT_TITLE)} &nbsp;|&nbsp; Document {_esc(DOCUMENT_NUMBER)} &nbsp;|&nbsp;
        Page <pdf:pagenumber/> of <pdf:pagecount/>
    </div>
    """


def build_report_html(summary_df: pd.DataFrame, breakdown_df: pd.DataFrame, generated_at: datetime) -> str:
    """Assemble the full report HTML from the Summary and Flag_Breakdown dataframes."""
    records_checked = _records_checked_map(summary_df)

    body_sections = "".join([
        _build_cover_section(generated_at),
        _build_classification_section(generated_at),
        _build_risk_assessment_section(),
        _build_glossary_section(),
        _build_introduction_section(),
        _build_objectives_section(),
        _build_scope_section(generated_at, records_checked),
        _build_result_section(records_checked, breakdown_df),
        _build_conclusion_section(records_checked, breakdown_df),
        _build_appendices_section(),
    ])

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>{_esc(REPORT_TITLE)}</title>
<style>{_CSS}</style>
</head>
<body>
{_build_footer_frame()}
{body_sections}
</body>
</html>
"""


def generate_pdf_report(summary_path: str, output_path: str) -> None:
    """Generate the Agent C PDF validation report from an existing Findings Summary workbook.

    Args:
        summary_path: Path to the already-written SAP_PM_Agent_Findings_Summary.xlsx workbook
            (must contain 'Summary' and 'Flag_Breakdown' sheets).
        output_path: Path where the generated PDF should be written. Parent directories are
            created if they do not already exist.

    Raises:
        FileNotFoundError: if summary_path does not exist.
        RuntimeError: if PDF generation fails (xhtml2pdf reports an error).
    """
    from xhtml2pdf import pisa

    summary_path_obj = Path(summary_path)
    if not summary_path_obj.exists():
        raise FileNotFoundError(
            f"Findings Summary workbook not found at {summary_path!r} — run the pipeline first "
            "so output_writer.write_findings_summary_workbook() produces it."
        )

    summary_df, breakdown_df = _read_summary_workbook(str(summary_path_obj))
    generated_at = datetime.now()
    html_content = build_report_html(summary_df, breakdown_df, generated_at)

    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path_obj, "wb") as pdf_file:
        result = pisa.CreatePDF(src=html_content, dest=pdf_file, encoding="utf-8")

    if result.err:
        raise RuntimeError(f"xhtml2pdf reported {result.err} error(s) while generating {output_path!r}")


if __name__ == "__main__":
    import sys

    base_dir = Path(__file__).resolve().parent
    default_summary = base_dir / "output" / "SAP_PM_Agent_Findings_Summary.xlsx"
    default_output = base_dir / "output" / "Agent_C_Validation_Report_Bokor.pdf"

    summary_arg = sys.argv[1] if len(sys.argv) > 1 else str(default_summary)
    output_arg = sys.argv[2] if len(sys.argv) > 2 else str(default_output)

    generate_pdf_report(summary_arg, output_arg)
    print(f"Agent C PDF report generated: {output_arg}")
