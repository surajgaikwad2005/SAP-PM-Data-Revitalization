"""
SSPS vs GOPS4.0 - SCE status of each Bokor SSPS group against the latest GOPS
-----------------------------------------------------------------------------
Agreed with PCSB (call, 9 Oct 2026): GOPS4.0 (Revision 4, March 2026) is the
latest standard; the Bokor Site-Specific Performance Standards (SSPS, 2022)
were prepared under GOPS3. Where GOPS4.0 keeps an SCE Group, the SSPS is in
line. Where GOPS4.0 no longer has the group, but the Bokor SSPS still sets
assurance tasks for it as an SCE, the SSPS contradicts the latest GOPS and
the client is told which SSPS document it comes from.

GOPS4.0 basis:
  - p.10: "The GOPS consists of 45 SCE groups (Refer to Figure 1-1)".
  - p.12, Figure 1-1: the 45 SCE Groups by barrier.
  - p.4, amendment sheet, Revision 4.0 (13/3/26): tasks and barriers revised
    for all SCE groups.
  - p.11, section 1.4: SSPS may vary GOPS tasks and frequency with
    endorsement, so task-level differences are not reported here as
    contradictions; only the SCE status of the group is.

Output: Data exploration/output/D9_SSPS_vs_GOPS4.xlsx
  - Summary
  - SSPS_Group_Status       (one row per Bokor SSPS group, with its GOPS4.0
                             status and what uses the group at Bokor)
  - Contradicting_SSPS_Tasks (the applicable assurance tasks of the SSPS
                             groups not in GOPS4.0, with document and page)
  - GOPS4_Groups_No_SSPS    (GOPS4.0 groups with no Bokor SSPS document)

Run:
    python "code/agent/check9_ssps_vs_gops4.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Data exploration" / "output"
SSPS_FILE = OUT / "ssps_requirements.xlsx"
GOPS4_FILE = OUT / "gops4_sce_groups.xlsx"
REGISTER_DB = OUT / "sce_register.db"
SAP_FL_FILE = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master" / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx"
MIC_REPORT_FILE = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Transactional Data" / "MIC" / "MIC Report 2024_2025.xlsx"
SSPS_DIR = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master" / "BOKOR SCE REPORT" / "SSPS"
OUT_XLSX = OUT / "D9_SSPS_vs_GOPS4.xlsx"

GOPS4_REF = "GOPS4.pdf (Revision 4, March 2026), page 10 (45 SCE groups) and page 12, Figure 1-1"
# the DS002 SSPS file name was truncated on disk; cite it by what its own page 1 says
DS002_SOURCE = ("Bokor SSPS DS002, Telecommunication, November 2022 (SSPS TELECOM folder, file SKA_BO~1.PDF)")


def code_of(s):
    return s.astype(str).str.extract(r"^\s*([A-Z]{2}\d{3})", expand=False)


def norm_fl(s):
    return s.astype(str).str.replace(r"\s+", "", regex=True).str.upper()


def ssps_listed_on_sign_off_pages():
    """SCE Groups listed as attachments on the Bokor SSPS sign-off pages: {code: 'sign-off file, page n'}."""
    import pymupdf
    listed = {}
    for f in sorted(SSPS_DIR.glob("*/*.pdf")) + sorted(SSPS_DIR.glob("*/*.PDF")):
        doc = pymupdf.open(f)
        if "SITE SPECIFIC PERFORMANCE STANDARD" not in doc[0].get_text().upper():
            continue  # not a sign-off document
        for i, page in enumerate(doc):
            for code in re.findall(r"Performance Standard\s+([A-Z]{2}\d{3})", page.get_text()):
                listed.setdefault(code, f"{f.parent.name}/{f.name}, page {i + 1}")
    return listed


def main():
    groups = pd.read_excel(SSPS_FILE, sheet_name="SSPS_Groups")
    tasks = pd.read_excel(SSPS_FILE, sheet_name="Functionality_Tasks")
    gops4 = pd.read_excel(GOPS4_FILE)
    current = set(gops4["sce_group"])

    tasks["document"] = tasks["source"].str.replace(r"\s*\(page \d+\)$", "", regex=True)
    tasks["page"] = tasks["source"].str.extract(r"\(page (\d+)\)$", expand=False).astype(float)
    tasks["applicable"] = ~tasks["applicable_or_not"].fillna("").astype(str).str.upper().str.replace(" ", "").isin(
        ["N", "N/A", "NA"])
    per_group = tasks.groupby("sce_group").agg(
        ssps_tasks=("assurance_task", "size"), applicable_tasks=("applicable", "sum"),
        pages=("page", lambda p: ", ".join(str(int(x)) for x in sorted(p.dropna().unique()))))

    # what uses each group at Bokor today
    reg = pd.read_sql("select functional_location, attachment_title, sce_group from sce_register", sqlite3.connect(REGISTER_DB))
    reg = reg[reg["attachment_title"].str.startswith("SCE FUNCTIONAL", na=False)]
    reg["code"] = code_of(reg["sce_group"])
    reg_fls = reg.assign(fl=norm_fl(reg["functional_location"])).groupby("code")["fl"].nunique()
    fl = pd.read_excel(SAP_FL_FILE, dtype=str)
    sap_primary = code_of(fl["SCE GROUP"]).value_counts()
    sap_secondary = code_of(fl["SECONDARY SCE GROUP"]).value_counts()
    mic = pd.read_excel(MIC_REPORT_FILE, dtype=str)
    mic["code"] = code_of(mic["SCE Grp - MIC"])
    mic_records = mic["code"].value_counts()
    mic_codes = mic.groupby("code")["MIC"].nunique()

    rows = []
    for g in groups.itertuples():
        in_gops4 = g.sce_group in current
        doc = DS002_SOURCE if g.sce_group == "DS002" else f"{g.folder}/{g.source_file}"
        rows.append({
            "SCE Group": g.sce_group,
            "SSPS group name": g.sce_group_name,
            "Status in GOPS4.0": "Maintained as SCE in GOPS4.0" if in_gops4 else "Not in GOPS4.0",
            "Finding": "SSPS in line with GOPS4.0" if in_gops4 else
                       "SSPS contradicts GOPS4.0: the Bokor SSPS still sets assurance tasks for this group as an SCE, "
                       "but the group is not among the 45 SCE Groups of the latest GOPS4.0",
            "SSPS document": doc,
            "SSPS pages": per_group["pages"].get(g.sce_group, ""),
            "SSPS assurance tasks": int(per_group["ssps_tasks"].get(g.sce_group, 0)),
            "  of which applicable at Bokor": int(per_group["applicable_tasks"].get(g.sce_group, 0)),
            "Register SCE FLs with this group": int(reg_fls.get(g.sce_group, 0)),
            "SAP FLs with this SCE GROUP": int(sap_primary.get(g.sce_group, 0)),
            "SAP FLs with this SECONDARY SCE GROUP": int(sap_secondary.get(g.sce_group, 0)),
            "MIC records 2024-2025 of this group": int(mic_records.get(g.sce_group, 0)),
            "Distinct MICs of this group": int(mic_codes.get(g.sce_group, 0)),
            "GOPS4.0 reference": GOPS4_REF,
        })
    status = pd.DataFrame(rows).sort_values(["Status in GOPS4.0", "SCE Group"], ascending=[False, True])
    contra = status[status["Status in GOPS4.0"] == "Not in GOPS4.0"]

    ct = tasks[tasks["sce_group"].isin(contra["SCE Group"]) & tasks["applicable"]].copy()
    ct["SSPS document"] = ct["sce_group"].map(dict(zip(status["SCE Group"], status["SSPS document"])))
    ct = ct.rename(columns={"sce_group": "SCE Group", "assurance_task": "SSPS assurance task",
                            "frequency": "SSPS frequency", "min_acceptable_criteria": "Minimum acceptable criteria"})
    ct["SSPS page"] = ct["page"].astype("Int64")
    ct = ct[["SCE Group", "SSPS document", "SSPS page", "SSPS assurance task", "Minimum acceptable criteria",
             "SSPS frequency"]].assign(Finding="Assurance task set for an SCE Group that GOPS4.0 no longer has")

    missing = sorted(current - set(groups["sce_group"]))
    no_ssps = pd.DataFrame({
        "SCE Group": missing,
        "GOPS4.0 group name": [gops4.set_index("sce_group")["sce_group_name"].get(c) for c in missing],
        "Register SCE FLs with this group": [int(reg_fls.get(c, 0)) for c in missing],
        "SAP FLs with this SCE GROUP": [int(sap_primary.get(c, 0)) for c in missing],
        "MIC records 2024-2025 of this group": [int(mic_records.get(c, 0)) for c in missing],
    })
    listed = ssps_listed_on_sign_off_pages()
    no_ssps["Listed on an SSPS sign-off page"] = no_ssps["SCE Group"].map(lambda c: listed.get(c, ""))

    def no_ssps_finding(r):
        if r["Listed on an SSPS sign-off page"]:
            return "Bokor SSPS exists (listed on the sign-off page) but the document was not supplied - PCSB to provide"
        if r["Register SCE FLs with this group"]:
            return "SCE FLs at Bokor but no Bokor SSPS - assurance tasks would come from GOPS4.0 only"
        return "No SCE FL at Bokor - no SSPS needed"

    no_ssps["Finding"] = no_ssps.apply(no_ssps_finding, axis=1)

    summary = pd.DataFrame({
        "Metric": [
            "Bokor SSPS groups (documents)",
            "  - maintained as SCE in GOPS4.0 (SSPS in line)",
            "  - not in GOPS4.0 (SSPS contradicts the latest GOPS)",
            "Applicable SSPS assurance tasks in the contradicting documents",
            "Register SCE FLs in the contradicting groups",
            "SAP FLs with a contradicting group as SCE GROUP",
            "SAP FLs with a contradicting group as SECONDARY SCE GROUP",
            "MIC records 2024-2025 in the contradicting groups",
            "GOPS4.0 SCE Groups (current)",
            "  - with no Bokor SSPS document",
            "    of which with SCE FLs in the register",
        ],
        "Value": [
            len(status), int((status["Status in GOPS4.0"] != "Not in GOPS4.0").sum()), len(contra), len(ct),
            int(contra["Register SCE FLs with this group"].sum()), int(contra["SAP FLs with this SCE GROUP"].sum()),
            int(contra["SAP FLs with this SECONDARY SCE GROUP"].sum()),
            int(contra["MIC records 2024-2025 of this group"].sum()), len(current), len(no_ssps),
            int((no_ssps["Register SCE FLs with this group"] > 0).sum()),
        ],
    })
    print(summary.to_string(index=False))
    print(contra[["SCE Group", "SSPS group name", "  of which applicable at Bokor", "Register SCE FLs with this group",
                  "SAP FLs with this SCE GROUP", "MIC records 2024-2025 of this group"]].to_string(index=False))
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        status.to_excel(xl, sheet_name="SSPS_Group_Status", index=False)
        ct.to_excel(xl, sheet_name="Contradicting_SSPS_Tasks", index=False)
        no_ssps.to_excel(xl, sheet_name="GOPS4_Groups_No_SSPS", index=False)
    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
