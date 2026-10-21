"""
Ad-hoc viewer for the Knowledge Graph's core PM entities: Equipment,
FunctionalLocation, MaintenancePlan/MaintenanceItem, and TaskList.

Prints each node type's real columns, row count, and a sample of rows —
plus the real linking edges between them (FOR_EQUIPMENT,
FOR_FUNCTIONAL_LOCATION, USES_TASK_LIST, HAS_ITEM) — so you can see the
actual shape of the data without writing a one-off query each time.

Usage:
    python scripts/view_kg_data.py                  # summary + sample rows for everything
    python scripts/view_kg_data.py --rows 20         # show more/fewer sample rows
    python scripts/view_kg_data.py --type Equipment  # only one node type
    python scripts/view_kg_data.py --search 10012345 # find this natural_key across all 4 types + show its edges
    python scripts/view_kg_data.py --csv-dir out/    # also dump each full table to CSV
    python scripts/view_kg_data.py --excel out/kg_data.xlsx  # one readable workbook, one sheet per type/edge, FULL data
"""

import argparse
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from scripts import kg_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NODE_TYPES = ["Equipment", "FunctionalLocation", "MaintenancePlan", "MaintenanceItem", "TaskList"]

EDGE_RELATIONSHIPS = [
    "FOR_EQUIPMENT",           # MaintenanceItem -> Equipment
    "FOR_FUNCTIONAL_LOCATION", # MaintenanceItem -> FunctionalLocation
    "USES_TASK_LIST",          # MaintenanceItem -> TaskList
    "HAS_ITEM",                # MaintenancePlan -> MaintenanceItem
]


def _print_table_summary(name: str, df: pd.DataFrame, sample_rows: int) -> None:
    print(f"\n{'=' * 70}")
    print(f"{name}  —  {df.shape[0]} rows, {df.shape[1]} columns")
    print("=" * 70)
    print("Columns:", ", ".join(df.columns.tolist()))
    if df.empty:
        print("(no rows)")
        return
    with pd.option_context("display.max_columns", None, "display.width", 200, "display.max_colwidth", 40):
        print(df.head(sample_rows).to_string())


def _print_edge_summary(name: str, df: pd.DataFrame, sample_rows: int) -> None:
    print(f"\n--- edge: {name}  ({df.shape[0]} edges) ---")
    if df.empty:
        print("(no edges)")
        return
    print(df.head(sample_rows).to_string())


def _sheet_name(name: str) -> str:
    # Excel sheet names: max 31 chars, no : \ / ? * [ ]
    cleaned = re.sub(r"[:\\/?*\[\]]", "_", name)
    return cleaned[:31]


def _write_readable_sheet(writer: "pd.ExcelWriter", sheet_name: str, df: pd.DataFrame) -> None:
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    sheet_name = _sheet_name(sheet_name)
    if df.empty:
        df = pd.DataFrame({"(no rows)": []})
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    ws = writer.sheets[sheet_name]

    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    for col_idx, col_name in enumerate(df.columns, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True)
        cell.fill = header_fill
        max_len = max(
            [len(str(col_name))] + [len(str(v)) for v in df.iloc[:, col_idx - 1].head(500)]
        )
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(max_len + 2, 10), 60)
    ws.freeze_panes = "A2"
    if ws.max_row >= 1 and ws.max_column >= 1:
        last_col = get_column_letter(ws.max_column)
        ws.auto_filter.ref = f"A1:{last_col}{ws.max_row}"


