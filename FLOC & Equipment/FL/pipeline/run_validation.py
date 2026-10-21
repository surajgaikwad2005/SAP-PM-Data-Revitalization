"""
Command-line pipeline for the FL validation agent.

Steps (main -> run_jobs -> run_dataset):
  1. Asset master     load the FL + Equipment master from the cache, or from PostgreSQL (data/db_connection.py)
  2. Hierarchy index  join FL + Equipment into AssetHierarchyIndex and attach the ECA equipment links
  3. Standards KB     build the Claude-extracted standards knowledge base when missing (hybrid mode)
  4. Input sheet      read the FL / Equipment sheet from the asset cache or from the Excel input file
  5. Rule validators  Functional Location, completion, ABC Indicator, Catalog Profile, Technical IdentNo.
  6. Claude review    only the unclear rows go to Claude (hybrid "llm") or the tool-use agent ("agent")
  7. Output           write the validated sheet + run summary as a styled Excel workbook

Every default comes from .env through config/settings.py; command-line options override it.
Run from the AgentV2 project root:
    python FL/main.py
    python -m FL --mode deterministic
"""

from __future__ import annotations

import argparse
import html
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from ..config import settings
from ..core.common import normalize_floc
from ..core.hierarchy_rules import AssetHierarchyIndex
from ..core.sources import confidence_label, deterministic_source
from ..data.database_evidence import load_asset_master_cache, load_eca_equipment_links
from ..data.db_connection import load_asset_cache
from ..llm.llm_model import LLMModel
from ..llm.llm_reviewer import LLMReviewer, fields_for_route
from ..llm.standards_kb import StandardsKB
from ..validators.abc_indicator_validator import ABCIndicatorValidator
from ..validators.catalog_profile_validator import CatalogProfileValidator
from ..validators.equipment_validator import EquipmentFieldValidator
from ..validators.functional_location_validator import FunctionalLocationValidator
from ..validators.master_data_mapper import MasterDataCompletionValidator

MODES = ("hybrid", "deterministic")


def main(default_input: str = settings.INPUT_FILE, default_output: str = settings.OUTPUT_FILE) -> None:
    args = parse_args(default_input, default_output)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    mode = resolve_mode(args)
    logging.info("Site: %s (%s) | validation mode: %s", settings.SITE_NAME, settings.SITE_CODE, mode)

    # Step 1-2: one joined FL + Equipment index shared by all validators, the reviewer and the agent tools.
    asset_cache = load_asset_master_cache(args.asset_cache_file, args.force_asset_refresh)
    index = AssetHierarchyIndex(asset_cache)
    index.attach_eca_equipment_links(load_eca_equipment_links(args.cache_dir, args.rebuild_cache, args.use_database))
    logging.info(
        "Asset index: %s FLOCs, %s equipment, %s packages with learned Level 8 naming",
        len(index.fl_records), len(index.equipment_records), len(index.level8_templates),
    )

    session_id = f"{settings.TRACE_TAG}-{datetime.now():%Y%m%d-%H%M%S}"
    trace_metadata = {"mode": mode, "dataset": args.dataset, "validator": args.validator, "limit_rows": args.limit_rows}
    try:
        if mode == "deterministic":
            run_jobs(args, mode, index)
        else:
            with LLMModel.run_trace(f"{settings.AGENT_NAME} - {settings.SITE_NAME} validation", session_id, trace_metadata, env_file=args.env_file):
                run_jobs(args, mode, index)
    finally:
        LLMModel.flush_langfuse()


def run_jobs(args: argparse.Namespace, mode: str, index: AssetHierarchyIndex) -> None:
    kb_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    # Step 3: standards KB (Claude-built) when requested or missing in hybrid mode.
    if args.build_standards_kb or args.rebuild_standards_kb or (mode != "deterministic" and not StandardsKB.is_claude_built(Path(args.standards_kb_file))):
        kb = StandardsKB(
            standards_dir=args.standards_dir,
            kb_file=args.standards_kb_file,
            env_file=args.env_file,
            model=args.model,
            max_chunks=args.standards_kb_max_chunks,
        )
        kb.ensure(force_rebuild=args.rebuild_standards_kb)
        kb_usage = kb.usage

    if args.dataset == "both":
        jobs = [
            ("fl", args.fl_input_file or args.input_file, args.fl_output_file),
            ("equipment", args.eq_input_file or args.input_file, args.eq_output_file),
        ]
    else:
        dataset = args.dataset if args.dataset != "auto" else infer_dataset(args.input_file, args.output_file)
        jobs = [(dataset, args.input_file, args.output_file)]

    for dataset, input_file, output_file in jobs:
        job_args = argparse.Namespace(**vars(args))
        job_args.dataset, job_args.input_file, job_args.output_file = dataset, input_file, output_file
        logging.info("===== Validating %s sheet -> %s =====", dataset, output_file)
        run_dataset(job_args, mode, index, kb_usage)
        kb_usage = {key: 0 for key in kb_usage}  # KB tokens are reported once


