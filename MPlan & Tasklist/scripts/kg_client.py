import os

import pandas as pd
import psycopg
import sqlalchemy
from azure.identity import AzureCliCredential

TOKEN_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def get_connection() -> psycopg.Connection:
    credential = AzureCliCredential()
    token = credential.get_token(TOKEN_SCOPE)
    return psycopg.connect(
        host=os.environ["KG_HOST"],
        port=int(os.environ.get("KG_PORT", "5432")),
        dbname=os.environ["KG_DATABASE"],
        user=os.environ["KG_USERNAME"],
        password=token.token,
        sslmode="require",
    )


def _as_sqlalchemy_engine(conn: psycopg.Connection) -> sqlalchemy.engine.Engine:
    return sqlalchemy.create_engine(
        "postgresql+psycopg://", creator=lambda: conn, poolclass=sqlalchemy.pool.StaticPool
    )


def get_nodes_by_type(conn: psycopg.Connection, node_type: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT node_id, natural_key FROM nodes WHERE node_type = %(node_type)s",
        _as_sqlalchemy_engine(conn), params={"node_type": node_type},
    )


def get_properties_for_type(conn: psycopg.Connection, node_type: str) -> pd.DataFrame:
    long_df = pd.read_sql_query(
        """
        SELECT np.node_id, np.property_name, np.value_text, np.value_num, np.value_date
        FROM node_properties np
        JOIN nodes n ON n.node_id = np.node_id
        WHERE n.node_type = %(node_type)s
        """,
        _as_sqlalchemy_engine(conn), params={"node_type": node_type},
    )
    if long_df.empty:
        return pd.DataFrame({"node_id": pd.Series(dtype="object")})

    def _coalesce(row):
        if pd.notna(row["value_text"]):
            return row["value_text"]
        if pd.notna(row["value_num"]):
            return row["value_num"]
        if pd.notna(row["value_date"]):
            value = row["value_date"]
            if hasattr(value, "tzinfo") and value.tzinfo is not None:
                value = value.replace(tzinfo=None)
            return value
        return None

    long_df["value"] = long_df.apply(_coalesce, axis=1)
    wide = long_df.pivot_table(
        index="node_id", columns="property_name", values="value", aggfunc="first"
    ).reset_index()
    wide.columns.name = None
    return wide


def get_full_table_for_type(conn: psycopg.Connection, node_type: str) -> pd.DataFrame:
    nodes_df = get_nodes_by_type(conn, node_type)
    props_df = get_properties_for_type(conn, node_type)
    return nodes_df.merge(props_df, on="node_id", how="left")


def get_children(conn: psycopg.Connection, source_id: str, relationship: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT target_id FROM edges WHERE source_id = %s AND relationship = %s",
            (source_id, relationship),
        )
        return [r[0] for r in cur.fetchall()]


def get_edges_by_relationship(conn: psycopg.Connection, relationship: str) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT source_id, target_id FROM edges WHERE relationship = %(relationship)s",
        _as_sqlalchemy_engine(conn), params={"relationship": relationship},
    )


def get_table(conn: psycopg.Connection, table_name: str) -> pd.DataFrame:
    if table_name not in {
        "oreda_data", "bokor_eca_report", "catalog_profile",
        "hierarchy_index", "process_subprocess",
    }:
        raise ValueError(f"get_table: unrecognized table name {table_name!r}")
    return pd.read_sql_query(f"SELECT * FROM {table_name}", _as_sqlalchemy_engine(conn))  # noqa: S608 — table_name checked against allowlist above