def write_excel(conn, node_types: list[str], excel_path: str) -> None:
    import openpyxl

    out_path = Path(excel_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    overview_rows = []
    tables: dict[str, pd.DataFrame] = {}
    for node_type in node_types:
        df = kg_client.get_full_table_for_type(conn, node_type)
        tables[node_type] = df
        overview_rows.append({"Sheet": node_type, "Kind": "Node type", "Rows": df.shape[0], "Columns": df.shape[1]})
        print(f"  fetched {node_type}: {df.shape[0]} rows, {df.shape[1]} columns")

    edges: dict[str, pd.DataFrame] = {}
    if len(node_types) == len(NODE_TYPES):
        for relationship in EDGE_RELATIONSHIPS:
            edge_df = kg_client.get_edges_by_relationship(conn, relationship)
            edges[relationship] = edge_df
            overview_rows.append({"Sheet": relationship, "Kind": "Edge (relationship)", "Rows": edge_df.shape[0], "Columns": edge_df.shape[1]})
            print(f"  fetched edge {relationship}: {edge_df.shape[0]} rows")

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        _write_readable_sheet(writer, "Overview", pd.DataFrame(overview_rows))
        for node_type, df in tables.items():
            _write_readable_sheet(writer, node_type, df)
        for relationship, edge_df in edges.items():
            _write_readable_sheet(writer, f"edge_{relationship}", edge_df)

    print(f"\nWrote {out_path} — {1 + len(tables) + len(edges)} sheets.")


def show_all(conn, node_types: list[str], sample_rows: int, csv_dir: str | None) -> None:
    for node_type in node_types:
        df = kg_client.get_full_table_for_type(conn, node_type)
        _print_table_summary(node_type, df, sample_rows)
        if csv_dir:
            out_path = Path(csv_dir) / f"{node_type}.csv"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_path, index=False)
            print(f"  -> wrote {out_path} ({df.shape[0]} rows)")

    if len(node_types) == len(NODE_TYPES):
        print(f"\n{'=' * 70}")
        print("EDGES (relationships linking the above node types)")
        print("=" * 70)
        for relationship in EDGE_RELATIONSHIPS:
            edges = kg_client.get_edges_by_relationship(conn, relationship)
            _print_edge_summary(relationship, edges, sample_rows)
            if csv_dir:
                out_path = Path(csv_dir) / f"edge_{relationship}.csv"
                edges.to_csv(out_path, index=False)
                print(f"  -> wrote {out_path} ({edges.shape[0]} rows)")


def search(conn, natural_key: str) -> None:
    print(f"Searching for natural_key = {natural_key!r} across {', '.join(NODE_TYPES)} ...")
    found_node_ids: dict[str, str] = {}
    for node_type in NODE_TYPES:
        nodes = kg_client.get_nodes_by_type(conn, node_type)
        match = nodes[nodes["natural_key"].astype(str) == str(natural_key)]
        if not match.empty:
            node_id = match.iloc[0]["node_id"]
            found_node_ids[node_type] = node_id
            props = kg_client.get_properties_for_type(conn, node_type)
            prop_row = props[props["node_id"] == node_id]
            print(f"\nFound as {node_type} (node_id={node_id}):")
            if not prop_row.empty:
                with pd.option_context("display.max_columns", None, "display.width", 200):
                    print(prop_row.to_string(index=False))

    if not found_node_ids:
        print("Not found in any node type — check the natural_key value.")
        return

    print(f"\n{'=' * 70}")
    print("Edges touching this node")
    print("=" * 70)
    for relationship in EDGE_RELATIONSHIPS:
        edges = kg_client.get_edges_by_relationship(conn, relationship)
        for node_type, node_id in found_node_ids.items():
            as_source = edges[edges["source_id"] == node_id]
            as_target = edges[edges["target_id"] == node_id]
            if not as_source.empty:
                print(f"\n{relationship}: {node_type} ({node_id}) --> {len(as_source)} target(s)")
                print(as_source.to_string(index=False))
            if not as_target.empty:
                print(f"\n{relationship}: {len(as_target)} source(s) --> {node_type} ({node_id})")
                print(as_target.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--type", choices=NODE_TYPES, help="Only show this one node type (skips edges).")
    parser.add_argument("--rows", type=int, default=10, help="Sample rows to print per table/edge (default 10).")
    parser.add_argument("--search", metavar="NATURAL_KEY", help="Find one natural_key across all node types and show its real edges.")
    parser.add_argument("--csv-dir", metavar="DIR", help="Also write each full table to a CSV file in this directory.")
    parser.add_argument("--excel", metavar="PATH", help="Write one readable Excel workbook (one sheet per node type/edge) to this path, e.g. out/kg_data.xlsx.")
    args = parser.parse_args()

    conn = kg_client.get_connection()
    try:
        if args.search:
            search(conn, args.search)
        elif args.excel:
            node_types = [args.type] if args.type else NODE_TYPES
            write_excel(conn, node_types, args.excel)
        else:
            node_types = [args.type] if args.type else NODE_TYPES
            show_all(conn, node_types, args.rows, args.csv_dir)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
