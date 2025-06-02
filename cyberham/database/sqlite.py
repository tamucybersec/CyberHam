import sqlite3
from typing import Optional, Any
from cyberham.database.types import Item


class SQLiteDB:
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER NOT NULL,
                attended INTEGER NOT NULL,
                grad_year INTEGER NOT NULL,
                email TEXT NOT NULL
            )"""
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER NOT NULL,
                date TEXT NOT NULL,
                resources TEXT NOT NULL,
                attended_users TEXT NOT NULL
            )"""
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flagged (
                user_id INTEGER PRIMARY KEY,
                offenses INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE
            )"""
        )

        # exact copy of users
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tests (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER NOT NULL,
                attended INTEGER NOT NULL,
                grad_year INTEGER NOT NULL,
                email TEXT NOT NULL
            )"""
        )

        self.conn.commit()

    # create
    def create_row(self, table: str, item: Item) -> None:
        cols = ", ".join(list(item.keys()))
        placeholders = ", ".join("?" for _ in item)
        vals = list(item.values())

        self.cursor.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals
        )
        self.conn.commit()

    # read
    def get_row(
        self, table: str, pk_names: list[str], pk_values: list[Any]
    ) -> Optional[Item]:
        wheres = self._wheres(pk_names)
        self.cursor.execute(f"SELECT * FROM {table} WHERE {wheres}", pk_values)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # update
    def update_row(
        self, table: str, pk_names: list[str], original: Item, updated: Item
    ) -> None:
        # Determine the columns that have changed
        diffs = {key: updated[key] for key in updated if original[key] != updated[key]}

        if not diffs:
            return  # Nothing to update

        set_clause = ", ".join(f"{col} = ?" for col in diffs)
        set_values = list(diffs.values())
        wheres = self._wheres(pk_names)
        pk_values = [original[pk] for pk in pk_names]

        self.cursor.execute(
            f"UPDATE {table} SET {set_clause} WHERE {wheres}", set_values + pk_values
        )
        self.conn.commit()

    # delete
    def delete_row(
        self, table: str, pk_names: list[str], pk_values: list[Any]
    ) -> Optional[Item]:
        old = self.get_row(table, pk_names, pk_values)
        if old:
            wheres = self._wheres(pk_names)
            self.cursor.execute(f"DELETE FROM {table} WHERE {wheres}", pk_values)
            self.conn.commit()
        return old

    def get_all_rows(self, table: str) -> list[Item]:
        self.cursor.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_count(self, table: str) -> int:
        self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return self.cursor.fetchone()[0]

    def reset_table(self, table: str) -> None:
        self.cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()

    def _wheres(self, pk_names: list[str]) -> str:
        return " AND ".join([f"{pk} = ?" for pk in pk_names])