def run_dataset(args: argparse.Namespace, mode: str, index: AssetHierarchyIndex, kb_usage: dict[str, int]) -> None:
    # Step 4: input sheet.
    df = load_input_dataframe(args)
    if args.limit_rows:
        df = df.head(args.limit_rows).copy()

    # Step 5: rule validators (each adds suggest_ / confidence / evidence / status columns).

    output = df.copy()
    if args.validator in {"all", "functional_location"}:
        fl_validator = FunctionalLocationValidator(
            output,
            standards_dir=args.standards_dir,
            cache_dir=args.cache_dir,
            rebuild_cache=args.rebuild_cache,
            min_suggest_confidence=args.min_suggest_confidence,
            min_review_confidence=args.min_review_confidence,
            asset_cache_file=args.asset_cache_file,
            force_asset_refresh=False,
            use_database=args.use_database,
            index=index,
        )
        if args.validator != "all" or fl_validator.floc_col:
            output = fl_validator.add_validation_columns(output)
            write_checkpoint(output, args, "functional_location")

    if args.validator in {"all", "completion"}:
        completion = MasterDataCompletionValidator(
            output,
            index,
            min_suggest_confidence=args.min_suggest_confidence,
            min_review_confidence=args.min_review_confidence,
        )
        output = completion.add_validation_columns(output)
        write_checkpoint(output, args, "completion")

    if args.validator in {"all", "abc_indicator"}:
        abc_validator = ABCIndicatorValidator(
            output,
            eca_dir=args.eca_dir,
            cache_dir=args.cache_dir,
            rebuild_cache=args.rebuild_cache,
            max_pdf_pages=args.max_pdf_pages,
            min_suggest_confidence=args.min_suggest_confidence,
            min_review_confidence=args.min_review_confidence,
            evidence_db=args.evidence_db,
            use_database=args.use_database,
            index=index,
        )
        if args.validator != "all" or abc_validator.abc_col:
            output = abc_validator.add_validation_columns(output)
            write_checkpoint(output, args, "abc_indicator")

    if args.validator in {"all", "catalog_profile"}:
        catalog_validator = CatalogProfileValidator(
            output,
            standards_dir=args.standards_dir,
            cache_dir=args.cache_dir,
            rebuild_cache=args.rebuild_cache,
            min_suggest_confidence=args.min_suggest_confidence,
            min_review_confidence=args.min_review_confidence,
            asset_cache_file=args.asset_cache_file,
            force_asset_refresh=False,
            use_database=args.use_database,
        )
        if args.validator != "all" or catalog_validator.catalog_col:
            output = catalog_validator.add_validation_columns(output)
            write_checkpoint(output, args, "catalog_profile")

    if args.validator in {"all", "technical_ident_no"}:
        equipment_validator = EquipmentFieldValidator(
            output,
            asset_cache_file=args.asset_cache_file,
            force_asset_refresh=False,
            min_suggest_confidence=args.min_suggest_confidence,
            min_review_confidence=args.min_review_confidence,
        )
        output = equipment_validator.add_validation_columns(output)
        write_checkpoint(output, args, "technical_ident_no")

    # Step 6: Claude review of the unclear rows.
    llm_usage = dict(kb_usage)
    if mode != "deterministic":
        # Columns routed to "python" stay rule/database only; "llm" and "agent" columns send only unclear rows to Claude.
        for route in ("llm", "agent"):
            fields = fields_for_route(route, args.validator)
            if not fields:
                continue
            logging.info("Claude %s review for columns: %s", route, ", ".join(fields))
            reviewer = build_reviewer(args, route, index, fields)
            output = reviewer.review(output)
            llm_usage = {key: llm_usage.get(key, 0) + reviewer.usage.get(key, 0) for key in llm_usage}

    # Step 7: styled Excel output.
    write_output(output, args.output_file, mode, llm_usage)
    print(f"Created: {Path(args.output_file).resolve()}")


