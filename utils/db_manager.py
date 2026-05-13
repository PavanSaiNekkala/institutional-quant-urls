# =========================================================
# IMPORTS
# =========================================================

import duckdb

from pathlib import Path

# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = (
    BASE_DIR
    / "database"
)

DATABASE_DIR.mkdir(
    exist_ok=True
)

DB_FILE = (
    DATABASE_DIR
    / "institutional_quant.db"
)

# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    return duckdb.connect(
        str(DB_FILE)
    )
