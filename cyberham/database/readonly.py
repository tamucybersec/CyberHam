import sqlite3
from typing import Any


class ReadonlyDB:
    conn: sqlite3.Connection

    def __init__(
        self,
        db_path: str,
    ):
        self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def execute(self, sql: str) -> dict[str, Any]:
        cursor = self.conn.cursor()

        try:
            cursor.execute(sql)
        except sqlite3.Error as err:
            raise ValueError("Query failed or not allowed.") from err

        if cursor.description is None:
            return {"columns": [], "rows": []}

        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows}
