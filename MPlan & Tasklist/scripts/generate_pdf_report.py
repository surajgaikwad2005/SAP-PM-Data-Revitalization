"""
Standalone PDF report generator for Agent C's pain-point findings.

STANDALONE, NOT PART OF THE PIPELINE: this script is never imported or
called by app.py / validation.py / output_writer.py, and does not modify
any of them. It only READS the two existing output workbooks
(SAP_PM_Agent_Findings_Summary.xlsx) already produced by a normal
pipeline run, and writes a new PDF into output/ — it never re-runs any
pain-point logic itself.

Usage: python scripts/generate_pdf_report.py
Output: output/Agent_C_Findings_Report_<YYYYMMDD_HHMMSS>.pdf
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = BASE_DIR / "output" / "SAP_PM_Agent_Findings_Summary.xlsx"

PAIN_POINT_ORDER = ["PP1", "PP2", "PP3", "PP4", "PP5", "PP6", "PP7"]

PAIN_POINT_DESCRIPTIONS = {
    "PP1": "Validates whether each Task List Group's name reflects the platform and Equipment Class of its currently linked equipment.",
    "PP2": "Classifies the required maintenance discipline for each operation and maps it to the approved Bokor Work Centre.",
    "PP3": "Flags Task Lists with real operations but no current, non-stub Maintenance Item using them.",
    "PP4": "Flags candidate Task List pairs whose operation scope substantially overlaps or duplicates, for review only.",
    "PP5": "Validates recorded man-hours (WORK) against the PERSON x DURATION formula and comparable historical/JMS execution evidence.",
    "PP6": "Validates Maintenance Strategy and Frequency consistency between a Task List and its linked Maintenance Items/Equipment.",
    "PP7": "Flags Maintenance Items with no Maintenance Plan assigned (a 'hanging' item).",
}


def load_summary() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not SUMMARY_PATH.exists():
        print(f"ERROR: {SUMMARY_PATH} not found. Run the pipeline first.", file=sys.stderr)
        sys.exit(1)
    xls = pd.ExcelFile(SUMMARY_PATH)
    summary = pd.read_excel(xls, sheet_name="Summary")
    breakdown = pd.read_excel(xls, sheet_name="Flag_Breakdown") if "Flag_Breakdown" in xls.sheet_names else pd.DataFrame()
    return summary, breakdown


def pct(count, total) -> str:
    if not total:
        return "0%"
    return f"{count / total * 100:.0f}%"


def build_pp_table_rows(pain_point: str, summary: pd.DataFrame, breakdown: pd.DataFrame) -> list[list[str]]:
    row = summary[summary["Pain_Point"] == pain_point]
    if row.empty:
        return [["No data available for this pain point in the current run.", "", ""]]
    checked = int(row["Records_Checked"].iloc[0])

    rows = [["Metric", "Count", "%"]]
    rows.append(["Total records assessed", f"{checked:,}", "100%"])

    pp_breakdown = breakdown[breakdown["Pain_Point"] == pain_point] if not breakdown.empty else pd.DataFrame()
    if not pp_breakdown.empty:
        for _, r in pp_breakdown.sort_values("Count", ascending=False).iterrows():
            label = str(r["Value"])
            count = int(r["Count"])
            rows.append([label, f"{count:,}", pct(count, checked)])
    else:
        findings = int(row["Findings"].iloc[0])
        rows.append(["Findings", f"{findings:,}", pct(findings, checked)])

    return rows


def build_pp_narrative(pain_point: str, summary: pd.DataFrame, breakdown: pd.DataFrame) -> str:
    row = summary[summary["Pain_Point"] == pain_point]
    if row.empty:
        return "No data was available for this pain point in the current run."
    checked = int(row["Records_Checked"].iloc[0])
    pp_breakdown = breakdown[breakdown["Pain_Point"] == pain_point] if not breakdown.empty else pd.DataFrame()

    if pp_breakdown.empty:
        findings = int(row["Findings"].iloc[0])
        return (
            f"Based on the assessment of {checked:,} records, {findings:,} finding(s) "
            f"({pct(findings, checked)}) were identified."
        )

    top = pp_breakdown.sort_values("Count", ascending=False)
    parts = []
    for _, r in top.iterrows():
        parts.append(f"{int(r['Count']):,} ({pct(int(r['Count']), checked)}) {r['Value']}")
    joined = "; ".join(parts[:4])
    return f"Based on the assessment of {checked:,} records: {joined}."


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=20, leading=24, spaceAfter=6, textColor=colors.HexColor("#1F3A5F")))
    styles.add(ParagraphStyle(name="ReportSubtitle", fontSize=11, leading=14, textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=14, leading=18, spaceBefore=18, spaceAfter=6, textColor=colors.HexColor("#1F3A5F")))
    styles.add(ParagraphStyle(name="SubHeading", fontSize=12, leading=15, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#2E5C4E")))
    styles.add(ParagraphStyle(name="BodyTextTight", fontSize=10, leading=14, spaceAfter=8))
    return styles


def table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F3F3")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def generate_report(output_path: Path) -> None:
    summary, breakdown = load_summary()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    now_str = datetime.now().strftime("%d %B %Y %H:%M")
    total_checked = {pp: int(summary.loc[summary["Pain_Point"] == pp, "Records_Checked"].iloc[0])
                      if not summary[summary["Pain_Point"] == pp].empty else 0
                      for pp in PAIN_POINT_ORDER}

    story.append(Paragraph("Task List &amp; Maintenance Plan Validation Report", styles["ReportTitle"]))
    story.append(Paragraph("Agent C &middot; SAP PM Data Revitalization &middot; Bokor", styles["ReportSubtitle"]))
    story.append(Paragraph(f"Generated: {now_str}", styles["ReportSubtitle"]))
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph("1.0 Introduction", styles["SectionHeading"]))
    story.append(Paragraph(
        "The SAP Plant Maintenance (PM) Data Revitalization Project is a large-scale SAP PM/Enterprise Asset "
        "Management (EAM) data cleanup and remediation programme for asset-intensive, upstream operations. "
        "Agent C supports this programme by applying automated, Knowledge-Graph-based validation to Task List "
        "and Maintenance Plan master data, covering seven distinct data-quality checks (PP1-PP7) across naming "
        "conventions, Work Centre assignment, Task List redundancy, man-hour planning, maintenance strategy, "
        "and plan completeness.",
        styles["BodyTextTight"],
    ))

    story.append(Paragraph("1.1 Objectives", styles["SubHeading"]))
    story.append(Paragraph(
        "The objective of this report is to record the outcome of the automated Task List and Maintenance "
        "Plan data quality assessment for Bokor, covering PP1 through PP7, ensuring that naming, Work Centre, "
        "duplication, man-hour, strategy, and Maintenance Plan data are kept complete and correct.",
        styles["BodyTextTight"],
    ))

    story.append(Paragraph("1.2 Scope", styles["SubHeading"]))
    story.append(Paragraph(
        f"This assessment covers {total_checked.get('PP1', 0):,} Task Lists, {total_checked.get('PP2', 0):,} "
        f"operations, and {total_checked.get('PP7', 0):,} Maintenance Items for Bokor, as reflected in the "
        f"Knowledge Graph at the time of this run. The assessment applies seven validation checks (PP1-PP7) "
        "described in Section 2.0.",
        styles["BodyTextTight"],
    ))

    story.append(PageBreak())
    story.append(Paragraph("2.0 Maintenance Master Data Quality Assessment", styles["SectionHeading"]))

    for pp in PAIN_POINT_ORDER:
        pp_name = PAIN_POINT_DESCRIPTIONS.get(pp, "")
        row = summary[summary["Pain_Point"] == pp]
        pp_label = row["Pain_Point_Name"].iloc[0] if not row.empty else pp

        story.append(Paragraph(f"2.{PAIN_POINT_ORDER.index(pp) + 1} {pp} &ndash; {pp_label}", styles["SubHeading"]))
        story.append(Paragraph(pp_name, styles["BodyTextTight"]))
        story.append(Paragraph(build_pp_narrative(pp, summary, breakdown), styles["BodyTextTight"]))

        rows = build_pp_table_rows(pp, summary, breakdown)
        t = Table(rows, colWidths=[90 * mm, 30 * mm, 20 * mm])
        t.setStyle(table_style())
        story.append(t)
        story.append(Spacer(1, 6 * mm))

    story.append(PageBreak())
    story.append(Paragraph("3.0 Conclusion &amp; Way Forward", styles["SectionHeading"]))

    conclusions = []
    pp1_row = summary[summary["Pain_Point"] == "PP1"]
    if not pp1_row.empty and int(pp1_row["Suggestions_Generated"].iloc[0]) > 0:
        conclusions.append(
            f"Agent C has identified {int(pp1_row['Suggestions_Generated'].iloc[0]):,} Task List Group(s) (PP1) "
            "with a confirmed naming discrepancy against currently linked equipment, for review and correction "
            "by the SKA PMMS Team."
        )
    pp4_row = summary[summary["Pain_Point"] == "PP4"]
    if not pp4_row.empty and int(pp4_row["Findings"].iloc[0]) > 0:
        conclusions.append(
            f"{int(pp4_row['Findings'].iloc[0]):,} Task List pair(s) (PP4) have been flagged for potential "
            "duplication or overlap and require review before any consolidation decision is made; Agent C "
            "does not recommend deletion or merging."
        )
    pp5_row = summary[summary["Pain_Point"] == "PP5"]
    if not pp5_row.empty and int(pp5_row["Cannot_Verify"].iloc[0]) > 0:
        conclusions.append(
            f"Man-hour validation (PP5) for {int(pp5_row['Cannot_Verify'].iloc[0]):,} operation(s) could not be "
            "completed due to insufficient comparable historical execution and JMS reference data; it is "
            "recommended that additional historical Work Order detail be made available to close this evidence "
            "gap in a future assessment cycle."
        )
    conclusions.append(
        "Agent C's full findings and suggested values for all seven pain points are provided in the "
        "accompanying Recommendations and Findings Summary workbooks (Appendix)."
    )

    for i, c in enumerate(conclusions, start=1):
        story.append(Paragraph(f"{i}. {c}", styles["BodyTextTight"]))

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Appendix: Supporting Data", styles["SectionHeading"]))
    story.append(Paragraph(
        "The detailed, record-level findings and suggested values for all seven pain points are provided in: "
        "SAP_PM_Agent_Recommendations.xlsx and SAP_PM_Agent_Findings_Summary.xlsx (output directory).",
        styles["BodyTextTight"],
    ))

    doc.build(story)


def main():
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"Agent_C_Findings_Report_{timestamp}.pdf"
    generate_report(output_path)
    print(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
