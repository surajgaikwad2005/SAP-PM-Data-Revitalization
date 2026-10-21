"""
Pain Point 8 - Inspection results outside their specification but accepted
--------------------------------------------------------------------------
Agreed with PCSB (call, 9 Oct 2026): until an extract with rejected lots is
available, flag the MIC records whose recorded result does not meet the
acceptance criterion in their own specification, yet were accepted.

MIC Report 2024_2025.xlsx columns used:
  AB Specification  - the acceptance criterion: "YES / NO", ">=  60 min",
                      "<=  45.00 s", ... or "NOT APPLICABLE"
  AC Result         - the recorded result
  AD ResVal         - result valuation: "A" (accepted); blank where the
                      specification is NOT APPLICABLE
  UD / UDVal        - the usage decision of the lot (A1 / A on every row)

Flags:
  1. Numeric result outside its specification, accepted (ResVal = A):
     ">= x" with result < x, or "<= x" with result > x.
  2. YES / NO specification with a result other than Y, accepted. The only
     other value in the extract is "0"; whether "0" means "No" (a failed
     check) or "not recorded" is for PCSB to confirm, so these are kept
     apart from flag 1.

For each flagged record, the notifications raised on the same Functional
Location on or after the result date are listed (notification history,
M014_WO_NN Listing_Jan2026_BOKOR.xlsx), as a first view of whether a
follow-up was raised. The follow-up rule itself (which notification types,
within what period) is still to be agreed with PCSB.

Output: Data exploration/output/D8b_MIC_Result_vs_Specification.xlsx
  - Summary
  - Out_Of_Spec_Accepted
  - YesNo_Result_Not_Y
  - Specification_Overview (each specification with its record count)

Run:
    python "code/agent/check8b_mic_result_vs_specification.py"
"""

import re
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
TRANS = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Transactional Data"
MIC_REPORT_FILE = TRANS / "MIC" / "MIC Report 2024_2025.xlsx"
WO_NN_FILE = TRANS / "M014_WO_NN Listing_Jan2026_BOKOR.xlsx"
OUT_XLSX = ROOT / "Data exploration" / "output" / "D8b_MIC_Result_vs_Specification.xlsx"

SPEC_RE = re.compile(r"^\s*([<>]=)\s*([\d.,]+)\s*(.*)$")
RECORD_COLS = ["Order", "Inspection Lot", "Functional Location", "SCE Grp - FL", "EQ at WO Hdr", "MIC", "MIC Name",
               "PS Req", "Specification", "Result", "ResVal", "UD", "UDVal", "Created on"]


def norm_fl(s):
    return s.astype(str).str.replace(r"\s+", "", regex=True).str.upper()


def follow_up_notifications(flagged, nn):
    """Notifications on the same FL dated on or after the result date: count and the first few, for review."""
    by_fl = {fl: g.sort_values("date") for fl, g in nn.groupby("fl")}
    counts, listing = [], []
    for fl, date in zip(norm_fl(flagged["Functional Location"]), pd.to_datetime(flagged["Created on"], errors="coerce")):
        g = by_fl.get(fl)
        g = g[g["date"] >= date] if g is not None and pd.notna(date) else None
        counts.append(0 if g is None else len(g))
        listing.append("" if g is None or g.empty else "; ".join(
            f"{r['Notification']} ({r['Notification type']}, {r['date']:%d %b %Y}): {r['Description']}"
            for _, r in g.head(3).iterrows()))
    flagged = flagged.copy()
    flagged["Notifications on the FL on/after the result date"] = counts
    flagged["First notifications (number, type, date, description)"] = listing
    return flagged


