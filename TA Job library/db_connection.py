"""Postgres connection to the SAP PM knowledge graph via Azure AD."""

import psycopg
from azure.identity import AzureCliCredential

HOST = "pg-db-petronas-sap-prd.postgres.database.azure.com"
PORT = 5432
DATABASE = "sap_pm_kg"
USERNAME = "abhishek.mali@tridiagonal.ai"
TOKEN_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"


def get_connection():
    print("  Requesting Azure AD token (needs 'az login')...")
    token = AzureCliCredential(process_timeout=20).get_token(TOKEN_SCOPE)
    return psycopg.connect(
        host=HOST, port=PORT, dbname=DATABASE, user=USERNAME,
        password=token.token, sslmode="require", connect_timeout=20,
    )


if __name__ == "__main__":
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user;")
        print("Connected:", cur.fetchone())
