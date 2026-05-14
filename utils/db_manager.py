# =========================================================
# DATABASE MANAGER
# =========================================================

import duckdb
import pandas as pd

from pathlib import Path

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = (
    BASE_DIR
    / "database"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

DB_FILE = (
    DATABASE_DIR
    / "institutional_quant.db"
)

CSV_FILE = (
    OUTPUT_DIR
    / "enriched_stock_data.csv"
)

# =========================================================
# CREATE DIRECTORIES
# =========================================================

DATABASE_DIR.mkdir(
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)

# =========================================================
# GET CONNECTION
# =========================================================

def get_connection():

    conn = duckdb.connect(
        str(DB_FILE)
    )

    # =============================================
    # AUTO REBUILD DATABASE
    # =============================================

    try:

        tables = conn.execute(
            "SHOW TABLES"
        ).fetchall()

        table_names = [

            table[0]
            for table in tables
        ]

        # =========================================
        # REBUILD IF TABLE MISSING
        # =========================================

        if "enriched_stocks" not in table_names:

            rebuild_database(conn)

    except Exception:

        rebuild_database(conn)

    return conn

# =========================================================
# REBUILD DATABASE
# =========================================================

def rebuild_database(conn):

    print("=" * 60)
    print("REBUILDING DATABASE...")
    print("=" * 60)

    if CSV_FILE.exists():

        df = pd.read_csv(
            CSV_FILE
        )

        conn.register(
            "temp_df",
            df
        )

        conn.execute(
            """
            CREATE OR REPLACE TABLE
            enriched_stocks AS

            SELECT *
            FROM temp_df
            """
        )

        print(
            "Database rebuilt successfully."
        )

    else:

        print(
            "CSV file missing. "
            "Database rebuild failed."
        )
