"""
Pain Point 8 - Rejected inspection lots vs notification history (mapping stage)
------------------------------------------------------------------------------
Goal of the pain point: for every inspection lot whose result was rejected,
confirm that a follow-up notification was raised.

This script builds and measures the MAPPING the check will run on, using the
data available today. It does not yet report follow-up findings, because the
inspection-lot extract supplied contains no rejected lot (see below).

Mapping path (established here):
  inspection lot (MIC report) -> work order (same report, verified in the
  WO listing) -> Functional Location of the lot -> notifications raised on
  that Functional Location (notification history).
  The order number cannot be used as the key: the inspection work orders are
  generated from maintenance plans and do not appear on any notification, so
  a follow-up notification can only be found through the asset (Functional
  Location) and the date.

Measured:
  - usage decisions in the lot extract (rejected lots present or not)
  - lots whose work order is found in the WO listing
  - lots on a Functional Location that has any Bokor notification
  - lots dated after the end of the notification extract (cannot be mapped
    until a newer notification extract is supplied)

Output: Data exploration/output/D8_Inspection_Lot_Notification_Mapping.xlsx
  - Summary
  - Lot_Mapping (one row per inspection lot)

Run:
    python "code/agent/check8_inspection_lot_notification_mapping.py"
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
OUT_XLSX = ROOT / "Data exploration" / "output" / "D8_Inspection_Lot_Notification_Mapping.xlsx"


def norm_fl(s):
    return s.astype(str).str.replace(r"\s+", "", regex=True).str.upper()


def norm_no(s):
    return s.astype(str).str.strip().str.lstrip("0")


def main():
    mic = pd.read_excel(MIC_REPORT_FILE, sheet_name="Data", dtype=str)
    mic.columns = [c.strip() for c in mic.columns]
    wo = pd.read_excel(WO_NN_FILE, sheet_name="M014_Work Order", dtype=str)
    nn = pd.read_excel(WO_NN_FILE, sheet_name="Notification", dtype=str)
    nn = nn[nn["Location"].str.upper().eq("BOKOR")].copy()
    nn["fl"] = norm_fl(nn["Functional Location"])
    nn["date"] = pd.to_datetime(nn["Notification date"], errors="coerce")
    nn_end = nn["date"].max()
    print(f"Bokor notifications: {len(nn):,} ({nn['date'].min():%d %b %Y} - {nn_end:%d %b %Y})")

    lots = mic.groupby("Inspection Lot").agg(
        order=("Order", "first"), functional_location=("Functional Location", "first"),
        sce_group=("SCE Grp - FL", "first"), created_on=("Created on", "first"),
        usage_decision=("UD", lambda s: ",".join(sorted(set(s.dropna())))),
        ud_valuation=("UDVal", lambda s: ",".join(sorted(set(s.dropna())))),
    ).reset_index()
    lots["date"] = pd.to_datetime(lots["created_on"], errors="coerce")
    lots["fl"] = norm_fl(lots["functional_location"])
    lots["rejected"] = lots["ud_valuation"].str.contains("R")
    lots["work_order_in_wo_listing"] = norm_no(lots["order"]).isin(set(norm_no(wo["Order"])))
    lots["work_order_on_a_notification"] = norm_no(lots["order"]).isin(set(norm_no(nn["Order"].dropna())))
    nn_per_fl = nn.groupby("fl").size()
    lots["notifications_on_fl"] = lots["fl"].map(nn_per_fl).fillna(0).astype(int)
    lots["after_notification_extract"] = lots["date"] > nn_end
    print(f"Inspection lots: {len(lots):,}; rejected: {lots['rejected'].sum()}")

    summary = pd.DataFrame({
        "Metric": [
            "Inspection lots in the MIC report (2024-2025 extract)",
            "  - lots with a rejected usage decision",
            "  - lots whose work order is found in the WO listing",
            "  - lots whose work order appears on a notification",
            "  - lots on a Functional Location with at least one Bokor notification",
            "  - lots dated after the last notification in the extract",
            "Distinct Functional Locations of the lots",
            "  - with at least one Bokor notification",
            "Bokor notifications in the extract",
            "Notification extract date range",
        ],
        "Value": [
            len(lots), int(lots["rejected"].sum()), int(lots["work_order_in_wo_listing"].sum()),
            int(lots["work_order_on_a_notification"].sum()), int((lots["notifications_on_fl"] > 0).sum()),
            int(lots["after_notification_extract"].sum()),
            lots["fl"].nunique(), int(pd.Series(lots["fl"].unique()).isin(nn_per_fl.index).sum()),
            len(nn), f"{nn['date'].min():%d %b %Y} - {nn_end:%d %b %Y}",
        ],
    })
    print(summary.to_string(index=False))
    out_cols = ["Inspection Lot", "order", "functional_location", "sce_group", "created_on", "usage_decision",
                "ud_valuation", "rejected", "work_order_in_wo_listing", "work_order_on_a_notification",
                "notifications_on_fl", "after_notification_extract"]
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        lots[out_cols].to_excel(xl, sheet_name="Lot_Mapping", index=False)
    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
