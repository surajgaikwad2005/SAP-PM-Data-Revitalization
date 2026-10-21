
from pathlib import Path

import pandas as pd
import yaml    
from dotenv import load_dotenv
import os

from evidence_connectors.pitstops_connector import discipline_duration_ranges, load_pitstops_tasklists
from logging_config import get_logger
from scripts import kg_client
from output_writer import write_findings_summary_workbook, write_recommendations_workbook
from scripts.normalize import classify_mplan_rows, normalize_long_text, parse_mplan_task_list_key
from scripts.validate_schema import (
    validate_equipment_schema,
    validate_floc_schema,
    validate_long_text_schema,
    validate_mplan_schema,
    validate_task_list_group_schema,
)
from validation import Finding, run_pp1, run_pp2, run_pp3, run_pp4, run_pp5, run_pp6, run_pp7

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

logger = get_logger()


def _split_group_counter(natural_key):
    if natural_key is None or (isinstance(natural_key, float) and pd.isna(natural_key)):
        return None, None
    group, _, counter = str(natural_key).rpartition("-")
    return (group or None), (counter or None)


def _first_real(series: pd.Series):
    non_null = series.dropna()
    return non_null.iloc[0] if len(non_null) else None


def load_settings() -> dict:
    load_dotenv(BASE_DIR / ".env")
    return {
        "platform_codes": yaml.safe_load((CONFIG_DIR / "platform_code_prefixes.yaml").read_text())["platform_codes"],
        "work_centre_families": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["planner_groups"],
        "multi_work_centre_variants": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["multi_work_centre_variants"],
        "explicit_discipline_codes": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["explicit_discipline_codes"],
        "suffix_discipline_patterns": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["suffix_discipline_patterns"],
        "unit_rules": yaml.safe_load((CONFIG_DIR / "unit_rules.yaml").read_text()),
        "thresholds": yaml.safe_load((CONFIG_DIR / "thresholds.yaml").read_text()),
        "llm_provider": os.environ.get("AGENT_C_LLM_PROVIDER", "azure_openai"),
    }


def get_chat_model(llm_provider: str):
    if llm_provider == "azure_openai":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
    if llm_provider == "azure_foundry_claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=os.environ.get("AZURE_FOUNDRY_CLAUDE_API_KEY", ""),
            base_url=os.environ.get("AZURE_FOUNDRY_CLAUDE_ENDPOINT", ""),
            model=os.environ.get("AZURE_FOUNDRY_CLAUDE_DEPLOYMENT", ""),
        )
    raise ValueError(
        f"unknown llm_provider {llm_provider!r}; expected 'azure_openai' or 'azure_foundry_claude'"
    )


def build_agent_c(chat_model, kg_conn=None):
    from deepagents import create_deep_agent

    ground_truth_dir = BASE_DIR / "ground_truth_cache"

    def read_ground_truth(pain_point_file: str) -> str:
        """Read the cited ground-truth excerpt for one pain point (e.g. 'PP04_Duplicate_TaskList.md') from ground_truth_cache/."""
        path = ground_truth_dir / pain_point_file
        if not path.exists():
            return f"No ground truth cache found at {pain_point_file}."
        return path.read_text(encoding="utf-8")

    def check_oreda_applicability() -> str:
        """Check whether the KG's oreda_data table offers any usable signal for PP5's planned-manhours check."""
        from evidence_connectors.oreda_connector import is_oreda_applicable_to_pp5

        if kg_conn is None:
            return "applicable=unknown; no Knowledge Graph connection was supplied to this agent."
        applicable, reason = is_oreda_applicable_to_pp5(kg_conn)
        return f"applicable={applicable}; {reason}"

    tools = [read_ground_truth, check_oreda_applicability]
    system_prompt = (BASE_DIR / "system_prompt.md").read_text(encoding="utf-8")
    return create_deep_agent(tools=tools, system_prompt=system_prompt, model=chat_model)


