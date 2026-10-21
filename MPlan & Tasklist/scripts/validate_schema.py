import pandas as pd

EXPECTED_FLOC_COLUMNS = [
    "Maintenance Plant", "Functional Location", "FunctLocDescrip.", "User Status",
    "Location", "System status", "Created On", "Main Work Center", "Inventory Number",
    "Superior FunctLoc.", "Changed On", "ABC Indicator",
]

EXPECTED_EQUIPMENT_COLUMNS = [
    "Equipment", "Object Description", "Functional Location", "FunctLocDescrip.",
    "Location", "Technical IdentNo.", "Catalog Profile", "ABC Indicator",
    "System status", "User Status", "Maint. Planner Group", "Main Work Center",
    "Created By", "Maintenance Plant", "Manuf. Serial Number", "ManufDrawingNumber",
    "Manufacturer", "ManufactPartNo.", "Material", "Material Description",
    "Model number", "Created On", "Inventory Number", "Plant",
]

# The 3 primary files (§3) — verified directly against the real files.
EXPECTED_TASK_LIST_GROUP_COLUMNS = [
    "Planning Plant", "Maintenance Plan", "Maintenance Item", "Maint. item text",
    "Functional Location", "FunctLocDescrip.", "Equipment", "Object Description",
    "Order Type", "Maintenance Strategy", "ABC Indicator", "Group", "Group Counter",
    "Maint. Planner Group", "Main Work Center", "Changed On", "Changed By",
    "Created On", "Created By", "Location",
]

EXPECTED_LONG_TEXT_COLUMNS = [
    "PLANT", "STRATEGY", "TLTYPE", "TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO",
    "TLNODE", "TLCOUNT", "CTRLKEY", "OPWKCEN", "OPDESC", "WORK", "WORK_UNIT",
    "PERSON", "DURATION", "DURATION_UNIT", "ACTTYPE", "SUIT", "FREQUENCY",
    "CA10TXT", "SO10TXT", "TEXTTITLE", "FORMAT", "LONGTEXT",
]

EXPECTED_MPLAN_COLUMNS = [
    "maintenance_plan", "task_list", "pm_planner_group", "main_work_center",
    "no_of_equipment", "equipment_with_plan_status", "equipment_with_rtof_status",
    "equipment_with_mplan_defined", "mplan_completion_pct",
]


class SchemaValidationError(Exception):
    pass


def _validate(df: pd.DataFrame, expected_columns: list[str], source_name: str) -> None:
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise SchemaValidationError(
            f"{source_name} is missing expected columns: {missing}. "
            "The source file's schema no longer matches the documented baseline "
            "(§3/§4a of the architecture) — halt and re-confirm before proceeding "
            "rather than let a pain-point function fail with a confusing error deep in the pipeline."
        )


def validate_floc_schema(df: pd.DataFrame) -> None:
    _validate(df, EXPECTED_FLOC_COLUMNS, "Agent A FLOC output")


def validate_equipment_schema(df: pd.DataFrame) -> None:
    _validate(df, EXPECTED_EQUIPMENT_COLUMNS, "Agent A Equipment output")


def validate_task_list_group_schema(df: pd.DataFrame) -> None:
    _validate(df, EXPECTED_TASK_LIST_GROUP_COLUMNS, "Bokor Task List Group.xlsx")


def validate_long_text_schema(df: pd.DataFrame) -> None:
    _validate(df, EXPECTED_LONG_TEXT_COLUMNS, "Bokor Long Text_Aug26_LATEST.xlsm (post WORK_UNIT/DURATION_UNIT rename)")


def validate_mplan_schema(df: pd.DataFrame) -> None:
    _validate(df, EXPECTED_MPLAN_COLUMNS, "MPLAN BOKOR AUG26.xlsx (post positional column assignment)")
