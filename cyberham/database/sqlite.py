import sqlite3
from typing import Optional, Any, Sequence
from cyberham.database.types import Item, TableName
from cyberham.database.backup import write_backup


class SQLiteDB:
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, db_path: str) -> None:
        self.setup(db_path)

    # should only be called in the constructor and during testing
    def setup(self, db_path: str) -> None:
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
                grad_year INTEGER NOT NULL,
                email TEXT NOT NULL,
                verified BOOLEAN NOT NULL
            )"""
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER NOT NULL,
                date TEXT NOT NULL,
                semester TEXT NOT NULL,
                year INTEGER NOT NULL
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

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
                FOREIGN KEY (code) REFERENCES events(code) ON UPDATE CASCADE,
                PRIMARY KEY (user_id, code)
            )"""
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER,
                points INTEGER NOT NULL,
                semester TEXT NOT NULL,
                year INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE,
                PRIMARY KEY (user_id, semester, year)
            )"""
        )

        self.conn.commit()

    # create
    def create_row(self, table: TableName, item: Item) -> None:
        cols = ", ".join(list(item.keys()))
        placeholders = ", ".join("?" for _ in item)
        vals = list(item.values())

        self.cursor.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", vals
        )
        self.conn.commit()

    # read
    def get_row(
        self, table: TableName, pk_names: list[str], pk_values: list[Any]
    ) -> Optional[Item]:
        wheres = self._wheres(pk_names)
        self.cursor.execute(f"SELECT * FROM {table} WHERE {wheres}", pk_values)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # update
    def update_row(
        self, table: TableName, pk_names: list[str], original: Item, updated: Item
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
        self, table: TableName, pk_names: list[str], pk_values: list[Any]
    ) -> Optional[Item]:
        old = self.get_row(table, pk_names, pk_values)
        if old:
            wheres = self._wheres(pk_names)
            self.cursor.execute(f"DELETE FROM {table} WHERE {wheres}", pk_values)
            self.conn.commit()
        return old

    def get_batch(
        self,
        table: TableName,
        pk_names: list[str],
        pk_values: list[list[Any]],
    ) -> Sequence[Optional[Item]]:
        if pk_values == []:
            return []

        wheres = " OR ".join(f"({self._wheres(pk_names)})" for _ in pk_values)

        # flatten pk_values
        values: list[Any] = []
        for vals in pk_values:
            values.extend(vals)

        self.cursor.execute(
            f"SELECT * FROM {table} WHERE {wheres}",
            values,
        )
        rows = self.cursor.fetchall()

        # lookup map of pk values -> row
        row_map: dict[tuple[Any], Item] = {}
        for row in rows:
            key = tuple(row[pk] for pk in pk_names)
            row_map[key] = dict(row)

        # rebuild list in the same order as pk_values
        results: list[Optional[Item]] = []
        for key_values in pk_values:
            key = tuple(key_values)
            result = row_map.get(key, None)
            results.append(result)

        return results

    def get_all_rows(self, table: TableName) -> list[Item]:
        self.cursor.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_count(self, table: TableName) -> int:
        self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return self.cursor.fetchone()[0]

    def reset_table(self, table: TableName) -> None:
        self.cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()

    def replace_table(self, table: TableName, items: Sequence[Item]):
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            old_items = self.get_all_rows(table)
            self.cursor.execute(f"DELETE FROM {table}")
            self.batch_insert(table, items)
            write_backup(table, old_items)
            return {"message": "Replacement successful"}

        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return {
                "error": "Replacement failed due to foreign key constraints",
                "details": str(e),
            }

        except Exception as e:
            self.conn.rollback()
            return {"error": "Unexpected failure", "details": str(e)}

    def batch_insert(self, table: TableName, items: Sequence[Item]):
        keys = items[0].keys()
        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        # Convert items to list of tuples
        values = [tuple(item[key] for key in keys) for item in items]
        self.cursor.executemany(sql, values)
        self.conn.commit()

    def _wheres(self, pk_names: list[str]) -> str:
        return " AND ".join([f"{pk} = ?" for pk in pk_names])
