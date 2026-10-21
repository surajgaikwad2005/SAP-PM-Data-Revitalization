"""Group worklist equipment into TaskList Groups using the Equipment Class
hierarchy (Level 3) and the SAP naming convention: <PlantCode><Class>."""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WORKLISTS = [
    BASE / "Processed Data" / "Cleanly_Mapped_Worklist_Bokor_2024.xlsx",
    BASE / "Processed Data" / "Cleanly_Mapped_Worklist_Bokor_2026.xlsx",
]
EQ_MASTER = BASE / "Processed Data" / "Equipment_Master_Bokor_2024.xlsx"
EQ_CLASS = BASE / "Raw data" / "Equipment Class.xlsx"
OUTPUT = BASE / "Processed Data" / "TaskList_Groups_Bokor.xlsx"

PLANT_NAME = "Bokor"
PLANT_CODE = "SK"
LEVEL = 2

# --- Load inputs
wl = pd.concat([pd.read_excel(f) for f in WORKLISTS], ignore_index=True)
em = pd.read_excel(EQ_MASTER)[["EquipmentNo", "ObjectDescription", "CatalogProfile"]]
cls = pd.read_excel(EQ_CLASS)[["Level", "Class", "Class Description"]].dropna(subset=["Class"])
cls["Class"] = cls["Class"].str.strip().str.upper()

# --- Join worklist -> equipment master -> catalog profile
wl["Suggested EquipmentNo"] = wl["Suggested EquipmentNo"].astype(str).str.strip()
em["EquipmentNo"] = em["EquipmentNo"].astype(str).str.strip()
df = wl.merge(em, left_on="Suggested EquipmentNo", right_on="EquipmentNo", how="left")

# Strip leading digit from CatalogProfile: "1IVCV" -> "IVCV"
df["CPCore"] = df["CatalogProfile"].astype(str).str.replace(r"^\d+", "", regex=True).str.upper()

# --- Resolve class: prefer Level 3, roll up to Level 2 / 1 otherwise
lookup = cls.set_index("Class").to_dict("index")

def resolve(code):
    if not code or code == "NAN":
        return None, None, None
    for n in range(len(code), 0, -1):
        hit = lookup.get(code[:n])
        if hit and hit["Level"] <= LEVEL:
            return code[:n], hit["Level"], hit["Class Description"]
    return None, None, None

df[["Class", "ClassLevel", "ClassDescription"]] = df["CPCore"].apply(
    lambda c: pd.Series(resolve(c))
)

# --- Build TaskList Group name & description
df["TaskListGroup"] = df["Class"].apply(lambda c: f"{PLANT_CODE}{c}" if c else None)
df["TaskListGroupDescription"] = df.apply(
    lambda r: f"{PLANT_NAME} - {r['ClassDescription']} - {r['Job Description']}"
    if r["Class"] else None, axis=1
)

# --- Build class-wise sheet: header row per class, then its equipment rows
EQUIP_COLS = ["Suggested EquipmentNo", "ObjectDescription", "CatalogProfile",
              "Job Description", "WorklistID", "SubLoc1", "Discipline", "EqptType"]

rows = []
resolved = df.dropna(subset=["TaskListGroup"]).sort_values(["TaskListGroup", "Suggested EquipmentNo"])
for (group, cls_code, cls_desc), block in resolved.groupby(
        ["TaskListGroup", "Class", "ClassDescription"], dropna=False, sort=True):
    # Header row: class name across the first columns
    header = {c: "" for c in EQUIP_COLS}
    header["Suggested EquipmentNo"] = f"{group} - {cls_code} - {cls_desc} ({len(block)} items)"
    rows.append(header)
    # Equipment rows under the header
    for _, r in block.iterrows():
        rows.append({c: r.get(c, "") for c in EQUIP_COLS})
    rows.append({c: "" for c in EQUIP_COLS})  # blank spacer

classwise = pd.DataFrame(rows, columns=EQUIP_COLS)

# --- Write output
from openpyxl.styles import PatternFill, Font, Alignment

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as xw:
    classwise.to_excel(xw, sheet_name="ClasswiseEquipment", index=False)
    df.to_excel(xw, sheet_name="Worklist_Enriched", index=False)

    # Style the header rows (those starting with the plant code prefix)
    ws = xw.sheets["ClasswiseEquipment"]
    fill = PatternFill("solid", fgColor="305496")
    font = Font(bold=True, color="FFFFFF")
    for row_idx in range(2, ws.max_row + 1):
        cell_val = ws.cell(row=row_idx, column=1).value or ""
        if cell_val.startswith(PLANT_CODE) and " - " in cell_val:
            for col in range(1, len(EQUIP_COLS) + 1):
                c = ws.cell(row=row_idx, column=col)
                c.fill = fill
                c.font = font
                c.alignment = Alignment(horizontal="left")
    for col_idx, col_name in enumerate(EQUIP_COLS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = \
            max(18, min(60, len(col_name) + 10))

n_groups = resolved["TaskListGroup"].nunique()
print(f"Wrote {OUTPUT}")
print(f"{len(df)} worklist rows -> {n_groups} tasklist groups "
      f"({df['Class'].isna().sum()} unresolved)")
