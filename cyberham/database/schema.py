import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkstemp
from typing import Any

from sqlalchemy import Connection, inspect, text
from sqlalchemy.engine.interfaces import ReflectedForeignKeyConstraint
from sqlalchemy.types import NullType, TypeEngine

from cyberham import data_path
from cyberham.database.engine import make_engine
from cyberham.database.tables import create_tables


@dataclass(frozen=True)
class ColumnSchema:
    name: str
    type: str
    not_null: bool
    default_value: str | None
    primary_key_index: int


@dataclass(frozen=True)
class ForeignKeySchema:
    column: str
    references_table: str
    references_column: str
    on_update: str
    on_delete: str


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: list[ColumnSchema]
    foreign_keys: list[ForeignKeySchema]

    @property
    def primary_key(self) -> list[str]:
        return [
            column.name
            for column in sorted(
                self.columns, key=lambda column: column.primary_key_index
            )
            if column.primary_key_index > 0
        ]


@dataclass(frozen=True)
class SchemaDrift:
    table: str
    missing_columns: list[str]
    extra_columns: list[str]
    changed_columns: list[str]
    relationships_changed: bool


def live_database_path() -> Path:
    return data_path / "cyberham.db"


def introspect_schema(conn: Connection) -> dict[str, TableSchema]:
    inspector = inspect(conn)
    tables = [name for name in inspector.get_table_names() if name != "alembic_version"]

    result: dict[str, TableSchema] = {}
    for table in tables:
        primary_key = inspector.get_pk_constraint(table)["constrained_columns"]

        result[table] = TableSchema(
            name=table,
            columns=[
                ColumnSchema(
                    name=column["name"],
                    type=_type_name(column["type"]),
                    not_null=not column["nullable"],
                    default_value=column.get("default"),
                    primary_key_index=(
                        primary_key.index(column["name"]) + 1
                        if column["name"] in primary_key
                        else 0
                    ),
                )
                for column in inspector.get_columns(table)
            ],
            foreign_keys=[
                ForeignKeySchema(
                    column=column,
                    references_table=fk["referred_table"],
                    references_column=referred_column,
                    on_update=_fk_action(fk, "onupdate"),
                    on_delete=_fk_action(fk, "ondelete"),
                )
                for fk in inspector.get_foreign_keys(table)
                for column, referred_column in zip(
                    fk["constrained_columns"], fk["referred_columns"], strict=True
                )
            ],
        )

    return result


def _type_name(column_type: TypeEngine[Any]) -> str:
    # untyped columns reflect as NullType
    if isinstance(column_type, NullType):
        return ""
    return str(column_type)


def _fk_action(fk: ReflectedForeignKeyConstraint, action: str) -> str:
    options = fk.get("options", {})
    return (options.get(action) or "NO ACTION").upper()


def canonical_schema() -> dict[str, TableSchema]:
    engine = make_engine(":memory:")
    try:
        with engine.connect() as conn:
            create_tables(conn)
            return introspect_schema(conn)
    finally:
        engine.dispose()


def live_schema(db_path: Path | None = None) -> dict[str, TableSchema]:
    engine = make_engine(db_path or live_database_path(), readonly=True)
    try:
        with engine.connect() as conn:
            return introspect_schema(conn)
    finally:
        engine.dispose()


def detect_schema_drift(
    db_path: Path | None = None,
    *,
    live: dict[str, TableSchema] | None = None,
) -> list[SchemaDrift]:
    canonical = canonical_schema()
    if live is None:
        live = live_schema(db_path)

    table_names = sorted(set(canonical.keys()) | set(live.keys()))
    drift: list[SchemaDrift] = []

    for table in table_names:
        expected = canonical.get(table, TableSchema(table, [], []))
        actual = live.get(table, TableSchema(table, [], []))
        canonical_columns = {column.name: column for column in expected.columns}
        live_columns = {column.name: column for column in actual.columns}

        missing_columns = sorted(canonical_columns.keys() - live_columns.keys())
        extra_columns = sorted(live_columns.keys() - canonical_columns.keys())
        changed_columns = sorted(
            name
            for name in canonical_columns.keys() & live_columns.keys()
            if canonical_columns[name] != live_columns[name]
        )
        relationships_changed = set(expected.foreign_keys) != set(actual.foreign_keys)

        if missing_columns or extra_columns or changed_columns or relationships_changed:
            drift.append(
                SchemaDrift(
                    table=table,
                    missing_columns=missing_columns,
                    extra_columns=extra_columns,
                    changed_columns=changed_columns,
                    relationships_changed=relationships_changed,
                )
            )

    return drift


def snapshot_database(db_path: Path) -> Path:
    """Create a consistent download, including committed WAL transactions."""
    descriptor, filename = mkstemp(prefix="cyberham-export-", suffix=".db")
    os.close(descriptor)
    snapshot_path = Path(filename)
    engine = make_engine(db_path, readonly=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("VACUUM INTO :path"), {"path": str(snapshot_path)})
    except BaseException:
        snapshot_path.unlink(missing_ok=True)
        raise
    finally:
        engine.dispose()
    return snapshot_path