def read_task_list_group(conn) -> pd.DataFrame:
    mi_df = kg_client.get_full_table_for_type(conn, "MaintenanceItem")

    for_floc = kg_client.get_edges_by_relationship(conn, "FOR_FUNCTIONAL_LOCATION").rename(
        columns={"source_id": "node_id", "target_id": "floc_node_id"}
    )
    for_equipment = kg_client.get_edges_by_relationship(conn, "FOR_EQUIPMENT").rename(
        columns={"source_id": "node_id", "target_id": "equipment_node_id"}
    )
    uses_task_list = kg_client.get_edges_by_relationship(conn, "USES_TASK_LIST").rename(
        columns={"source_id": "node_id", "target_id": "task_list_node_id"}
    )
    has_item = kg_client.get_edges_by_relationship(conn, "HAS_ITEM").rename(
        columns={"source_id": "plan_node_id", "target_id": "node_id"}
    )

    mi_df = (
        mi_df
        .merge(for_floc, on="node_id", how="left")
        .merge(for_equipment, on="node_id", how="left")
        .merge(uses_task_list, on="node_id", how="left")
        .merge(has_item, on="node_id", how="left")
    )

    floc_natural_keys = kg_client.get_nodes_by_type(conn, "FunctionalLocation").rename(
        columns={"node_id": "floc_node_id", "natural_key": "floc_natural_key"}
    )
    equipment_natural_keys = kg_client.get_nodes_by_type(conn, "Equipment").rename(
        columns={"node_id": "equipment_node_id", "natural_key": "equipment_natural_key"}
    )
    task_list_natural_keys = kg_client.get_nodes_by_type(conn, "TaskList").rename(
        columns={"node_id": "task_list_node_id", "natural_key": "task_list_natural_key"}
    )
    plan_natural_keys = kg_client.get_nodes_by_type(conn, "MaintenancePlan").rename(
        columns={"node_id": "plan_node_id", "natural_key": "plan_natural_key"}
    )

    mi_df = (
        mi_df
        .merge(floc_natural_keys, on="floc_node_id", how="left")
        .merge(equipment_natural_keys, on="equipment_node_id", how="left")
        .merge(task_list_natural_keys, on="task_list_node_id", how="left")
        .merge(plan_natural_keys, on="plan_node_id", how="left")
    )

    split = mi_df["task_list_natural_key"].apply(_split_group_counter)
    mi_df["Group"] = [s[0] for s in split]
    mi_df["Group Counter"] = [s[1] for s in split]

    return pd.DataFrame({
        "Planning Plant": mi_df.get("planning_plant"),
        "Maintenance Plan": mi_df["plan_natural_key"],
        "Maintenance Item": mi_df["natural_key"],
        "Maint. item text": mi_df.get("maint_item_text"),
        "Functional Location": mi_df["floc_natural_key"],
        "FunctLocDescrip.": mi_df.get("functlocdescrip"),
        "Equipment": mi_df["equipment_natural_key"],
        "Object Description": mi_df.get("object_description"),
        "Order Type": mi_df.get("order_type"),
        "Maintenance Strategy": mi_df.get("maintenance_strategy"),
        "ABC Indicator": mi_df.get("abc_indicator"),
        "Group": mi_df["Group"],
        "Group Counter": mi_df["Group Counter"],
        "Maint. Planner Group": mi_df.get("maint_planner_group"),
        "Main Work Center": mi_df.get("main_work_center"),
        "Changed On": mi_df.get("changed_on"),
        "Changed By": mi_df.get("changed_by"),
        "Created On": mi_df.get("created_on"),
        "Created By": mi_df.get("created_by"),
        "Location": mi_df.get("location"),
    })


def read_pp3_task_list_relationships(conn) -> tuple[dict[str, int], dict[str, int]]:
    task_list_natural_keys = kg_client.get_nodes_by_type(conn, "TaskList").rename(
        columns={"node_id": "task_list_node_id", "natural_key": "task_list_natural_key"}
    )

    has_operation = kg_client.get_edges_by_relationship(conn, "HAS_OPERATION").rename(
        columns={"source_id": "task_list_node_id"}
    )
    operation_counts_by_node = has_operation.groupby("task_list_node_id").size()
    op_count_df = task_list_natural_keys.copy()
    op_count_df["operation_count"] = op_count_df["task_list_node_id"].map(operation_counts_by_node).fillna(0).astype(int)
    task_list_operation_counts = dict(zip(op_count_df["task_list_natural_key"], op_count_df["operation_count"]))

    real_mi_node_ids = set(kg_client.get_properties_for_type(conn, "MaintenanceItem")["node_id"])
    uses_task_list = kg_client.get_edges_by_relationship(conn, "USES_TASK_LIST").rename(
        columns={"source_id": "mi_node_id", "target_id": "task_list_node_id"}
    )
    real_uses = uses_task_list[uses_task_list["mi_node_id"].isin(real_mi_node_ids)]
    real_mi_counts_by_node = real_uses.groupby("task_list_node_id").size()
    mi_count_df = task_list_natural_keys.copy()
    mi_count_df["real_mi_count"] = mi_count_df["task_list_node_id"].map(real_mi_counts_by_node).fillna(0).astype(int)
    task_list_real_mi_counts = dict(zip(mi_count_df["task_list_natural_key"], mi_count_df["real_mi_count"]))

    return task_list_operation_counts, task_list_real_mi_counts


def read_pp1_task_list_equipment(conn) -> dict[str, list[dict]]:
    task_list_natural_keys = kg_client.get_nodes_by_type(conn, "TaskList").rename(
        columns={"node_id": "task_list_node_id", "natural_key": "task_list_natural_key"}
    )
    uses_task_list = kg_client.get_edges_by_relationship(conn, "USES_TASK_LIST").rename(
        columns={"source_id": "mi_node_id", "target_id": "task_list_node_id"}
    )
    mi_natural_keys = kg_client.get_nodes_by_type(conn, "MaintenanceItem").rename(
        columns={"node_id": "mi_node_id", "natural_key": "mi_natural_key"}
    )
    for_equipment = kg_client.get_edges_by_relationship(conn, "FOR_EQUIPMENT").rename(
        columns={"source_id": "mi_node_id", "target_id": "equipment_node_id"}
    )
    for_floc = kg_client.get_edges_by_relationship(conn, "FOR_FUNCTIONAL_LOCATION").rename(
        columns={"source_id": "mi_node_id", "target_id": "floc_node_id"}
    )

    equipment_props = kg_client.get_properties_for_type(conn, "Equipment").rename(
        columns={"node_id": "equipment_node_id"}
    )
    equipment_natural_keys = kg_client.get_nodes_by_type(conn, "Equipment").rename(
        columns={"node_id": "equipment_node_id", "natural_key": "equipment_natural_key"}
    )
    floc_props = kg_client.get_properties_for_type(conn, "FunctionalLocation").rename(
        columns={"node_id": "floc_node_id"}
    )
    floc_natural_keys = kg_client.get_nodes_by_type(conn, "FunctionalLocation").rename(
        columns={"node_id": "floc_node_id", "natural_key": "floc_natural_key"}
    )

    merged = (
        uses_task_list
        .merge(task_list_natural_keys, on="task_list_node_id", how="inner")
        .merge(mi_natural_keys, on="mi_node_id", how="left")
        .merge(for_equipment, on="mi_node_id", how="left")
        .merge(for_floc, on="mi_node_id", how="left")
        .merge(equipment_natural_keys, on="equipment_node_id", how="left")
        .merge(
            equipment_props[["equipment_node_id", "catalog_profile", "system_status"]].rename(
                columns={"system_status": "equipment_system_status"}
            ),
            on="equipment_node_id", how="left",
        )
        .merge(floc_natural_keys, on="floc_node_id", how="left")
        .merge(
            floc_props[["floc_node_id", "system_status"]].rename(
                columns={"system_status": "floc_system_status"}
            ),
            on="floc_node_id", how="left",
        )
    )

    def _platform_prefix(floc_natural_key):
        if floc_natural_key is None or (isinstance(floc_natural_key, float) and pd.isna(floc_natural_key)):
            return None
        return str(floc_natural_key)[:4]

    merged["platform_prefix"] = merged["floc_natural_key"].apply(_platform_prefix)

    result: dict[str, list[dict]] = {}
    for r in merged.to_dict("records"):
        task_list_key = r.get("task_list_natural_key")
        if task_list_key is None or (isinstance(task_list_key, float) and pd.isna(task_list_key)):
            continue
        result.setdefault(task_list_key, []).append({
            "maintenance_item": r.get("mi_natural_key"),
            "equipment_id": r.get("equipment_natural_key"),
            "equipment_system_status": r.get("equipment_system_status"),
            "catalog_profile": r.get("catalog_profile"),
            "floc_natural_key": r.get("floc_natural_key"),
            "floc_system_status": r.get("floc_system_status"),
            "platform_prefix": r.get("platform_prefix"),
        })
    return result