def build_reviewer(args: argparse.Namespace, route: str, index: AssetHierarchyIndex, fields: list[str]) -> Any:
    kwargs = dict(
        env_file=args.env_file,
        model=args.model,
        cache_dir=args.cache_dir,
        max_rows=args.max_llm_rows,
        batch_size=args.llm_batch_size,
        min_confidence=args.llm_min_confidence,
        validators=fields,
        include_missing_evidence=args.llm_include_missing_evidence,
        parallel_fields=args.llm_parallel_fields,
        effort=args.effort,
        skip_confidence=args.llm_skip_confidence,
        context_builder=make_context_builder(index),
        suggestion_guard=make_suggestion_guard(index),
        standards_kb_file=args.standards_kb_file,
    )
    if route == "agent":
        from ..llm.llm_agent import AgentReviewer

        return AgentReviewer(
            index=index,
            agent_batch_size=args.agent_batch_size,
            max_agent_turns=args.max_agent_turns,
            use_database=args.use_database,
            **kwargs,
        )
    return LLMReviewer(**kwargs)


def make_context_builder(index: AssetHierarchyIndex):
    """Hierarchy context (the ground-truth records) attached to every row sent to Claude in hybrid mode."""

    def build(row: dict[str, str]) -> dict[str, Any]:
        floc = normalize_floc(row.get("Functional Location", ""))
        context: dict[str, Any] = {"current_floc": index.floc_context(floc, max_children=8) if floc else {}}
        suggested = normalize_floc(row.get("suggest_functional_location", ""))
        if suggested and suggested != floc:
            context["suggested_floc"] = index.floc_context(suggested, max_children=8)
        equipment = str(row.get("Equipment", "")).strip()
        if equipment and equipment in index.equipment_records:
            record = index.equipment_records[equipment]
            context["equipment_master"] = {k: v for k, v in record.items() if v}
        return context

    return build


def make_suggestion_guard(index: AssetHierarchyIndex):
    """
    Claude / agent Functional Location suggestions on the Equipment sheet must be a real Level 8 FL
    (Inventory 8 in the FL master) or the Level 8 FL derived by find_level8_floc - never an edited string.
    """

    def guard(validator_name: str, row: pd.Series, suggested: str) -> str:
        if validator_name != "functional_location" or not str(row.get("Equipment", "")).strip():
            return ""
        floc = normalize_floc(suggested)
        if index.inventory.get(floc) == "8" and not index.children.get(floc):
            return ""
        derived = index.find_level8_floc(row.get("Functional Location", ""), row.get("Technical IdentNo.", ""), row.get("Object Description", ""))
        if derived and derived["floc"] and normalize_floc(derived["floc"]) == floc:
            return ""
        return f"{floc} is not an Inventory 8 FL in the FL master nor the Level 8 FL derived from the hierarchy"

    return guard


def resolve_mode(args: argparse.Namespace) -> str:
    if args.mode:
        return args.mode
    return "hybrid" if args.use_llm else "deterministic"


def overall_status(row: pd.Series) -> str:
    statuses = [str(value) for value in row]
    if any(status == "Suggest Change" for status in statuses):
        return "Suggest Change"
    if any(status in {"Manual Review", "Invalid Format"} for status in statuses):
        return "Manual Review"
    if statuses and all(status in {"OK", "Skipped"} for status in statuses):
        return "OK"
    return "Missing Evidence"


