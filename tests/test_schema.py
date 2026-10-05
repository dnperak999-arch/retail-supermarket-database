"""Schema, constraint, and seed checks against an in-memory database."""

import math
import sqlite3
import unittest

import support
from support import EXPECTED_COUNTS, TABLES, open_seeded_memory


EXPECTED_FOREIGN_KEYS = {
    "Role": set(),
    "User": {("role_id", "Role", "role_id")},
    "Customer": set(),
    "Supplier": set(),
    "Category": set(),
    "Product": {
        ("category_id", "Category", "category_id"),
        ("supplier_id", "Supplier", "supplier_id"),
    },
    "Inventory": {("product_id", "Product", "product_id")},
    "CustomerOrder": {
        ("customer_id", "Customer", "customer_id"),
        ("user_id", "User", "user_id"),
    },
    "OrderItem": {
        ("order_id", "CustomerOrder", "order_id"),
        ("product_id", "Product", "product_id"),
    },
    "Payment": {("order_id", "CustomerOrder", "order_id")},
}

REQUIRED_FOREIGN_KEYS = (
    ("User", "role_id"),
    ("Product", "category_id"),
    ("Product", "supplier_id"),
    ("Inventory", "product_id"),
    ("CustomerOrder", "customer_id"),
    ("CustomerOrder", "user_id"),
    ("OrderItem", "order_id"),
    ("OrderItem", "product_id"),
    ("Payment", "order_id"),
)

INVALID_WRITES = (
    (
        "invalid foreign key",
        "INSERT INTO Product (product_id, product_name, category_id, supplier_id, unit_price) "
        "VALUES (91, 'Ghost', 999, 1, 1.0)",
    ),
    (
        "null required foreign key",
        "INSERT INTO Product (product_id, product_name, category_id, supplier_id, unit_price) "
        "VALUES (90, 'No Category', NULL, 1, 1.0)",
    ),
    (
        "negative unit price",
        "UPDATE Product SET unit_price = -1 WHERE product_id = 1",
    ),
    (
        "negative stock",
        "UPDATE Inventory SET quantity_in_stock = -1 WHERE inventory_id = 1",
    ),
    (
        "zero order quantity",
        "INSERT INTO OrderItem (order_item_id, order_id, product_id, quantity, item_price) "
        "VALUES (90, 1, 2, 0, 1.0)",
    ),
    (
        "negative payment amount",
        "UPDATE Payment SET amount = -0.01 WHERE payment_id = 1",
    ),
    (
        "duplicate barcode",
        "INSERT INTO Product (product_id, product_name, category_id, supplier_id, unit_price, barcode) "
        "VALUES (92, 'Copy', 1, 1, 1.0, '111111111')",
    ),
    (
        "duplicate order item",
        "INSERT INTO OrderItem (order_item_id, order_id, product_id, quantity, item_price) "
        "VALUES (93, 1, 1, 1, 1.5)",
    ),
    (
        "invalid user status",
        "UPDATE User SET status = 'Suspended' WHERE user_id = 1",
    ),
    (
        "invalid order status",
        "UPDATE CustomerOrder SET order_status = 'Cancelled' WHERE order_id = 1",
    ),
    (
        "invalid payment method",
        "UPDATE Payment SET payment_method = 'Voucher' WHERE payment_id = 1",
    ),
    (
        "invalid payment status",
        "UPDATE Payment SET payment_status = 'Failed' WHERE payment_id = 1",
    ),
)


def foreign_keys(connection: sqlite3.Connection, table: str) -> set[tuple[str, str, str]]:
    """Return (column, referenced table, referenced column) for one table."""
    rows = connection.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    return {(row[3], row[2], row[4]) for row in rows}


def unique_column_sets(connection: sqlite3.Connection, table: str) -> set[tuple[str, ...]]:
    """Return column lists protected by a UNIQUE index."""
    unique_sets = set()
    for index in connection.execute(f"PRAGMA index_list({table})"):
        if index[2] != 1:
            continue
        columns = tuple(
            info[2]
            for info in connection.execute(f"PRAGMA index_info({index[1]})")
        )
        unique_sets.add(columns)
    return unique_sets


class SchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = open_seeded_memory()

    def tearDown(self) -> None:
        self.connection.close()

    def test_exactly_ten_application_tables(self) -> None:
        rows = self.connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        self.assertEqual([row[0] for row in rows], sorted(TABLES))

    def test_foreign_keys_match_the_retail_relationships(self) -> None:
        for table in TABLES:
            with self.subTest(table=table):
                self.assertEqual(foreign_keys(self.connection, table), EXPECTED_FOREIGN_KEYS[table])

    def test_foreign_key_enforcement_is_enabled(self) -> None:
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_required_relationship_columns_are_not_null(self) -> None:
        for table, column in REQUIRED_FOREIGN_KEYS:
            with self.subTest(table=table, column=column):
                info = {
                    row[1]: row[3]
                    for row in self.connection.execute(f"PRAGMA table_info({table})")
                }
                self.assertEqual(info[column], 1)

    def test_barcode_is_unique(self) -> None:
        self.assertIn(("barcode",), unique_column_sets(self.connection, "Product"))

    def test_order_item_product_is_unique_per_order(self) -> None:
        self.assertIn(
            ("order_id", "product_id"),
            unique_column_sets(self.connection, "OrderItem"),
        )

    def test_invalid_writes_raise_integrity_error(self) -> None:
        for label, sql in INVALID_WRITES:
            with self.subTest(constraint=label):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.connection.execute(sql)


class SeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = open_seeded_memory()

    def tearDown(self) -> None:
        self.connection.close()

    def test_seed_counts(self) -> None:
        self.assertEqual(support.table_counts(self.connection), EXPECTED_COUNTS)

    def test_foreign_key_check_is_clean(self) -> None:
        self.assertEqual(self.connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_integrity_check_is_ok(self) -> None:
        self.assertEqual(self.connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_stored_order_totals_match_line_items(self) -> None:
        rows = self.connection.execute(
            """
            SELECT
                CustomerOrder.order_id,
                CustomerOrder.total_amount,
                SUM(OrderItem.quantity * OrderItem.item_price) AS line_total
            FROM CustomerOrder
            JOIN OrderItem ON OrderItem.order_id = CustomerOrder.order_id
            GROUP BY CustomerOrder.order_id
            ORDER BY CustomerOrder.order_id
            """
        ).fetchall()
        self.assertEqual([row[0] for row in rows], [1, 2])
        for order_id, stored_total, line_total in rows:
            with self.subTest(order_id=order_id):
                self.assertTrue(
                    math.isclose(stored_total, line_total, rel_tol=1e-9, abs_tol=1e-6),
                    msg=f"order {order_id}: stored {stored_total}, lines {line_total}",
                )


if __name__ == "__main__":
    unittest.main()