def main():
    mic = pd.read_excel(MIC_REPORT_FILE, dtype=str)
    mic.columns = [c.strip() for c in mic.columns]
    nn = pd.read_excel(WO_NN_FILE, sheet_name="Notification", dtype=str)
    nn = nn[nn["Location"].str.upper().eq("BOKOR")].copy()
    nn["fl"] = norm_fl(nn["Functional Location"])
    nn["date"] = pd.to_datetime(nn["Notification date"], errors="coerce")
    nn_end = nn["date"].max()

    spec = mic["Specification"].fillna("").str.strip()
    result = mic["Result"].fillna("").str.strip()
    is_na = spec.eq("NOT APPLICABLE")
    is_yn = spec.eq("YES / NO")
    parsed = spec.str.extract(SPEC_RE)
    is_num = parsed[0].notna()
    limit = pd.to_numeric(parsed[1].str.replace(",", ""), errors="coerce")
    value = pd.to_numeric(result.str.replace(",", ""), errors="coerce")
    accepted = mic["ResVal"].eq("A")
    unparsed = ~(is_na | is_yn | is_num)
    assert not unparsed.any(), f"unrecognised specifications: {spec[unparsed].unique()[:10]}"
    assert value[is_num].notna().all(), "numeric specification with a non-numeric result"

    out_of_spec = is_num & (((parsed[0] == ">=") & (value < limit)) | ((parsed[0] == "<=") & (value > limit)))
    yn_not_y = is_yn & result.ne("Y")

    oos = mic.loc[out_of_spec & accepted, RECORD_COLS].assign(
        Finding="Result outside the specification, accepted",
        **{"Specification limit": parsed.loc[out_of_spec & accepted, 0] + " " + parsed.loc[out_of_spec & accepted, 1]
           + " " + parsed.loc[out_of_spec & accepted, 2].str.strip()})
    yn = mic.loc[yn_not_y & accepted, RECORD_COLS].assign(
        Finding="YES / NO check with result other than Y, accepted - PCSB to confirm whether '0' means No")
    oos = follow_up_notifications(oos, nn)
    yn = follow_up_notifications(yn, nn)
    after_extract = lambda d: int((pd.to_datetime(d["Created on"], errors="coerce") > nn_end).sum())

    summary = pd.DataFrame({
        "Metric": [
            "MIC records in the MIC report (2024-2025)",
            "  - specification NOT APPLICABLE (ResVal blank)",
            "  - specification YES / NO",
            "  - specification with a numeric limit (>= / <=)",
            "Records accepted (ResVal = A)",
            "Lots with a rejected usage decision",
            "FLAG 1 - numeric result outside its specification, accepted",
            "  - inspection lots",
            "  - Functional Locations",
            "  - with a notification on the FL on/after the result date",
            "  - dated after the notification extract ends",
            "FLAG 2 - YES / NO result other than Y (all '0'), accepted",
            "  - inspection lots",
            "  - Functional Locations",
            "  - with a notification on the FL on/after the result date",
            "  - dated after the notification extract ends",
            "Notification extract (Bokor) ends",
        ],
        "Value": [
            len(mic), int(is_na.sum()), int(is_yn.sum()), int(is_num.sum()), int(accepted.sum()),
            int((~mic["UDVal"].fillna("").eq("A")).sum()),
            len(oos), oos["Inspection Lot"].nunique(), oos["Functional Location"].nunique(),
            int((oos["Notifications on the FL on/after the result date"] > 0).sum()), after_extract(oos),
            len(yn), yn["Inspection Lot"].nunique(), yn["Functional Location"].nunique(),
            int((yn["Notifications on the FL on/after the result date"] > 0).sum()), after_extract(yn),
            f"{nn_end:%d %b %Y}",
        ],
    })
    overview = (pd.DataFrame({"Specification": spec, "flag_1": out_of_spec & accepted, "flag_2": yn_not_y & accepted})
                .groupby("Specification").agg(records=("flag_1", "size"), outside_spec_accepted=("flag_1", "sum"),
                                              yes_no_not_y_accepted=("flag_2", "sum"))
                .sort_values("records", ascending=False).reset_index())
    print(summary.to_string(index=False))
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        oos.to_excel(xl, sheet_name="Out_Of_Spec_Accepted", index=False)
        yn.to_excel(xl, sheet_name="YesNo_Result_Not_Y", index=False)
        overview.to_excel(xl, sheet_name="Specification_Overview", index=False)
    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
