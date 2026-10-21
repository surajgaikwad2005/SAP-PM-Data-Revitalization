"""Load the Bokor equipment master (from KG) and the Bokor worklist (from xlsx)."""

from pathlib import Path
import pandas as pd

from db_connection import get_connection

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
PROCESSED_DIR = PROJECT_ROOT / "Code Folder" / "SD-TA Agent" / "Processed Data"

# WORKLIST_XLSX = PROJECT_ROOT / "Code Folder" / "SD-TA Agent" / "Merged Sheet" / "Worklist_2024.xlsx"
# MASTER_CACHE = PROCESSED_DIR / "Equipment_Master_Bokor_2024.xlsx"

WORKLIST_XLSX = PROJECT_ROOT / "Code Folder" / "SD-TA Agent" / "Merged Sheet" / "Worklist_2026.xlsx"
MASTER_CACHE = PROCESSED_DIR / "Equipment_Master_Bokor_2026.xlsx"


def fetch_equipment_master(refresh=False):
    """Pull Bokor equipment (7 columns) from the KG; cache to xlsx."""
    if not refresh and MASTER_CACHE.exists():
        print(f"Using cached master: {MASTER_CACHE.name}")
        return pd.read_excel(MASTER_CACHE)

    print("Fetching Bokor equipment master from KG...")
    equipment_sql = """
        SELECT
            n.node_id,
            n.natural_key AS "EquipmentNo",
            MAX(np.value_text) FILTER (WHERE np.property_name = 'object_description') AS "ObjectDescription",
            MAX(np.value_text) FILTER (WHERE np.property_name = 'catalog_profile')    AS "CatalogProfile",
            MAX(np.value_text) FILTER (WHERE np.property_name = 'technical_identno')  AS "TechnicalIdentNo",
            MAX(np.value_text) FILTER (WHERE np.property_name = 'functlocdescrip')    AS "FunctLocDescrip",
            MAX(np.value_text) FILTER (WHERE np.property_name = 'system_status')      AS "SystemStatus"
        FROM nodes n
        JOIN node_properties np ON np.node_id = n.node_id
        WHERE n.node_type = 'Equipment'
          AND n.node_id IN (
              SELECT node_id FROM node_properties
              WHERE property_name = 'location' AND value_text = 'BOKOR'
          )
        GROUP BY n.node_id, n.natural_key
    """
    floc_sql = """
        SELECT e.target_id AS node_id, fl.natural_key AS "FunctionalLocation"
        FROM edges e
        JOIN nodes fl ON fl.node_id = e.source_id
        WHERE e.relationship = 'HAS_EQUIPMENT'
          AND e.target_id = ANY(%s)
    """
    with get_connection() as conn:
        equip = pd.read_sql(equipment_sql, conn)
        print(f"  {len(equip)} equipment rows")
        floc = pd.read_sql(floc_sql, conn, params=(equip["node_id"].tolist(),))
        print(f"  {len(floc)} equipment->FL edges")

    df = equip.merge(floc, on="node_id", how="left").drop(columns=["node_id"])
    df.to_excel(MASTER_CACHE, index=False)
    print(f"Cached master to {MASTER_CACHE.name}")
    return df


def load_worklist_bokor(sample=None, seed=42):
    """Load Worklist.xlsx, filter to Bokor rows, optionally sample N."""
    print(f"Loading worklist: {WORKLIST_XLSX.name}")
    try:
        df = pd.read_excel(WORKLIST_XLSX, sheet_name="Export")
    except ValueError:
        df = pd.read_excel(WORKLIST_XLSX)

    before = len(df)
    df = df[df["Loc"].fillna("").astype(str).str.strip().str.lower() == "bokor"]
    df = df.dropna(subset=["EquipmentNo"]).reset_index(drop=True)
    print(f"  Bokor rows with EquipmentNo: {len(df)}/{before}")

    if sample and len(df) > sample:
        df = df.sample(n=sample, random_state=seed).reset_index(drop=True)
        print(f"  Sampled {len(df)}")
    return df
