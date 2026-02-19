import pytest
from cyberham.database.sqlite import SQLiteDB
from cyberham.types import TableName
from cyberham.tests.models import (
    valid_user_item,
    valid_user_2_item,
    unregistered_user_item,
)
from typing import Any

table: TableName = "users"
pk_names = ["user_id"]


class TestSQLiteCrud:
    sqlite: SQLiteDB

    @classmethod
    def setup_class(cls):
        cls.sqlite = SQLiteDB(":memory:")

    @pytest.fixture(autouse=True)
    def setup_database(self):
        self.sqlite.reset_table(table)
        self.sqlite.create_row(table, valid_user_item())
        self.sqlite.create_row(table, valid_user_2_item())

    def test_create_item(self):
        pk_values = self._pk_values(unregistered_user_item())
        self.sqlite.create_row(table, unregistered_user_item())
        after = self.sqlite.get_row(table, pk_names, pk_values)
        assert after == unregistered_user_item()

    def test_create_item_fails_overwrite(self):
        with pytest.raises(Exception):
            self.sqlite.create_row(table, valid_user_item())

    def test_get_item(self):
        pk_values = self._pk_values(valid_user_item())
        item = self.sqlite.get_row(table, pk_names, pk_values)
        assert item and valid_user_item() == item

    def test_get_non_existent_item(self):
        pk_values = self._pk_values(unregistered_user_item())
        item = self.sqlite.get_row(table, pk_names, pk_values)
        assert item is None

    def test_update_item(self):
        self.sqlite.update_row(
            table, pk_names, valid_user_item(), unregistered_user_item()
        )

        pk_values = self._pk_values(valid_user_item())
        old_item = self.sqlite.get_row(table, pk_names, pk_values)
        assert old_item is None

        pk_values = self._pk_values(unregistered_user_item())
        new_item = self.sqlite.get_row(table, pk_names, pk_values)
        assert new_item == unregistered_user_item()

    def test_delete_item(self):
        pk_values = self._pk_values(valid_user_item())
        old_item = self.sqlite.delete_row(table, pk_names, pk_values)
        assert old_item == valid_user_item()

    def test_delete_non_existent_item(self):
        pk_values = self._pk_values(unregistered_user_item())
        old_item = self.sqlite.delete_row(table, pk_names, pk_values)
        assert old_item is None

    def test_get_all(self):
        items = self.sqlite.get_all_rows(table)
        got = sorted(items, key=lambda item: item[pk_names[0]])
        expected = sorted(
            [
                valid_user_item(),
                valid_user_2_item(),
            ],
            key=lambda item: str(item[pk_names[0]]),
        )
        assert got == expected

    def test_get_count(self):
        assert self.sqlite.get_count(table) == 2

    def test_users_schema_migration_adds_opt_out_column(self):
        self.sqlite.conn.execute("DROP TABLE users")
        self.sqlite.conn.execute(
            """
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                grad_semester TEXT NOT NULL,
                grad_year INTEGER NOT NULL,
                major TEXT NOT NULL,
                email TEXT NOT NULL,
                verified INTEGER NOT NULL CHECK(verified IN (0, 1)),
                join_date TEXT NOT NULL,
                notes TEXT NOT NULL,
                resume_format TEXT NOT NULL,
                resume_filename TEXT NOT NULL
            )
            """
        )
        self.sqlite.conn.execute(
            """
            INSERT INTO users (
                user_id, name, grad_semester, grad_year, major, email, verified,
                join_date, notes, resume_format, resume_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-user",
                "Legacy User",
                "spring",
                2026,
                "Computer Science",
                "legacy@tamu.edu",
                1,
                "2025-01-01",
                "",
                "",
                "",
            ),
        )
        self.sqlite.conn.commit()

        self.sqlite._migrate_users_schema()
        self.sqlite._migrate_users_schema()

        self.sqlite.cursor.execute("PRAGMA table_info(users)")
        columns = {column["name"] for column in self.sqlite.cursor.fetchall()}
        assert "sponsor_email_opt_out" in columns

        legacy_user = self.sqlite.get_row(table, pk_names, ("legacy-user",))
        assert legacy_user is not None
        assert legacy_user["sponsor_email_opt_out"] == 0

    def _pk_values(self, model: dict[str, object]) -> tuple[Any, ...]:
        return tuple(model[pk] for pk in pk_names)
