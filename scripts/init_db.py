"""
NeuroSync AI — Database initialisation script.

Creates the SQLite database and runs the schema DDL.

Usage:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neurosync.config.settings import DATABASE_PATH
from neurosync.database.manager import DatabaseManager


def main() -> None:
    print(f"Initialising database at: {DATABASE_PATH}")
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(DATABASE_PATH)
    db.initialise()

    # Verify tables exist
    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    table_names = [dict(t)["name"] for t in tables]
    print(f"Tables created: {', '.join(table_names)}")

    db.close()
    print("Database initialisation complete ✓")


if __name__ == "__main__":
    main()