def write_output(df: pd.DataFrame, output_file: str, mode: str, llm_usage: dict[str, int] | None = None) -> None:
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    export_df = exportable_dataframe(df)
    status_cols = [col for col in df.columns if str(col).startswith("__") and str(col).endswith("_status")]
    llm_usage = llm_usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    summary_row: dict[str, Any] = {"rows": len(export_df)}
    for col in status_cols:
        name = str(col).strip("_").removesuffix("_status")
        summary_row[f"{name}_changes"] = _count_status(df, col, "Suggest Change")
        summary_row[f"{name}_manual_review"] = _count_status(df, col, "Manual Review")
    summary_row.update(
        {
            "duplicate_equipment_rows": duplicate_equipment_rows(export_df),
            "manual_review_rows": int(df[status_cols].apply(lambda row: any(str(v) == "Manual Review" for v in row), axis=1).sum()) if status_cols else 0,
            "mode": mode,
            "langfuse_trace_name": settings.AGENT_NAME if mode != "deterministic" else "",
            "llm_input_tokens": llm_usage.get("input_tokens", 0),
            "llm_output_tokens": llm_usage.get("output_tokens", 0),
            "llm_total_tokens": llm_usage.get("total_tokens", 0),
        }
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="FL_Validated", index=False)
        pd.DataFrame([summary_row]).T.reset_index().rename(columns={"index": "metric", 0: "value"}).to_excel(writer, sheet_name="Run_Summary", index=False)
    style_workbook(path)


def _count_status(df: pd.DataFrame, col: str, status: str) -> int:
    return int((df[col] == status).sum()) if col in df else 0


def duplicate_equipment_rows(df: pd.DataFrame) -> int:
    equipment_col = next((col for col in df.columns if str(col).lower().replace(" ", "") in {"equipment", "equipmentnumber"}), None)
    if not equipment_col:
        return 0
    values = df[equipment_col].fillna("").astype(str).str.strip()
    return int((values.ne("") & values.duplicated(keep=False)).sum())


def style_workbook(path: Path) -> None:
    wb = load_workbook(path)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        headers = {str(ws.cell(1, c).value or ""): c for c in range(1, ws.max_column + 1)}
        for cell in ws[1]:
            header = str(cell.value or "")
            cell.font = Font(bold=True)
            if _is_result_header(header):
                cell.fill = PatternFill("solid", fgColor="FFF2CC")
        for col_idx in range(1, ws.max_column + 1):
            header = str(ws.cell(1, col_idx).value or "")
            letter = get_column_letter(col_idx)
            if header.endswith(("_source", "_evidence")) and _is_result_header(header):
                ws.column_dimensions[letter].width = 50
            elif header.startswith("suggest_"):
                ws.column_dimensions[letter].width = 28
            elif header.endswith("_confidence") and _is_result_header(header):
                ws.column_dimensions[letter].width = 14
            else:
                ws.column_dimensions[letter].width = min(max(len(header) + 4, 12), 26)
        if ws.title == "FL_Validated":
            highlight_rows(ws, headers)
            highlight_duplicate_equipment(ws, headers)
    wb.save(path)


def _is_result_header(header: str) -> bool:
    # Generated columns are lowercase snake_case; original SAP columns are not.
    return header.startswith("suggest_") or (header.endswith(("_confidence", "_source", "_evidence", "_status")) and header.islower())


def highlight_rows(ws, headers: dict[str, int]) -> None:
    groups = []
    for header in headers:
        if header.startswith("suggest_"):
            key = header.removeprefix("suggest_")
            groups.append((header, f"{key}_confidence", f"{key}_source", f"{key}_evidence"))
    accepted = PatternFill("solid", fgColor="E2F0D9")
    low = PatternFill("solid", fgColor="FCE4D6")
    for row_idx in range(2, ws.max_row + 1):
        for suggested_header, confidence_header, source_header, evidence_header in groups:
            suggested_col = headers.get(suggested_header)
            if not suggested_col or not str(ws.cell(row_idx, suggested_col).value or ""):
                continue
            confidence_col = headers.get(confidence_header)
            confidence = str(ws.cell(row_idx, confidence_col).value or "") if confidence_col else ""
            fill = low if confidence == "Low" else accepted
            for header in (suggested_header, confidence_header, source_header, evidence_header):
                col = headers.get(header)
                if col:
                    ws.cell(row_idx, col).fill = fill


def highlight_duplicate_equipment(ws, headers: dict[str, int]) -> None:
    equipment_col = None
    for header, col_idx in headers.items():
        if str(header).lower().replace(" ", "") in {"equipment", "equipmentnumber"}:
            equipment_col = col_idx
            break
    if not equipment_col:
        return
    values: dict[str, list[int]] = {}
    for row_idx in range(2, ws.max_row + 1):
        value = str(ws.cell(row_idx, equipment_col).value or "").strip()
        if value:
            values.setdefault(value, []).append(row_idx)
    fill = PatternFill("solid", fgColor="F4CCCC")
    for rows in values.values():
        if len(rows) <= 1:
            continue
        for row_idx in rows:
            for col_idx in range(1, ws.max_column + 1):
                ws.cell(row_idx, col_idx).fill = fill


