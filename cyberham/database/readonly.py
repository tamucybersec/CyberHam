from typing import Any

from sqlalchemy import Connection
from sqlalchemy.exc import SQLAlchemyError

from cyberham.database.engine import make_engine


class ReadonlyDB:
    conn: Connection

    def __init__(
        self,
        db_path: str,
    ):
        self.conn = make_engine(db_path, readonly=True).connect()

    def close(self):
        self.conn.close()

    def execute(self, sql: str) -> dict[str, Any]:
        try:
            result = self.conn.exec_driver_sql(sql)
        except SQLAlchemyError as err:
            self.conn.rollback()
            raise ValueError("Query failed or not allowed.") from err

        if not result.returns_rows:
            return {"columns": [], "rows": []}

        columns = list(result.keys())
        rows = [dict(zip(columns, row, strict=False)) for row in result.fetchall()]
        return {"columns": columns, "rows": rows}
