"""
Asset master loader: reads Functional Locations, Equipment and their graph relations from the
PostgreSQL knowledge graph (nodes / node_properties / edges) and stores them as a pickle cache.

Pipeline step 1. The cache is reused on later runs; use --force-asset-refresh (or `--refresh` below)
to rebuild it. Connection details come only from .env (FL_DB_HOST, FL_DB_NAME, FL_DB_USER,
FL_DB_TENANT_ID, FL_DB_TOKEN_SCOPE); authentication uses the Azure CLI login (`az login`).

Standalone, from the AgentV2 root:
    python -m FL.data.db_connection [--refresh] [--equipment 30166] [--floc <FLOC>]
"""

from __future__ import annotations

import argparse
import logging
import pickle
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import settings

FL_NODE_PREFIX = "FL:"

EQUIPMENT_COLUMNS = [
    "Equipment",
    "Object Description",
    "Functional Location",
    "FunctLocDescrip.",
    "Location",
    "Technical IdentNo.",
    "Catalog Profile",
    "ABC Indicator",
    "System status",
    "User Status",
    "Maint. Planner Group",
    "Main Work Center",
    "Created By",
    "Maintenance Plant",
    "Manuf. Serial Number",
    "ManufDrawingNumber",
    "Manufacturer",
    "ManufactPartNo.",
    "Material",
    "Material Description",
    "Model number",
    "Created On",
    "Inventory Number",
    "Plant",
]

FL_COLUMNS = [
    "Maintenance Plant",
    "Functional Location",
    "FunctLocDescrip.",
    "User Status",
    "Location",
    "System status",
    "Created On",
    "Main Work Center",
    "Inventory Number",
    "Superior FunctLoc.",
    "Changed On",
    "ABC Indicator",
]

# Output column -> property names it may have in node_properties (compared after normalize_name).
PROPERTY_ALIASES: dict[str, list[str]] = {
    "Object Description": ["object_description", "equipment_description", "description", "object_desc"],
    "FunctLocDescrip.": [
        "functlocdescrip",
        "functional_location_description",
        "functional_location_desc",
        "funct_loc_description",
        "fl_description",
        "description",
    ],
    "Functional Location": ["functional_location", "functional_location_code", "funct_loc", "floc"],
    "Technical IdentNo.": ["technical_ident_no", "technical_identno", "technical_identification_number", "technical_id"],
    "Catalog Profile": ["catalog_profile", "catalogprofile"],
    "ABC Indicator": ["abc_indicator", "abcindicator"],
    "System status": ["system_status", "systemstatus"],
    "User Status": ["user_status", "userstatus"],
    "Maint. Planner Group": ["maint_planner_group", "maintenance_planner_group", "planner_group"],
    "Main Work Center": ["main_work_center", "mainworkcenter", "work_center"],
    "Created By": ["created_by", "createdby"],
    "Maintenance Plant": ["maintenance_plant", "maintenanceplant", "maint_plant"],
    "Manuf. Serial Number": ["manuf_serial_number", "manufacturer_serial_number", "manufact_serial_number", "serial_number"],
    "ManufDrawingNumber": ["manuf_drawing_number", "manufacturer_drawing_number", "manufact_drawing_number", "drawing_number"],
    "Manufacturer": ["manufacturer"],
    "ManufactPartNo.": ["manufact_part_no", "manufacturer_part_no", "manufacturer_part_number", "manufact_part_number"],
    "Material": ["material", "material_number"],
    "Material Description": ["material_description", "material_desc"],
    "Model number": ["model_number", "model_no", "model"],
    "Created On": ["created_on", "created_date", "creation_date"],
    "Changed On": ["changed_on", "changed_date", "last_changed_on"],
    "Inventory Number": ["inventory_number", "inventory_no"],
    "Superior FunctLoc.": ["superior_functloc", "superior_functional_location", "superior_funct_loc", "parent_functional_location"],
    "Plant": ["plant"],
    "Location": ["location"],
}