def read_long_text(conn) -> pd.DataFrame:
    top_df = kg_client.get_full_table_for_type(conn, "TaskListOperation")

    def _split_natural_key(natural_key):
        group, counter, op = str(natural_key).split("-")
        return group, counter, op

    split = top_df["natural_key"].apply(_split_natural_key)
    top_df["TLGRP"] = [s[0] for s in split]
    top_df["TLGRPCOUNT"] = [s[1] for s in split]
    top_df["TLOPNO"] = [s[2] for s in split]

    has_operation = kg_client.get_edges_by_relationship(conn, "HAS_OPERATION").rename(
        columns={"source_id": "task_list_node_id", "target_id": "node_id"}
    )
    task_list_props = kg_client.get_properties_for_type(conn, "TaskList").rename(
        columns={"node_id": "task_list_node_id"}
    )
    top_df = top_df.merge(has_operation, on="node_id", how="left").merge(
        task_list_props[["task_list_node_id", "strategy", "tltype"]], on="task_list_node_id", how="left"
    )

    result = pd.DataFrame({
        "PLANT": None,  # no KG equivalent on TaskList/TaskListOperation — left blank, never guessed
        "STRATEGY": top_df.get("strategy"),
        "TLTYPE": top_df.get("tltype"),
        "TLGRP": top_df["TLGRP"],
        "TLGRPCOUNT": top_df["TLGRPCOUNT"],
        "TLOPNO": top_df["TLOPNO"],
        "TLSUBOPNO": "0",  # no sub-operation dimension in the KG's TaskListOperation nodes (see comment above)
        "TLNODE": None,
        "TLCOUNT": None,
        "CTRLKEY": top_df.get("ctrlkey"),
        "OPWKCEN": top_df.get("opwkcen"),
        "OPDESC": top_df.get("opdesc"),
        "WORK": pd.to_numeric(top_df.get("work"), errors="coerce"),
        "WORK_UNIT": top_df.get("work_unit"),
        "PERSON": pd.to_numeric(top_df.get("person"), errors="coerce"),
        "DURATION": pd.to_numeric(top_df.get("duration"), errors="coerce"),
        "DURATION_UNIT": top_df.get("duration_unit"),
        "ACTTYPE": top_df.get("acttype"),
        "SUIT": top_df.get("suit"),
        "FREQUENCY": top_df.get("frequency"),
        "CA10TXT": top_df.get("ca10txt"),
        "SO10TXT": top_df.get("so10txt"),
        "TEXTTITLE": top_df.get("texttitle"),
        "FORMAT": None,
        "LONGTEXT": top_df.get("long_text"),
    })
    return result


def read_mplan_bokor(conn) -> pd.DataFrame:
    tl_df = kg_client.get_full_table_for_type(conn, "TaskList")

    def _rebuild_task_list_string(row):
        tltype = row.get("tltype")
        group, _, counter = str(row["natural_key"]).rpartition("-")
        if not group or not counter or tltype is None:
            return None
        return f"{tltype}{group}{counter.zfill(4)}"

    tl_df["task_list"] = tl_df.apply(_rebuild_task_list_string, axis=1)

    return pd.DataFrame({
        "pm_planning_plant": None,
        "pm_planning_plant_desc": None,
        "maintenance_plant": None,
        "maintenance_plant_desc": None,
        "maintenance_plan": None,  # TaskList nodes have no direct maintenance_plan property in the KG
        "maintenance_plan_desc": None,
        "task_list": tl_df["task_list"],
        "task_list_desc": None,
        "plant": None,
        "plant_desc": None,
        "location": None,
        "location_desc": None,
        "pm_planner_group": tl_df.get("pm_planner_group"),
        "pm_planner_group_desc": None,
        "main_work_center": tl_df.get("main_work_center"),
        "main_work_center_desc": None,
        "abc_indicator": tl_df.get("abc_indicator"),
        "spacer_17": None,
        "no_of_equipment": pd.to_numeric(tl_df.get("no_of_equipment"), errors="coerce"),
        "equipment_with_plan_status": pd.to_numeric(tl_df.get("equipment_with_plan_status_set"), errors="coerce"),
        "equipment_with_rtof_status": pd.to_numeric(tl_df.get("equipment_with_rtof_status"), errors="coerce"),
        "equipment_with_mplan_defined": pd.to_numeric(tl_df.get("equipment_with_mplan_defined"), errors="coerce"),
        "mplan_completion_pct": tl_df.get("mplan_completion"),
        "pct_equipment_with_plan_status": tl_df.get("of_equipment_with_plan_status"),
        "equipment_with_mplan_incl_rtof": pd.to_numeric(tl_df.get("equipment_with_mplan_incl_rtof"), errors="coerce"),
    })


