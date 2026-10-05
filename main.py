"""Rebuild the retail sample database and print three read-only reports.

Running this file replaces database/retail.db from sql/create_tables.sql and
sql/seed.sql, then prints the reports in sql/queries.sql. The database is
generated demo state, so a second run produces the same rows and the same
report output.
"""

import re
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "retail.db"
SQL_DIR = BASE_DIR / "sql"
GENERATED_DB_NAME = "retail.db"

REPORTS = (
    ("order_contents", "Order contents"),
    ("low_stock", "Low stock"),
    ("payment_status", "Payment status"),
)

_REPORT_MARKER = re.compile(r"(?m)^-- report:\s+([a-z0-9_]+)\s*$")
_DATA_CHANGING = re.compile(
    r"\b(?:INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|REPLACE)\b",
    re.IGNORECASE,
)


def read_sql_file(file_name: str) -> str:
    """Read a SQL file from the project sql directory."""
    file_path = SQL_DIR / file_name
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


@contextmanager
def connect_database(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open SQLite with foreign keys on, and always close the connection."""
    connection = sqlite3.connect(db_path, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON;")
        yield connection
    finally:
        connection.close()


def execute_sql_script(connection: sqlite3.Connection, script: str) -> None:
    """Execute one complete SQL script.

    executescript commits an open transaction before it starts, so this must
    not be called in the middle of a transaction. Schema and seed setup pass
    a single script that begins and commits its own transaction.
    """
    connection.executescript(script)


def initialise_database(connection: sqlite3.Connection) -> None:
    """Create the schema and load the seed data in one transaction."""
    schema = read_sql_file("create_tables.sql").strip()
    seed = read_sql_file("seed.sql").strip()
    execute_sql_script(connection, f"BEGIN IMMEDIATE;\n{schema}\n{seed}\nCOMMIT;")


def remove_generated_database(db_path: Path, *, allowed_dir: Path = DATABASE_DIR) -> None:
    """Delete one non-symlink retail.db inside allowed_dir before a rebuild."""
    if db_path.is_symlink():
        raise RuntimeError("Refusing to delete a symlinked database file")

    if db_path.name != GENERATED_DB_NAME or db_path.parent.resolve() != allowed_dir.resolve():
        raise RuntimeError("Refusing to delete a path that is not retail.db in the rebuild directory")

    if db_path.exists():
        db_path.unlink()


def rebuild_database(db_path: Path = DB_PATH) -> None:
    """Replace the generated sample database with schema and seed data."""
    remove_generated_database(db_path, allowed_dir=db_path.parent)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with connect_database(db_path) as connection:
        try:
            initialise_database(connection)
        except sqlite3.Error:
            if connection.in_transaction:
                connection.rollback()
            raise


def load_reports(sql_text: str) -> list[tuple[str, str]]:
    """Load the named SELECT reports from queries.sql, in file order."""
    matches = list(_REPORT_MARKER.finditer(sql_text))
    expected = [name for name, _title in REPORTS]
    found = [match.group(1) for match in matches]
    if found != expected:
        raise ValueError(
            "queries.sql must define these reports in order: " + ", ".join(expected)
        )

    reports: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(sql_text)
        statement = _single_select(match.group(1), sql_text[match.end() : end])
        reports.append((match.group(1), statement))
    return reports


def _single_select(name: str, body: str) -> str:
    """Return one SELECT statement, rejecting anything that can change data."""
    lines = [
        line
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    statement = "\n".join(lines).strip().rstrip(";").strip()
    if not statement.upper().startswith("SELECT") or ";" in statement:
        raise ValueError(f"Report '{name}' must be exactly one SELECT statement")
    if _DATA_CHANGING.search(statement):
        raise ValueError(f"Report '{name}' must be read-only")
    return statement


def run_reports(
    connection: sqlite3.Connection, reports: list[tuple[str, str]]
) -> None:
    """Print each named SELECT. The connection is placed in query-only mode."""
    connection.execute("PRAGMA query_only = ON;")
    titles = dict(REPORTS)

    for name, statement in reports:
        print(f"\n--- {titles[name]} ({name}) ---")
        rows = connection.execute(statement).fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print("No results found.")


def main() -> None:
    """Rebuild database/retail.db from schema and seed, then print the reports."""
    rebuild_database(DB_PATH)
    reports = load_reports(read_sql_file("queries.sql"))
    with connect_database(DB_PATH) as connection:
        run_reports(connection, reports)
    print(f"\nSample database ready at {DB_PATH}")


if __name__ == "__main__":
    main()
