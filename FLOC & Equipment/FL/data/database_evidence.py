"""
Reference data loaders: PostgreSQL tables (via data.db_connection), pickle caches and local Excel fallbacks.

Tables: public.process_subprocess and public.catalog_profile (shared standards) and the site ECA
criticality table settings.ECA_TABLE (e.g. public.bokor_eca_report).
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import settings
from .db_connection import get_connection, load_asset_cache

ROOT_DIR = settings.PROJECT_ROOT


TABLE_COLUMNS = {
    "process_subprocess": [
        "process_code",
        "process_name",
        "sub_process_code",
        "sub_process_name",
        "description",
        "source_page",
    ],
    "catalog_profile": [
        "level_raw",
        "level",
        "class",
        "class_description",
        "symptom_code",
        "symptom_description",
        "source_page",
    ],
    settings.ECA_TABLE: [
        "functional_location",
        "functional_location_description",
        "criticality",
        "criticality_norm",
        "source_file",
        "page_no",
    ],
}


LOCAL_FALLBACKS = {
    "process_subprocess": settings.PROCESS_SUBPROCESS_FALLBACK,
    "catalog_profile": settings.CATALOG_PROFILE_FALLBACK,
    settings.ECA_TABLE: settings.ECA_REPORT_FALLBACK,
}


def load_reference_table(
    table_name: str,
    cache_dir: str = settings.CACHE_DIR,
    use_database: bool = True,
    rebuild_cache: bool = False,
    allow_local_fallback: bool = True,
) -> pd.DataFrame:
    if table_name not in TABLE_COLUMNS:
        raise ValueError(f"Unsupported reference table: {table_name}")

    cache_path = Path(cache_dir) / "db_tables" / f"{table_name}.pkl"
    if cache_path.exists() and not rebuild_cache:
        try:
            return pd.read_pickle(cache_path)
        except Exception as exc:
            logging.warning("Could not read cached %s table: %s", table_name, exc)

    df = pd.DataFrame()
    if use_database:
        df = _load_from_postgres(table_name)

    if df.empty and allow_local_fallback:
        df = _load_local_fallback(table_name)

    if not df.empty:
        df = _standardize_columns(df, table_name)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_pickle(cache_path)
    return df


def load_asset_master_cache(
    cache_file: str = settings.ASSET_CACHE_FILE,
    force_refresh: bool = False,
) -> dict[str, Any]:
    path = Path(cache_file)
    if path.exists() and not force_refresh:
        with path.open("rb") as file:
            return pickle.load(file)

    try:
        return load_asset_cache(force_refresh=force_refresh, cache_file=path)
    except Exception as exc:
        logging.warning("Asset master cache unavailable: %s", exc)
        return {}


ECA_LINK_COLUMNS = ["functional_location", "equipment_number", "source_file", "page_no"]


def load_eca_equipment_links(cache_dir: str = settings.CACHE_DIR, rebuild_cache: bool = False, use_database: bool = True) -> pd.DataFrame:
    """
    ECA report rows linking an equipment tag (Equipment Number, e.g. BOKA-EF3709-M) to its Level 8
    Functional Location. Read from the site ECA table (settings.ECA_TABLE_FQN) when it has equipment_number,
    else from the ECA extract workbook(s) in the project root / settings.ECA_EXTRACT_DIR.
    """
    cache_path = Path(cache_dir) / "db_tables" / f"{settings.SITE_SLUG}_eca_equipment_links.pkl"
    if cache_path.exists() and not rebuild_cache:
        try:
            return pd.read_pickle(cache_path)
        except Exception as exc:
            logging.warning("Could not read cached ECA equipment links: %s", exc)

    df = pd.DataFrame()
    if use_database:
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"select {', '.join(ECA_LINK_COLUMNS)} from {settings.ECA_TABLE_FQN}")
                    df = pd.DataFrame(cursor.fetchall(), columns=ECA_LINK_COLUMNS)
        except Exception as exc:
            logging.info("%s has no equipment link columns, using ECA extract workbook: %s", settings.ECA_TABLE_FQN, exc)
            df = pd.DataFrame()

    if df.empty:
        frames = []
        for path in sorted(ROOT_DIR.glob("ECA_Extract*.xlsx")) + sorted(settings.ECA_EXTRACT_DIR.glob("ECA_Extract*.xlsx")):
            try:
                frames.append(pd.read_excel(path, dtype=str).fillna(""))
            except Exception as exc:
                logging.warning("ECA extract %s unavailable: %s", path, exc)
        if frames:
            raw = pd.concat(frames, ignore_index=True)
            normalized = {_normalize_header(col): col for col in raw.columns}
            df = pd.DataFrame(
                {col: raw[normalized[_normalize_header(col)]] if _normalize_header(col) in normalized else "" for col in ECA_LINK_COLUMNS}
            )

    if not df.empty:
        df = df.fillna("").astype(str)
        df = df[(df["functional_location"].str.strip() != "") & (df["equipment_number"].str.strip() != "")]
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_pickle(cache_path)
    logging.info("Loaded %s ECA equipment -> Functional Location links", len(df))
    return df


def _load_from_postgres(table_name: str) -> pd.DataFrame:
    columns = TABLE_COLUMNS[table_name]
    quoted = ", ".join(columns)
    sql = f"select {quoted} from public.{table_name}"
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
    except Exception as exc:
        logging.warning("Database table public.%s unavailable, using cache/file fallback: %s", table_name, exc)
        return pd.DataFrame()


def _load_local_fallback(table_name: str) -> pd.DataFrame:
    path = LOCAL_FALLBACKS.get(table_name)
    if not path or not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_excel(path, dtype=str).fillna("")
    except Exception as exc:
        logging.warning("Local fallback %s unavailable: %s", path, exc)
        return pd.DataFrame()


def _standardize_columns(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    normalized = {_normalize_header(col): col for col in df.columns}
    output = pd.DataFrame()
    for expected in TABLE_COLUMNS[table_name]:
        source = normalized.get(_normalize_header(expected))
        output[expected] = df[source].fillna("").astype(str) if source else ""
    return output


def _normalize_header(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())