def write_checkpoint(df: pd.DataFrame, args: argparse.Namespace, stage: str) -> None:
    if not args.checkpoint:
        return
    checkpoint_dir = Path(args.cache_dir) / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / f"{Path(args.output_file).stem}_{stage}.xlsx"
    exportable_dataframe(df).to_excel(path, index=False)
    logging.info("Checkpoint saved: %s", path)


def exportable_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Original columns + exactly three columns per validated field:
    suggest_<field>, <field>_confidence (High / Medium / Low) and <field>_source.
    """
    output = pd.DataFrame(index=df.index)
    for col in df.columns:
        name = str(col)
        if name.startswith("__"):
            continue
        if name.endswith("_confidence_score"):
            key = name.removesuffix("_confidence_score")
            suggested = df[f"suggest_{key}"].astype(str).str.strip() if f"suggest_{key}" in df.columns else pd.Series("", index=df.index)
            output[f"{key}_confidence"] = [confidence_label(v) if s else "" for v, s in zip(df[col], suggested)]
            continue
        if name.endswith("_evidence"):
            key = name.removesuffix("_evidence")
            if f"suggest_{key}" in df.columns:
                output[f"{key}_source"] = field_sources(df, key, col)
                # Facts behind every suggestion (and the reason for every Manual Review).
                output[f"{key}_evidence"] = [html.unescape(str(value or "")) for value in df[col]]
            continue
        output[col] = df[col]
    return output


def field_sources(df: pd.DataFrame, key: str, evidence_col: str) -> list[str]:
    """Source of each suggested value: the records/standards Claude named, else the rule's source."""
    suggested_col, llm_col = f"suggest_{key}", f"__{key}_llm_source"
    sources = []
    for idx in df.index:
        if not str(df.at[idx, suggested_col] or "").strip():
            sources.append("")
            continue
        llm_source = str(df.at[idx, llm_col] or "").strip() if llm_col in df.columns else ""
        sources.append(html.unescape(llm_source or deterministic_source(df.at[idx, evidence_col])))
    return sources


def load_input_dataframe(args: argparse.Namespace) -> pd.DataFrame:
    if args.input_source == "excel":
        return pd.read_excel(args.input_file, sheet_name=args.input_sheet, dtype=str).fillna("")

    cache = load_pipeline_cache(args.asset_cache_file, False)
    dataset = args.dataset
    if dataset == "auto":
        dataset = infer_dataset(args.input_file, args.output_file)

    key = "equipment_df" if dataset == "equipment" else "fl_df"
    df = cache.get(key)
    if not isinstance(df, pd.DataFrame):
        raise ValueError(
            f"Asset cache does not contain {key}. Run `python -m FL.data.db_connection --refresh` first or use --force-asset-refresh."
        )
    return df.fillna("").astype(str).replace({"None": "", "nan": "", "NaT": ""})


def load_pipeline_cache(asset_cache_file: str, force_refresh: bool) -> dict:
    if force_refresh or not Path(asset_cache_file).exists():
        return load_asset_cache(force_refresh=force_refresh, cache_file=asset_cache_file)

    with Path(asset_cache_file).open("rb") as file:
        return pickle.load(file)


def infer_dataset(input_file: str, output_file: str) -> str:
    text = f"{input_file} {output_file}".lower()
    if "equipment" in text or "\\eq\\" in text or "/eq/" in text:
        return "equipment"
    return "fl"


def _sheet(value: str) -> int | str:
    """Excel sheet given on the command line: an index ("0") or a sheet name."""
    return int(value) if value.isdigit() else value