NODES_QUERY = """
    SELECT n.node_id, n.natural_key, np.property_name, np.value_text, np.value_num, np.value_date
    FROM nodes n
    LEFT JOIN node_properties np ON np.node_id = n.node_id
    WHERE n.node_type = %s
    ORDER BY n.node_id, np.property_name;
"""

RELATIONSHIPS_QUERY = """
    SELECT source_id, relationship, target_id
    FROM edges
    WHERE relationship IN ('HAS_EQUIPMENT', 'HAS_SUBFLOC');
"""


# ------------------------------------------------------------------ connection
def get_connection() -> Any:
    """PostgreSQL connection authenticated with an Azure AD token from the Azure CLI login."""
    import psycopg
    from azure.identity import AzureCliCredential

    logging.info("Getting Azure access token...")
    credential = AzureCliCredential(tenant_id=settings.require("FL_DB_TENANT_ID"))
    token = credential.get_token(settings.require("FL_DB_TOKEN_SCOPE"))
    logging.info("Connecting to PostgreSQL...")
    conn = psycopg.connect(
        host=settings.require("FL_DB_HOST"),
        port=settings.DB_PORT,
        dbname=settings.require("FL_DB_NAME"),
        user=settings.require("FL_DB_USER"),
        password=token.token,
        sslmode=settings.DB_SSLMODE,
        connect_timeout=settings.DB_CONNECT_TIMEOUT,
    )
    logging.info("Connected to PostgreSQL.")
    return conn