def read_agent_a_floc(conn) -> pd.DataFrame:
    df = kg_client.get_full_table_for_type(conn, "FunctionalLocation")
    return pd.DataFrame({
        "Maintenance Plant": df.get("maintenance_plant"),
        "Functional Location": df["natural_key"],
        "FunctLocDescrip.": df.get("functlocdescrip"),
        "User Status": df.get("user_status"),
        "Location": df.get("location"),
        "System status": df.get("system_status"),
        "Created On": df.get("created_on"),
        "Main Work Center": df.get("main_work_center"),
        "Inventory Number": df.get("inventory_number"),
        "Superior FunctLoc.": None,
        "Changed On": df.get("changed_on"),
        "ABC Indicator": df.get("abc_indicator"),
    })


def read_agent_a_equipment(conn) -> pd.DataFrame:
    df = kg_client.get_full_table_for_type(conn, "Equipment")
    return pd.DataFrame({
        "Equipment": df["natural_key"],
        "Object Description": df.get("object_description"),
        "Functional Location": None,  # resolved separately via FOR_FUNCTIONAL_LOCATION edges where needed
        "FunctLocDescrip.": df.get("functlocdescrip"),
        "Location": df.get("location"),
        "Technical IdentNo.": df.get("technical_identno"),
        "Catalog Profile": df.get("catalog_profile"),
        "ABC Indicator": df.get("abc_indicator"),
        "System status": df.get("system_status"),
        "User Status": df.get("user_status"),
        "Maint. Planner Group": df.get("maint_planner_group"),
        "Main Work Center": df.get("main_work_center"),
        "Created By": df.get("created_by"),
        "Maintenance Plant": df.get("maintenance_plant"),
        "Manuf. Serial Number": df.get("manuf_serial_number"),
        "ManufDrawingNumber": None,  # no KG equivalent found
        "Manufacturer": df.get("manufacturer"),
        "ManufactPartNo.": df.get("manufactpartno"),
        "Material": None,  # no KG equivalent found on Equipment nodes
        "Material Description": None,
        "Model number": df.get("model_number"),
        "Created On": df.get("created_on"),
        "Inventory Number": df.get("inventory_number"),
        "Plant": df.get("maintenance_plant"),
    })


def read_work_order_history(conn) -> pd.DataFrame:
    wo_df = kg_client.get_full_table_for_type(conn, "WorkOrder")

    for_equipment = kg_client.get_edges_by_relationship(conn, "FOR_EQUIPMENT").rename(
        columns={"source_id": "node_id", "target_id": "equipment_node_id"}
    )
    for_floc = kg_client.get_edges_by_relationship(conn, "FOR_FUNCTIONAL_LOCATION").rename(
        columns={"source_id": "node_id", "target_id": "floc_node_id"}
    )
    for_mi = kg_client.get_edges_by_relationship(conn, "FOR_MAINTENANCE_ITEM").rename(
        columns={"source_id": "node_id", "target_id": "mi_node_id"}
    )
    uses_task_list = kg_client.get_edges_by_relationship(conn, "USES_TASK_LIST").rename(
        columns={"source_id": "mi_node_id", "target_id": "task_list_node_id"}
    )

    wo_df = (
        wo_df
        .merge(for_equipment, on="node_id", how="left")
        .merge(for_floc, on="node_id", how="left")
        .merge(for_mi, on="node_id", how="left")
        .merge(uses_task_list, on="mi_node_id", how="left")
    )

    equipment_natural_keys = kg_client.get_nodes_by_type(conn, "Equipment").rename(
        columns={"node_id": "equipment_node_id", "natural_key": "equipment_natural_key"}
    )
    floc_natural_keys = kg_client.get_nodes_by_type(conn, "FunctionalLocation").rename(
        columns={"node_id": "floc_node_id", "natural_key": "floc_natural_key"}
    )
    mi_natural_keys = kg_client.get_nodes_by_type(conn, "MaintenanceItem").rename(
        columns={"node_id": "mi_node_id", "natural_key": "mi_natural_key"}
    )
    task_list_natural_keys = kg_client.get_nodes_by_type(conn, "TaskList").rename(
        columns={"node_id": "task_list_node_id", "natural_key": "task_list_natural_key"}
    )

    wo_df = (
        wo_df
        .merge(equipment_natural_keys, on="equipment_node_id", how="left")
        .merge(floc_natural_keys, on="floc_node_id", how="left")
        .merge(mi_natural_keys, on="mi_node_id", how="left")
        .merge(task_list_natural_keys, on="task_list_node_id", how="left")
    )

    split = wo_df["task_list_natural_key"].apply(_split_group_counter)
    wo_df["Group"] = [s[0] for s in split]
    wo_df["Group Counter"] = [s[1] for s in split]

    return pd.DataFrame({
        "Order": wo_df["natural_key"],
        "Maint. Planner Group": wo_df.get("maint_planner_group"),
        "Maintenance Plant": wo_df.get("maintenance_plant"),
        "Main Work Center": wo_df.get("main_work_center"),
        "Order Type": wo_df.get("order_type"),
        "Basic start date": wo_df.get("basic_start_date"),
        "Basic finish date": wo_df.get("basic_finish_date"),
        "Description": wo_df.get("description"),
        "OLASD": wo_df.get("olasd"),
        "OLAFD": wo_df.get("olafd"),
        "LASD": wo_df.get("lasd"),
        "LAFD": wo_df.get("lafd"),
        "System status": wo_df.get("system_status"),
        "User Status": wo_df.get("user_status"),
        "Location": wo_df.get("location"),
        "SCE FL": wo_df.get("sce_fl"),
        "Inspection Lot": wo_df.get("inspection_lot"),
        "Functional Location": wo_df["floc_natural_key"],
        "Equipment": wo_df["equipment_natural_key"],
        "Entered By": wo_df.get("entered_by"),
        "Created On": wo_df.get("created_on"),
        "Total sum (actual)": pd.to_numeric(wo_df.get("total_sum_actual"), errors="coerce"),
        "Total sum (plan)": pd.to_numeric(wo_df.get("total_sum_plan"), errors="coerce"),
        "Maintenance Plan": wo_df.get("maintenance_plan"),
        "Maintenance Item": wo_df["mi_natural_key"],
        "Group": wo_df["Group"],
        "Group Counter": wo_df["Group Counter"],
    })


