"""Build isolated databases from the project SQL files."""

import sqlite3
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import main


TABLES = (
    "Role",
    "User",
    "Customer",
    "Supplier",
    "Category",
    "Product",
    "Inventory",
    "CustomerOrder",
    "OrderItem",
    "Payment",
)

EXPECTED_COUNTS = {
    "Role": 2,
    "User": 2,
    "Customer": 2,
    "Supplier": 2,
    "Category": 2,
    "Product": 3,
    "Inventory": 3,
    "CustomerOrder": 2,
    "OrderItem": 2,
    "Payment": 2,
}


def open_seeded_memory() -> sqlite3.Connection:
    """Return an in-memory database loaded from the project schema and seed."""
    connection = sqlite3.connect(":memory:", isolation_level=None)
    connection.execute("PRAGMA foreign_keys = ON;")
    main.initialise_database(connection)
    return connection


def table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return row counts for the ten application tables."""
    return {
        name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in TABLES
    }