def parse_args(default_input: str, default_output: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"{settings.SITE_NAME} Functional Location / Equipment master-data validation and completion."
    )
    parser.add_argument("--input-file", default=default_input)
    parser.add_argument("--output-file", default=default_output)
    parser.add_argument("--input-source", choices=["cache", "excel"], default=settings.INPUT_SOURCE)
    parser.add_argument("--input-sheet", type=_sheet, default=settings.INPUT_SHEET, help="Excel sheet name or index for --input-source excel")
    parser.add_argument("--fl-input-file", default=settings.FL_INPUT_FILE, help="Excel FL sheet when --dataset both (default: --input-file)")
    parser.add_argument("--eq-input-file", default=settings.EQ_INPUT_FILE, help="Excel Equipment sheet when --dataset both (default: --input-file)")
    parser.add_argument(
        "--dataset",
        choices=["both", "fl", "equipment", "auto"],
        default=settings.DATASET,
        help="both = FL sheet and Equipment sheet in one run",
    )
    parser.add_argument("--fl-output-file", default=settings.FL_OUTPUT_FILE, help="Output for the FL sheet when --dataset both")
    parser.add_argument("--eq-output-file", default=settings.EQ_OUTPUT_FILE, help="Output for the Equipment sheet when --dataset both")
    parser.add_argument(
        "--validator",
        choices=["all", "functional_location", "completion", "abc_indicator", "catalog_profile", "technical_ident_no"],
        default="all",
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default=None,
        help="hybrid (default) = rules first; unclear rows go to Claude / agent per FIELD_ROUTE in llm/llm_reviewer.py; deterministic = rules only, no LLM",
    )
    parser.add_argument("--standards-dir", default=settings.STANDARDS_DIR)
    parser.add_argument("--eca-dir", default=settings.ECA_DIR)
    parser.add_argument("--cache-dir", default=settings.CACHE_DIR)
    parser.add_argument("--asset-cache-file", default=settings.ASSET_CACHE_FILE)
    parser.add_argument("--evidence-db", default="", help="Optional SQLite DB containing evidence_records or abc_criticality table")
    parser.add_argument("--rebuild-cache", action="store_true")
    parser.add_argument("--force-asset-refresh", action="store_true")
    parser.add_argument("--no-database", dest="use_database", action="store_false", help="Skip PostgreSQL reference tables and use cached/local evidence only")
    parser.set_defaults(use_database=True)
    parser.add_argument("--checkpoint", action="store_true", help="Save checkpoint Excel files after each validation stage")
    parser.add_argument("--max-pdf-pages", type=int, default=0, help="0 means all PDF pages")
    parser.add_argument("--min-suggest-confidence", type=float, default=0.85)
    parser.add_argument("--min-review-confidence", type=float, default=0.65)
    parser.add_argument("--limit-rows", type=int, default=0)
    parser.add_argument("--use-llm", dest="use_llm", action="store_true", help="Same as --mode hybrid")
    parser.add_argument("--no-llm", dest="use_llm", action="store_false", help="Same as --mode deterministic")
    parser.set_defaults(use_llm=True)
    parser.add_argument("--build-standards-kb", action="store_true", help="Build the Claude-extracted standards KB before writing output")
    parser.add_argument("--rebuild-standards-kb", action="store_true")
    parser.add_argument("--standards-kb-file", default=settings.STANDARDS_KB_FILE)
    parser.add_argument("--standards-kb-max-chunks", type=int, default=0, help="0 means process all standards chunks")
    parser.add_argument("--env-file", default=settings.ENV_FILE, help="dotenv file with FOUNDRY_ANTHROPIC_BASE_URL / FOUNDRY_API_KEY / FOUNDRY_MODEL_DEPLOYMENT")
    parser.add_argument("--model", default=None, help="Override FOUNDRY_MODEL_DEPLOYMENT")
    parser.add_argument("--effort", choices=["low", "medium", "high", "max"], default="medium", help="Claude effort level")
    parser.add_argument("--max-llm-rows", type=int, default=0, help="Cap on rows sent to Claude; 0 = every unclear row")
    parser.add_argument("--llm-batch-size", type=int, default=20)
    parser.add_argument("--llm-parallel-fields", type=int, default=2)
    parser.add_argument("--llm-min-confidence", type=float, default=0.85)
    parser.add_argument("--llm-skip-confidence", type=float, default=0.90, help="Rule results at or above this (High) are final and not sent to Claude")
    parser.add_argument("--llm-include-missing-evidence", action="store_true", help="Slower: also send rows with no deterministic evidence to Claude")
    parser.add_argument("--agent-batch-size", type=int, default=5, help="Rows per agent investigation")
    parser.add_argument("--max-agent-turns", type=int, default=14)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


if __name__ == "__main__":
    main()
