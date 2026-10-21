"""Shared data classes, text/FLOC normalisation helpers and evidence-cache I/O."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


FLOC_RE = re.compile(r"\b[A-Z0-9]{2,}(?:[.-][A-Z0-9]{1,}){1,}(?:-[A-Z0-9]+)?\b")
TAG_RE = re.compile(r"\b[A-Z]{1,8}[-]?\d{2,6}[A-Z0-9]*(?:-[A-Z0-9]+)?\b")
CRITICALITY_RE = re.compile(r"\bC\s*[-:]?\s*([123])\b", re.IGNORECASE)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_type: str
    key: str
    value: str
    source_name: str
    source_ref: str
    evidence_text: str
    confidence_base: float


@dataclass
class ValidationResult:
    suggested_value: str = ""
    status: str = "OK"
    confidence: float | str = ""
    evidence: str = ""


def normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip().upper())


def normalize_floc(value: Any) -> str:
    return normalize_text(value).replace(" ", "")


def compact_key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_text(value))


def normalize_abc(value: Any) -> str:
    match = re.search(r"[123]", normalize_text(value))
    return match.group(0) if match else ""


def inventory_level(value: Any) -> int | None:
    match = re.search(r"\d+", normalize_text(value))
    return int(match.group(0)) if match else None


def inventory_suffix(value: Any) -> str:
    match = re.search(r"\d+\s*([A-Z])", normalize_text(value))
    return match.group(1) if match else ""


def split_floc(value: str) -> list[str]:
    return [part for part in re.split(r"[.-]", normalize_floc(value)) if part]


def parent_floc(floc: str) -> str:
    clean = normalize_floc(floc)
    if "-" in clean:
        return clean.rsplit("-", 1)[0]
    if "." in clean:
        return clean.rsplit(".", 1)[0]
    return ""


def tag_suffix(floc: str) -> str:
    clean = normalize_floc(floc)
    if "-" in clean:
        return clean.rsplit("-", 1)[-1]
    parts = split_floc(clean)
    return parts[-1] if parts else ""


def is_final_tag_floc(floc: str) -> bool:
    return "-" in normalize_floc(floc) and bool(re.search(r"\d", tag_suffix(floc)))


def normalized_header(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_text(value))


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    columns = [str(col) for col in df.columns]
    by_normalized = {normalized_header(col): col for col in columns}
    for alias in aliases:
        found = by_normalized.get(normalized_header(alias))
        if found:
            return found
    for col in columns:
        if any(normalized_header(alias) in normalized_header(col) for alias in aliases):
            return col
    return None


def insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
    """Place `new_cols` directly after `source_col` (or at the end when it is missing)."""
    if not source_col or source_col not in df.columns:
        return pd.concat([df, new_cols], axis=1)
    parts = []
    for col in df.columns:
        parts.append(df[[col]])
        if col == source_col:
            parts.append(new_cols)
    return pd.concat(parts, axis=1)


def file_signature(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {"path": str(path.resolve()), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def load_cached_records(cache_path: Path, files: list[Path], rebuild_cache: bool) -> list[EvidenceRecord] | None:
    if rebuild_cache or not cache_path.exists():
        return None
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    if payload.get("file_signatures") != [file_signature(path) for path in files]:
        return None
    return [EvidenceRecord(**item) for item in payload.get("records", [])]


def save_cached_records(cache_path: Path, files: list[Path], records: list[EvidenceRecord]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {
                "file_signatures": [file_signature(path) for path in files],
                "records": [asdict(record) for record in records],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class FunctionalLocationHierarchy:
    def __init__(self, df: pd.DataFrame, floc_col: str | None, superior_col: str | None):
        self.by_floc: dict[str, int] = {}
        self.children: dict[str, list[str]] = {}
        if not floc_col:
            return
        for idx, row in df.iterrows():
            floc = normalize_floc(row.get(floc_col, ""))
            superior = normalize_floc(row.get(superior_col, "")) if superior_col else ""
            if floc:
                self.by_floc[floc] = idx
            if superior:
                self.children.setdefault(superior, []).append(floc)

    def exists(self, floc: str) -> bool:
        return normalize_floc(floc) in self.by_floc

    def child_count(self, floc: str) -> int:
        return len(self.children.get(normalize_floc(floc), []))

    def is_leaf(self, floc: str) -> bool:
        return self.child_count(floc) == 0
