"""Read-only report checks against an in-memory seeded database."""

import io
import sqlite3
import unittest
from contextlib import redirect_stdout

import main
from support import EXPECTED_COUNTS, open_seeded_memory, table_counts


def report_script(statements: dict[str, str]) -> str:
    """Build a queries.sql-style script in the application's report order."""
    return "\n".join(
        f"-- report: {name}\n{statements[name]}"
        for name, _title in main.REPORTS
    )


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = open_seeded_memory()
        self.reports = main.load_reports(main.read_sql_file("queries.sql"))

    def tearDown(self) -> None:
        self.connection.close()

    def rows(self, name: str) -> list[tuple]:
        statement = dict(self.reports)[name]
        return self.connection.execute(statement).fetchall()

    def test_three_named_reports_load_in_order(self) -> None:
        self.assertEqual(
            [name for name, _statement in self.reports],
            ["order_contents", "low_stock", "payment_status"],
        )

    def test_order_contents_lists_the_seeded_purchases(self) -> None:
        self.assertCountEqual(
            self.rows("order_contents"),
            [
                ("Emily Brown", 1, "Coca-Cola", 2),
                ("Michael Green", 2, "Potato Chips", 2),
            ],
        )

    def test_low_stock_identifies_potato_chips(self) -> None:
        self.assertEqual(self.rows("low_stock"), [("Potato Chips", 8, 10)])

    def test_payment_status_includes_method_status_and_amount(self) -> None:
        self.assertCountEqual(
            self.rows("payment_status"),
            [
                (1, "Card", "Paid", 3.0),
                (2, "Cash", "Pending", 2.4),
            ],
        )

    def test_running_reports_does_not_change_row_counts(self) -> None:
        before = table_counts(self.connection)
        self.assertEqual(before, EXPECTED_COUNTS)
        with redirect_stdout(io.StringIO()):
            main.run_reports(self.connection, self.reports)
        self.assertEqual(table_counts(self.connection), before)

    def test_report_connection_rejects_writes(self) -> None:
        with redirect_stdout(io.StringIO()):
            main.run_reports(self.connection, self.reports)
        with self.assertRaises(sqlite3.OperationalError) as caught:
            self.connection.execute("UPDATE Product SET unit_price = 9 WHERE product_id = 1")
        self.assertIn("readonly", str(caught.exception).lower())
        self.assertEqual(table_counts(self.connection), EXPECTED_COUNTS)

    def test_loader_accepts_only_single_select_statements(self) -> None:
        for name, statement in self.reports:
            with self.subTest(report=name):
                self.assertTrue(statement.lstrip().upper().startswith("SELECT"))
                self.assertNotIn(";", statement)

        valid = "SELECT 1"
        rejected = (
            "INSERT INTO Product (product_id, product_name, category_id, supplier_id, unit_price) "
            "VALUES (10, 'Extra', 1, 1, 1.0)",
            "UPDATE Product SET unit_price = 1 WHERE product_id = 1",
            "DELETE FROM Product",
            "SELECT 1; DELETE FROM Product",
        )
        for statement in rejected:
            with self.subTest(statement=statement):
                script = report_script(
                    {
                        "order_contents": statement,
                        "low_stock": valid,
                        "payment_status": valid,
                    }
                )
                with self.assertRaises(ValueError):
                    main.load_reports(script)


if __name__ == "__main__":
    unittest.main()