# ------------------------------------------------------------------ property helpers
def normalize_name(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _clean_db_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def get_property(properties: dict[str, Any], column_name: str) -> Any:
    for candidate in [column_name, *PROPERTY_ALIASES.get(column_name, [])]:
        value = properties.get(normalize_name(candidate))
        if value is not None:
            return value
    return None


def _remove_prefix(node_id: str | None, prefix: str) -> str | None:
    if node_id is None:
        return None
    return node_id[len(prefix):] if node_id.startswith(prefix) else node_id


# ------------------------------------------------------------------ database reads
def load_nodes(conn: Any, node_type: str) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    with conn.cursor() as cursor:
        cursor.execute(NODES_QUERY, (node_type,))
        for node_id, natural_key, property_name, value_text, value_num, value_date in cursor:
            if node_id not in nodes:
                nodes[node_id] = {"natural_key": natural_key, "properties": {}}
            if property_name is None:
                continue
            if value_text is not None:
                value = value_text
            elif value_num is not None:
                value = _clean_db_value(value_num)
            elif value_date is not None:
                value = _clean_db_value(value_date)
            else:
                value = None
            nodes[node_id]["properties"][normalize_name(property_name)] = value
    logging.info("%s: %s nodes loaded", node_type, f"{len(nodes):,}")
    return nodes


def load_relationships(conn: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Return (equipment -> FL, child FL -> parent FL) from the graph edges."""
    equipment_to_fl: dict[str, str] = {}
    fl_to_parent: dict[str, str] = {}
    with conn.cursor() as cursor:
        cursor.execute(RELATIONSHIPS_QUERY)
        for source_id, relationship, target_id in cursor:
            if relationship == "HAS_EQUIPMENT":
                equipment_to_fl[target_id] = source_id
            elif relationship == "HAS_SUBFLOC":
                fl_to_parent[target_id] = source_id
    logging.info("HAS_EQUIPMENT relationships: %s", f"{len(equipment_to_fl):,}")
    logging.info("HAS_SUBFLOC relationships: %s", f"{len(fl_to_parent):,}")
    return equipment_to_fl, fl_to_parent


# ------------------------------------------------------------------ dataframes
def build_equipment_dataframe(
    equipment_nodes: dict[str, dict[str, Any]],
    fl_nodes: dict[str, dict[str, Any]],
    equipment_to_fl: dict[str, str],
) -> pd.DataFrame:
    rows = []
    for equipment_node_id, equipment in equipment_nodes.items():
        properties = equipment["properties"]
        row: dict[str, Any] = {"Equipment": equipment["natural_key"]}

        # Functional Location from the HAS_EQUIPMENT edge, else from the equipment's own property.
        fl_node_id = equipment_to_fl.get(equipment_node_id)
        if fl_node_id:
            row["Functional Location"] = _remove_prefix(fl_node_id, FL_NODE_PREFIX)
        else:
            row["Functional Location"] = get_property(properties, "Functional Location")

        for column in EQUIPMENT_COLUMNS:
            if column in ("Equipment", "Functional Location", "FunctLocDescrip."):
                continue
            row[column] = get_property(properties, column)

        fl_description = get_property(properties, "FunctLocDescrip.")
        if fl_description is None and fl_node_id in fl_nodes:
            fl_description = get_property(fl_nodes[fl_node_id]["properties"], "FunctLocDescrip.")
        row["FunctLocDescrip."] = fl_description
        rows.append(row)

    df = pd.DataFrame(rows, columns=EQUIPMENT_COLUMNS)
    if not df.empty:
        df["Equipment"] = df["Equipment"].astype(str).str.strip()
        df = df.sort_values("Equipment").reset_index(drop=True)
    return df


def build_fl_dataframe(fl_nodes: dict[str, dict[str, Any]], fl_to_parent: dict[str, str]) -> pd.DataFrame:
    rows = []
    for fl_node_id, fl in fl_nodes.items():
        properties = fl["properties"]
        row: dict[str, Any] = {"Functional Location": fl["natural_key"]}

        # Superior Functional Location from the HAS_SUBFLOC edge, else from the FL's own property.
        parent_node_id = fl_to_parent.get(fl_node_id)
        if parent_node_id:
            row["Superior FunctLoc."] = _remove_prefix(parent_node_id, FL_NODE_PREFIX)
        else:
            row["Superior FunctLoc."] = get_property(properties, "Superior FunctLoc.")

        for column in FL_COLUMNS:
            if column in ("Functional Location", "Superior FunctLoc."):
                continue
            row[column] = get_property(properties, column)
        rows.append(row)

    df = pd.DataFrame(rows, columns=FL_COLUMNS)
    if not df.empty:
        df["Functional Location"] = df["Functional Location"].astype(str).str.strip()
        df = df.sort_values("Functional Location").reset_index(drop=True)
    return df


def format_dates(equipment_df: pd.DataFrame, fl_df: pd.DataFrame) -> None:
    for column in ("Created On",):
        if column in equipment_df.columns:
            equipment_df[column] = pd.to_datetime(equipment_df[column], errors="coerce")
    for column in ("Created On", "Changed On"):
        if column in fl_df.columns:
            fl_df[column] = pd.to_datetime(fl_df[column], errors="coerce")


def create_lookups(equipment_df: pd.DataFrame, fl_df: pd.DataFrame) -> tuple[dict, dict, dict[str, list[str]]]:
    """Return (equipment_lookup, fl_lookup, equipment_by_floc)."""
    equipment_lookup = equipment_df.set_index("Equipment").to_dict("index")
    fl_lookup = fl_df.set_index("Functional Location").to_dict("index")
    equipment_by_floc: dict[str, list[str]] = {}
    valid_equipment = equipment_df[equipment_df["Functional Location"].notna()]
    for floc, group in valid_equipment.groupby("Functional Location"):
        equipment_by_floc[str(floc).strip()] = group["Equipment"].astype(str).str.strip().tolist()
    return equipment_lookup, fl_lookup, equipment_by_floc


# ------------------------------------------------------------------ cache
def save_cache(
    cache_file: Path,
    equipment_df: pd.DataFrame,
    fl_df: pd.DataFrame,
    equipment_to_fl: dict[str, str],
    fl_to_parent: dict[str, str],
) -> dict[str, Any]:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    equipment_lookup, fl_lookup, equipment_by_floc = create_lookups(equipment_df, fl_df)
    cache = {
        "created_at": datetime.now(),
        "equipment_df": equipment_df,
        "fl_df": fl_df,
        "equipment_lookup": equipment_lookup,
        "fl_lookup": fl_lookup,
        "equipment_by_floc": equipment_by_floc,
        "equipment_to_fl": equipment_to_fl,
        "fl_to_parent": fl_to_parent,
    }
    with cache_file.open("wb") as file:
        pickle.dump(cache, file, protocol=pickle.HIGHEST_PROTOCOL)
    logging.info(
        "Asset cache created: %s equipment, %s Functional Locations, %s FL with equipment -> %s",
        f"{len(equipment_lookup):,}", f"{len(fl_lookup):,}", f"{len(equipment_by_floc):,}", cache_file.resolve(),
    )
    return cache


def load_cache(cache_file: Path) -> dict[str, Any] | None:
    if not cache_file.exists():
        return None
    with cache_file.open("rb") as file:
        cache = pickle.load(file)
    logging.info(
        "Asset cache loaded (created %s): %s equipment, %s Functional Locations",
        cache.get("created_at"), f"{len(cache['equipment_lookup']):,}", f"{len(cache['fl_lookup']):,}",
    )
    return cache


def load_asset_cache(force_refresh: bool = False, cache_file: str | Path = settings.ASSET_CACHE_FILE) -> dict[str, Any]:
    """Existing cache -> no DB query; otherwise build the asset master from PostgreSQL and cache it."""
    cache_path = Path(cache_file)
    if cache_path.exists() and not force_refresh:
        return load_cache(cache_path)

    logging.info("Building asset cache from PostgreSQL...")
    conn = None
    try:
        conn = get_connection()
        fl_nodes = load_nodes(conn, "FunctionalLocation")
        equipment_nodes = load_nodes(conn, "Equipment")
        equipment_to_fl, fl_to_parent = load_relationships(conn)
        equipment_df = build_equipment_dataframe(equipment_nodes, fl_nodes, equipment_to_fl)
        fl_df = build_fl_dataframe(fl_nodes, fl_to_parent)
        format_dates(equipment_df, fl_df)
        return save_cache(cache_path, equipment_df, fl_df, equipment_to_fl, fl_to_parent)
    finally:
        if conn is not None:
            conn.close()
            logging.info("Database connection closed.")


def refresh_cache(cache_file: str | Path = settings.ASSET_CACHE_FILE) -> dict[str, Any]:
    return load_asset_cache(force_refresh=True, cache_file=cache_file)


# ------------------------------------------------------------------ lookups
def get_equipment(cache: dict[str, Any], equipment_number: Any) -> dict[str, Any] | None:
    return cache["equipment_lookup"].get(str(equipment_number).strip())


def get_functional_location(cache: dict[str, Any], functional_location: Any) -> dict[str, Any] | None:
    return cache["fl_lookup"].get(str(functional_location).strip())


def get_equipment_by_floc(cache: dict[str, Any], functional_location: Any) -> list[str]:
    return cache["equipment_by_floc"].get(str(functional_location).strip(), [])


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Build or inspect the {settings.SITE_NAME} asset master cache.")
    parser.add_argument("--refresh", action="store_true", help="Rebuild the cache from PostgreSQL")
    parser.add_argument("--cache-file", default=settings.ASSET_CACHE_FILE)
    parser.add_argument("--equipment", default="", help="Print one equipment record")
    parser.add_argument("--floc", default="", help="Print one Functional Location and its installed equipment")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cache = load_asset_cache(force_refresh=args.refresh, cache_file=args.cache_file)
    if args.equipment:
        print(f"Equipment {args.equipment}: {get_equipment(cache, args.equipment) or 'not found'}")
    if args.floc:
        print(f"Functional Location {args.floc}: {get_functional_location(cache, args.floc) or 'not found'}")
        print(f"Equipment under FL: {get_equipment_by_floc(cache, args.floc)}")


if __name__ == "__main__":
    main()
