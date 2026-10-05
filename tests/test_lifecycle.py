"""Rebuild behaviour against a temporary database file."""

import io
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import main
from support import EXPECTED_COUNTS, table_counts


class RebuildTests(unittest.TestCase):
    def test_rebuild_is_repeatable_and_reports_stay_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "retail.db"
            self.assertNotEqual(db_path.resolve(), main.DB_PATH.resolve())

            main.rebuild_database(db_path)
            self.assertTrue(db_path.is_file())
            first_counts = self.database_counts(db_path)
            self.assertEqual(first_counts, EXPECTED_COUNTS)

            main.rebuild_database(db_path)
            self.assertEqual(self.database_counts(db_path), first_counts)

            with main.connect_database(db_path) as connection:
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                reports = main.load_reports(main.read_sql_file("queries.sql"))
                before = table_counts(connection)
                with redirect_stdout(io.StringIO()):
                    main.run_reports(connection, reports)
                self.assertEqual(table_counts(connection), before)
                with self.assertRaises(sqlite3.OperationalError) as caught:
                    connection.execute("DELETE FROM Product")
                self.assertIn("readonly", str(caught.exception).lower())

    def test_rebuild_refuses_an_unexpected_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "notes.db"
            with self.assertRaises(RuntimeError):
                main.rebuild_database(db_path)
            self.assertFalse(db_path.exists())

    def test_rebuild_refuses_a_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.db"
            target.write_bytes(b"leave-me")
            link = Path(directory) / "retail.db"
            link.symlink_to(target)
            with self.assertRaises(RuntimeError):
                main.rebuild_database(link)
            self.assertEqual(target.read_bytes(), b"leave-me")

    def database_counts(self, db_path: Path) -> dict[str, int]:
        with main.connect_database(db_path) as connection:
            return table_counts(connection)


if __name__ == "__main__":
    unittest.main()
