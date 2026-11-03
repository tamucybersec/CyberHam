from collections.abc import Sequence
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    ColumnElement,
    Connection,
    Table,
    and_,
    delete,
    func,
    insert,
    inspect,
    or_,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError

from cyberham.database.backup import write_backup
from cyberham.database.engine import make_engine
from cyberham.database.tables import metadata
from cyberham.types import Item, TableName

ALEMBIC_INI = Path(__file__).parents[2] / "alembic.ini"

type PK = tuple[Any, ...]


class SQLiteDB:
    conn: Connection

    def __init__(self, db_path: str) -> None:
        self.setup(db_path)

    # should only be called in the constructor and during testing
    def setup(self, db_path: str) -> None:
        self.conn = make_engine(db_path).connect()
        self._migrate()

    def _migrate(self):
        cfg = Config(ALEMBIC_INI)
        cfg.attributes["connection"] = self.conn
        tables = inspect(self.conn).get_table_names()
        # assume existing db is par with baseline
        if tables and "alembic_version" not in tables:
            command.stamp(cfg, "0001")
        command.upgrade(cfg, "head")
        self.conn.commit()

    # create
    def create_row(self, table: TableName, item: Item) -> None:
        self.conn.execute(insert(_table(table)).values(item))
        self.conn.commit()

    # read
    def get_row(
        self, table: TableName, pk_names: list[str], pk_values: PK
    ) -> Item | None:
        t = _table(table)
        row = (
            self.conn.execute(select(t).where(_wheres(t, pk_names, pk_values)))
            .mappings()
            .first()
        )
        return dict(row) if row else None

    # update
    def update_row(
        self, table: TableName, pk_names: list[str], original: Item, updated: Item
    ) -> None:
        # Determine the columns that have changed
        diffs = {key: updated[key] for key in updated if original[key] != updated[key]}

        if not diffs:
            return  # Nothing to update

        t = _table(table)
        pk_values = [original[pk] for pk in pk_names]

        self.conn.execute(
            update(t).where(_wheres(t, pk_names, pk_values)).values(diffs)
        )
        self.conn.commit()

    # delete
    def delete_row(
        self, table: TableName, pk_names: list[str], pk_values: PK
    ) -> Item | None:
        old = self.get_row(table, pk_names, pk_values)
        if old:
            t = _table(table)
            self.conn.execute(delete(t).where(_wheres(t, pk_names, pk_values)))
            self.conn.commit()
        return old

    def get_batch(
        self,
        table: TableName,
        pk_names: list[str],
        pk_values: Sequence[PK],
    ) -> Sequence[Item | None]:
        if pk_values == []:
            return []

        t = _table(table)
        wheres = or_(*(_wheres(t, pk_names, vals) for vals in pk_values))
        rows = self.conn.execute(select(t).where(wheres)).mappings().all()

        # lookup map of pk values -> row
        row_map: dict[tuple[Any], Item] = {}
        for row in rows:
            key = tuple(row[pk] for pk in pk_names)
            row_map[key] = dict(row)

        # rebuild list in the same order as pk_values
        results: list[Item | None] = []
        for key_values in pk_values:
            key = tuple(key_values)
            result = row_map.get(key)
            results.append(result)

        return results

    def get_all_rows(self, table: TableName) -> list[Item]:
        rows = self.conn.execute(select(_table(table))).mappings().all()
        return [dict(row) for row in rows]

    def get_count(self, table: TableName) -> int:
        return self.conn.execute(
            select(func.count()).select_from(_table(table))
        ).scalar_one()

    def reset_table(self, table: TableName) -> None:
        self.conn.execute(delete(_table(table)))
        self.conn.commit()

    def replace_table(self, table: TableName, items: Sequence[Item]):
        try:
            self.conn.commit()
            old_items = self.get_all_rows(table)
            self.conn.execute(delete(_table(table)))
            self.batch_insert(table, items)
            write_backup(table, old_items)
            return {"message": "Replacement successful"}

        except IntegrityError as e:
            self.conn.rollback()
            return {
                "error": "Replacement failed due to foreign key constraints",
                "details": str(e),
            }

        except Exception as e:
            self.conn.rollback()
            return {"error": "Unexpected failure", "details": str(e)}

    def batch_insert(self, table: TableName, items: Sequence[Item]):
        self.conn.execute(insert(_table(table)), [dict(item) for item in items])
        self.conn.commit()


def _table(table: TableName) -> Table:
    return metadata.tables[table]


def _wheres(
    t: Table, pk_names: list[str], pk_values: Sequence[Any]
) -> ColumnElement[bool]:
    return and_(*(t.c[pk] == v for pk, v in zip(pk_names, pk_values, strict=True)))