def read_timesheet(path: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Data")


def read_jms_work_order(path: str) -> dict[str, pd.DataFrame]:
    return {
        "data": pd.read_excel(path, sheet_name="Data"),
        "operation_line": pd.read_excel(path, sheet_name="Operation Line"),
    }


def read_ppm_work_order(path: str) -> dict[str, pd.DataFrame]:
    return {
        "data": pd.read_excel(path, sheet_name="Data"),
        "operation_line": pd.read_excel(path, sheet_name="Oepration Line"),
    }


def read_equipment_class_master(path: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Sheet1")


def read_maintenance_strategy_master(path: str) -> pd.DataFrame:
    """PP6 Check B (Frequency) — all 13 real Strategy sheets (PCSB21/24/25/27/29/31/33/42/43/44/
    51/52/53), concatenated into one DataFrame of real Package rows (347 total rows)."""
    sheets = pd.read_excel(path, sheet_name=None)
    return pd.concat(sheets.values(), ignore_index=True)


def build_pp1_task_list_summary(normalized_operations: pd.DataFrame) -> pd.DataFrame:
    df = normalized_operations.copy()
    df["TLGRP"] = df["TLGRP"].astype(str)
    df["TLGRPCOUNT"] = df["TLGRPCOUNT"].astype(str)

    grouped = df.groupby(["TLGRP", "TLGRPCOUNT"], sort=False)

    summary = grouped.agg(
        Planning_Plant=("PLANT", _first_real),
        Strategy=("STRATEGY", _first_real),
        TaskList_Type=("TLTYPE", _first_real),
        Operation_Count=("TLOPNO", "nunique"),
        Sample_OPDESC=("OPDESC", _first_real),
        Sample_Work_Center=("OPWKCEN", _first_real),
    ).reset_index()

    return summary.rename(columns={"TLGRP": "Group", "TLGRPCOUNT": "Group Counter"})


def read_bokor_equipment_extract(path: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name="Sheet1")


def _fetch_kg_base_data(kg_conn):
    """STEP 1/2 — fetch Task List Group, Long Text, MPLAN, agent_a, Work Order history from the KG."""
    logger.info("STEP 1/2: fetching Task List Group, Long Text, MPLAN, agent_a, Work Order history from the Knowledge Graph (read-only)")
    task_list_group = read_task_list_group(kg_conn)
    long_text_raw = read_long_text(kg_conn)
    mplan_raw = read_mplan_bokor(kg_conn)
    task_list_operation_counts, task_list_real_mi_counts = read_pp3_task_list_relationships(kg_conn)
    pp1_task_list_equipment = read_pp1_task_list_equipment(kg_conn)
    validate_task_list_group_schema(task_list_group)
    validate_long_text_schema(long_text_raw)
    validate_mplan_schema(mplan_raw)
    logger.info(
        f"fetched from KG: Bokor Task List Group={task_list_group.shape[0]} rows, "
        f"Bokor Long Text={long_text_raw.shape[0]} rows, MPLAN BOKOR={mplan_raw.shape[0]} rows"
    )

    agent_a_floc = read_agent_a_floc(kg_conn)
    agent_a_equipment = read_agent_a_equipment(kg_conn)
    validate_floc_schema(agent_a_floc)
    validate_equipment_schema(agent_a_equipment)
    if "Location" in agent_a_floc.columns:
        agent_a_floc = agent_a_floc[agent_a_floc["Location"] == "BOKOR"]
    if "Location" in agent_a_equipment.columns:
        agent_a_equipment = agent_a_equipment[agent_a_equipment["Location"] == "BOKOR"]

    work_order_history = read_work_order_history(kg_conn)
    if "Location" in work_order_history.columns:
        work_order_history = work_order_history[work_order_history["Location"] == "BOKOR"]
    logger.info(f"fetched from KG: BOKOR_10years Work Order Data={work_order_history.shape[0]} rows")

    return {
        "task_list_group": task_list_group,
        "long_text_raw": long_text_raw,
        "mplan_raw": mplan_raw,
        "task_list_operation_counts": task_list_operation_counts,
        "task_list_real_mi_counts": task_list_real_mi_counts,
        "pp1_task_list_equipment": pp1_task_list_equipment,
        "agent_a_floc": agent_a_floc,
        "agent_a_equipment": agent_a_equipment,
        "work_order_history": work_order_history,
    }


def _load_ground_truth_masters(ground_truth_cache_dir: Path):
    """Equipment Class / Maintenance Strategy masters and PITSTOPS ranges — each optional,
    missing files degrade gracefully (the dependent PP check is skipped, not a hard failure)."""
    equipment_class_master = None
    equipment_extract = None
    equipment_class_master_path = ground_truth_cache_dir / "Equipment_Class_Master.xlsx"
    equipment_extract_path = ground_truth_cache_dir / "Bokor_EQ_List_All.xlsx"
    if equipment_class_master_path.exists():
        equipment_class_master = read_equipment_class_master(str(equipment_class_master_path))
        logger.info(f"fetched: Equipment Class master={equipment_class_master.shape[0]} rows")
    else:
        logger.info(f"PP1 naming/Equipment-Class check skipped: Equipment Class master not found at {equipment_class_master_path}")
    if equipment_extract_path.exists():
        equipment_extract = read_bokor_equipment_extract(str(equipment_extract_path))
        logger.info(f"fetched: Bokor EQ list all={equipment_extract.shape[0]} rows (legacy, only for the old Excel-bridge Check E)")

    maintenance_strategy_master = None
    maintenance_strategy_master_path = ground_truth_cache_dir / "Maintenance_Strategy_Master.xlsx"
    if maintenance_strategy_master_path.exists():
        maintenance_strategy_master = read_maintenance_strategy_master(str(maintenance_strategy_master_path))
        logger.info(f"fetched: Maintenance Strategy master={maintenance_strategy_master.shape[0]} rows (13 sheets)")
    else:
        logger.info(f"PP6 Frequency check skipped: Maintenance Strategy master not found at {maintenance_strategy_master_path}")

    pitstops_dir = ground_truth_cache_dir / "pitstops"
    pitstops_ranges = None
    if pitstops_dir.exists():
        pitstops_files = [str(p) for p in pitstops_dir.glob("*.xlsx")]
        if pitstops_files:
            pitstops_df = load_pitstops_tasklists(pitstops_files)
            pitstops_ranges = discipline_duration_ranges(pitstops_df)

    return {
        "equipment_class_master": equipment_class_master,
        "equipment_extract": equipment_extract,
        "maintenance_strategy_master": maintenance_strategy_master,
        "pitstops_ranges": pitstops_ranges,
    }


def _compute_pp5_historical_matches(ground_truth_cache_dir: Path, long_text_raw, task_list_group, work_order_history):
    """PP5 Tier-2 evidence — real historical Work Order/timesheet/JMS matching. Returns None when the
    required source files are not present (PP5 then runs with order-level evidence only)."""
    timesheet_2024_path = ground_truth_cache_dir / "Timesheet_BOKOR_2024.xlsx"
    timesheet_2025_path = ground_truth_cache_dir / "Timesheet_BOKOR_2025.xlsx"
    jms_work_order_path = ground_truth_cache_dir / "M014_Bokor_Non_PPM_Work_Order_2020_2025.xlsx"
    ppm_work_order_path = ground_truth_cache_dir / "BOKOR_PPM_Listing_2016_2025.xlsx"
    if not (timesheet_2024_path.exists() and timesheet_2025_path.exists() and jms_work_order_path.exists()):
        return None

    from scripts.historical_matching import (
        aggregate_timesheet_hours,
        extract_jms_actual_hours,
        match_operations_to_history,
        reconcile_actual_hours,
        split_general_receiver,
        strip_timesheet_summary_row,
    )

    ts_2024 = strip_timesheet_summary_row(read_timesheet(str(timesheet_2024_path)))
    ts_2025 = strip_timesheet_summary_row(read_timesheet(str(timesheet_2025_path)))
    timesheet_combined = pd.concat([ts_2024, ts_2025], ignore_index=True)
    timesheet_hours = aggregate_timesheet_hours(split_general_receiver(timesheet_combined))

    jms = read_jms_work_order(str(jms_work_order_path))

    ppm_data = pd.DataFrame({"Order": [], "Group": [], "Group Counter": []})
    ppm_operation_line = pd.DataFrame({"Order": [], "Activity": [], "Actual work": [], "Control Key": [], "Op. Short Text": []})
    if ppm_work_order_path.exists():
        ppm = read_ppm_work_order(str(ppm_work_order_path))
        jms_orders = set(jms["data"]["Order"].astype(str))
        ppm_data = ppm["data"][~ppm["data"]["Order"].astype(str).isin(jms_orders)]
        ppm_operation_line = ppm["operation_line"][~ppm["operation_line"]["Order"].astype(str).isin(jms_orders)]
        logger.info(
            f"fetched: BOKOR PPM Listing={ppm['data'].shape[0]} orders "
            f"({ppm_data.shape[0]} new after deduping against Non-PPM Orders)"
        )

    jms_hours = extract_jms_actual_hours(jms["operation_line"])
    ppm_hours = extract_jms_actual_hours(ppm_operation_line)
    reconciled_hours = reconcile_actual_hours(
        timesheet_hours, pd.concat([jms_hours, ppm_hours], ignore_index=True)
    )

    op_descriptions = pd.concat([jms["operation_line"], ppm_operation_line], ignore_index=True).rename(
        columns={"Order": "order", "Activity": "operation", "Op. Short Text": "description"}
    )[["order", "operation", "description"]]

    historical_matches = match_operations_to_history(
        normalize_long_text(long_text_raw),
        task_list_group,
        {
            "10yr": work_order_history if work_order_history is not None else pd.DataFrame({"Order": [], "Group": [], "Group Counter": []}),
            "jms": pd.concat([jms["data"], ppm_data], ignore_index=True),
        },
        reconciled_hours,
        op_descriptions,
    )
    logger.info(f"computed: PP5 historical-benchmark matching, {historical_matches.shape[0]} operations evaluated")
    return historical_matches


def _build_pp1_task_list_summary(normalized_operations, task_list_group):
    """STEP 3 — the PP1 output-sheet Task-List summary, merged with per-Group aggregates from
    the raw Task List Group bridge (one row per real Group+Group Counter)."""
    pp1_task_list_summary = build_pp1_task_list_summary(normalized_operations)
    logger.info(
        f"built: PP1 output-sheet Task-List summary (KG-derived)={pp1_task_list_summary.shape[0]} rows "
        "(one per real Group+Group Counter)"
    )

    tlg = task_list_group.copy()
    tlg["Group"] = tlg["Group"].astype(str)
    tlg["Group Counter"] = tlg["Group Counter"].astype(str)
    tlg_grouped = tlg.groupby(["Group", "Group Counter"], sort=False)

    tlg_summary = tlg_grouped.agg(
        TLG_Planning_Plant=("Planning Plant", _first_real),
        TLG_Maintenance_Plan=("Maintenance Plan", _first_real),
        TLG_Maintenance_Item=("Maintenance Item", _first_real),
        TLG_Maint_Item_Text=("Maint. item text", _first_real),
        TLG_Functional_Location=("Functional Location", _first_real),
        TLG_FunctLocDescrip=("FunctLocDescrip.", _first_real),
        TLG_Equipment=("Equipment", _first_real),
        TLG_Object_Description=("Object Description", _first_real),
        TLG_Order_Type=("Order Type", _first_real),
        TLG_Maintenance_Strategy=("Maintenance Strategy", _first_real),
        TLG_ABC_Indicator=("ABC Indicator", _first_real),
        TLG_Maint_Planner_Group=("Maint. Planner Group", _first_real),
        TLG_Main_Work_Center=("Main Work Center", _first_real),
        TLG_Location=("Location", _first_real),
        TLG_Linked_MI_Count=("Maintenance Item", "nunique"),
        TLG_Distinct_Equipment_Count=("Equipment", "nunique"),
    ).reset_index()

    pp1_task_list_summary = pp1_task_list_summary.merge(
        tlg_summary, on=["Group", "Group Counter"], how="left"
    )
    matched_count = pp1_task_list_summary["TLG_Maintenance_Item"].notna().sum()
    logger.info(
        f"merged: PP1 output-sheet Task-List-Group-derived columns matched for "
        f"{matched_count}/{pp1_task_list_summary.shape[0]} rows"
    )
    return pp1_task_list_summary


def _match_jms_manhours(ground_truth_cache_dir: Path, normalized_operations):
    jms_manhours_cache_path = ground_truth_cache_dir / "PP05_JMS_ManHours.csv"
    if not jms_manhours_cache_path.exists():
        return None

    from scripts.jms_workpack_matching import match_jms_to_operations

    jms_manhours_extraction = pd.read_csv(jms_manhours_cache_path, dtype=str, keep_default_na=False)
    matched_jms_rows = match_jms_to_operations(jms_manhours_extraction, normalized_operations)
    logger.info(
        f"computed: PP5 JMS workpack matching, {len(jms_manhours_extraction)} extracted rows -> "
        f"{matched_jms_rows['evidence_status'].value_counts().to_dict()}"
    )
    return matched_jms_rows


def _run_all_pain_points(kg, masters, normalized_operations, pp5_evidence, settings, batch_size, agent_c, kg_conn) -> list[Finding]:
    task_list_group = kg["task_list_group"]
    findings: list[Finding] = []

    pp1_findings = run_pp1(
        task_list_group, settings["platform_codes"],
        reuse_threshold=settings["thresholds"]["pp1"]["reused_prefix_min_occurrences"],
        batch_size=batch_size,
        work_order_history=kg["work_order_history"],
        agent_a_equipment=kg["agent_a_equipment"],
        historical_usage_confidence=settings["thresholds"]["pp1"]["historical_usage_confidence"],
        sce_naming_confidence=settings["thresholds"]["pp1"]["sce_naming_confidence"],
        inconsistent_applicability_confidence=settings["thresholds"]["pp1"]["inconsistent_applicability_confidence"],
        equipment_class_master=masters["equipment_class_master"],
        equipment_extract=masters["equipment_extract"],
        equipment_class_high_confidence=settings["thresholds"]["pp1"]["equipment_class_high_confidence"],
        equipment_class_family_match_confidence=settings["thresholds"]["pp1"]["equipment_class_family_match_confidence"],
        equipment_class_non_standard_scheme_confidence=settings["thresholds"]["pp1"]["equipment_class_non_standard_scheme_confidence"],
        pp1_task_list_equipment=kg["pp1_task_list_equipment"],
        pp1_kg_medium_confidence=settings["thresholds"]["pp1"]["pp1_kg_medium_confidence"],
        pp1_kg_review_confidence=settings["thresholds"]["pp1"]["pp1_kg_review_confidence"],
        pp1_historical_review_confidence=settings["thresholds"]["pp1"]["pp1_historical_review_confidence"],
    )
    logger.info(f"PP1 complete: {len(pp1_findings)} findings")
    findings += pp1_findings

    if agent_c is not None:
        pp2_findings = run_pp2(
            normalized_operations, settings["work_centre_families"], agent_c,
            batch_size=batch_size,
        )
        logger.info(f"PP2 complete: {len(pp2_findings)} findings")
        findings += pp2_findings
    else:
        logger.info("PP2 skipped: no agent_c supplied")

    pp3_findings = run_pp3(
        kg["task_list_operation_counts"], kg["task_list_real_mi_counts"],
        batch_size=batch_size,
    )
    logger.info(f"PP3 complete: {len(pp3_findings)} findings")
    findings += pp3_findings

    pp4_findings = run_pp4(
        normalized_operations, task_list_group,
        agent_c=agent_c,
        batch_size=batch_size,
    )
    logger.info(f"PP4 complete: {len(pp4_findings)} findings")
    findings += pp4_findings

    pp5_findings = run_pp5(
        normalized_operations,
        settings["unit_rules"]["valid_work_unit"],
        settings["unit_rules"]["valid_duration_unit"],
        masters["pitstops_ranges"],
        work_tolerance=settings["thresholds"]["pp5"]["work_tolerance"],
        agent_c=agent_c,
        batch_size=batch_size,
        historical_matches=pp5_evidence["historical_matches"],
        min_comparable_executions=settings["thresholds"]["pp5"]["min_comparable_executions"],
        historical_benchmark_confidence=settings["thresholds"]["pp5"]["historical_benchmark_confidence"],
        oreda_conn=kg_conn,
        matched_jms_rows=pp5_evidence["matched_jms_rows"],
        task_list_group=task_list_group,
    )
    logger.info(f"PP5 complete: {len(pp5_findings)} findings")
    findings += pp5_findings

    pp6_findings = run_pp6(
        task_list_group, normalized_operations, batch_size=batch_size,
        maintenance_strategy_master=masters["maintenance_strategy_master"],
        work_order_history=kg["work_order_history"],
    )
    logger.info(f"PP6 complete: {len(pp6_findings)} findings")
    findings += pp6_findings

    pp7_findings = run_pp7(task_list_group, batch_size=batch_size)
    logger.info(f"PP7 complete: {len(pp7_findings)} findings")
    findings += pp7_findings

    return findings


def _write_outputs(output_path: Path, task_list_group, normalized_operations, pp1_task_list_summary, findings: list[Finding]):
    logger.info(f"STEP 6: writing output, {len(findings)} total findings")
    sources = {
        "task_list_group": task_list_group,
        "normalized_operations": normalized_operations,
        "pp1_task_list_summary": pp1_task_list_summary,
    }
    records_checked = {
        "PP1": normalized_operations.shape[0],
        "PP2": task_list_group.shape[0],
        "PP3": normalized_operations.shape[0],
        "PP4": normalized_operations.shape[0],
        "PP5": normalized_operations.shape[0],
        "PP6": task_list_group.shape[0],
        "PP7": task_list_group.shape[0],
    }
    write_recommendations_workbook(sources, findings, str(output_path / "SAP_PM_Agent_Recommendations.xlsx"))
    summary = write_findings_summary_workbook(
        sources, findings, str(output_path / "SAP_PM_Agent_Findings_Summary.xlsx"), records_checked
    )
    for pain_point, row in summary.items():
        logger.info(
            f"STEP 6: {pain_point} — checked={row['Records_Checked']}, findings={row['Findings']}, "
            f"suggestions={row['Suggestions_Generated']} "
            f"(High={row['High_Confidence']}, Medium={row['Medium_Confidence']}, Low={row['Low_Confidence']}), "
            f"review_required={row['Review_Required']}"
        )
    logger.info("STEP 6: output written")


def run_pipeline(
    input_dir: str, output_dir: str, agent_c=None, kg_conn=None,
) -> list[Finding]:
    settings = load_settings()
    ground_truth_cache_dir = BASE_DIR / "ground_truth_cache"
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    batch_size = settings["thresholds"].get("batch_size", 500)

    if kg_conn is None:
        kg_conn = kg_client.get_connection()

    kg = _fetch_kg_base_data(kg_conn)
    masters = _load_ground_truth_masters(ground_truth_cache_dir)
    historical_matches = _compute_pp5_historical_matches(
        ground_truth_cache_dir, kg["long_text_raw"], kg["task_list_group"], kg["work_order_history"]
    )

    logger.info("STEP 3: normalizing (§5.0)")
    normalized_operations = normalize_long_text(kg["long_text_raw"])
    known_tlgrps = set(normalized_operations["TLGRP"].tolist()) | set(kg["task_list_group"]["Group"].tolist())
    mplan_with_key = parse_mplan_task_list_key(kg["mplan_raw"], known_tlgrps)
    mplan_detail_rows, _mplan_aggregate_rows = classify_mplan_rows(mplan_with_key)
    logger.info(
        f"normalized: {normalized_operations.shape[0]} distinct logical operations, "
        f"{mplan_detail_rows.shape[0]} MPLAN detail rows"
    )

    pp1_task_list_summary = _build_pp1_task_list_summary(normalized_operations, kg["task_list_group"])
    matched_jms_rows = _match_jms_manhours(ground_truth_cache_dir, normalized_operations)
    pp5_evidence = {"historical_matches": historical_matches, "matched_jms_rows": matched_jms_rows}

    findings = _run_all_pain_points(
        kg, masters, normalized_operations, pp5_evidence, settings, batch_size, agent_c, kg_conn
    )
    _write_outputs(output_path, kg["task_list_group"], normalized_operations, pp1_task_list_summary, findings)

    return findings


if __name__ == "__main__":
    settings = load_settings()
    chat_model = get_chat_model(settings["llm_provider"])
    kg_conn = kg_client.get_connection()
    agent_c = build_agent_c(chat_model, kg_conn=kg_conn)
    results = run_pipeline(str(BASE_DIR / "input"), str(BASE_DIR / "output"), agent_c=agent_c, kg_conn=kg_conn)
    print(
        f"Agent C run complete: {len(results)} findings written to "
        "output/SAP_PM_Agent_Recommendations.xlsx and output/SAP_PM_Agent_Findings_Summary.xlsx"
    )
