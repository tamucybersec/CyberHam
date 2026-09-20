import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkstemp

from cyberham import data_path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


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
            for column in sorted(self.columns, key=lambda column: column.primary_key_index)
            if column.primary_key_index > 0
        ]


@dataclass(frozen=True)
class SchemaDrift:
    table: str
    missing_columns: list[str]
    extra_columns: list[str]
    changed_columns: list[str]
    relationships_changed: bool


def load_schema_sql() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def live_database_path() -> Path:
    return data_path / "cyberham.db"


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def introspect_schema(connection: sqlite3.Connection) -> dict[str, TableSchema]:
    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
    tables = [row["name"] for row in cursor.fetchall()]

    result: dict[str, TableSchema] = {}
    for table in tables:
        column_rows = connection.execute(
            "SELECT * FROM pragma_table_info(?)", (table,)
        ).fetchall()
        fk_rows = connection.execute(
            "SELECT * FROM pragma_foreign_key_list(?)", (table,)
        ).fetchall()

        result[table] = TableSchema(
            name=table,
            columns=[
                ColumnSchema(
                    name=row["name"],
                    type=row["type"],
                    not_null=bool(row["notnull"]),
                    default_value=row["dflt_value"],
                    primary_key_index=row["pk"],
                )
                for row in column_rows
            ],
            foreign_keys=[
                ForeignKeySchema(
                    column=row["from"],
                    references_table=row["table"],
                    references_column=row["to"],
                    on_update=row["on_update"],
                    on_delete=row["on_delete"],
                )
                for row in fk_rows
            ],
        )

    return result


def canonical_schema() -> dict[str, TableSchema]:
    conn = _connect(":memory:")
    try:
        conn.executescript(load_schema_sql())
        return introspect_schema(conn)
    finally:
        conn.close()


def live_schema(db_path: Path | None = None) -> dict[str, TableSchema]:
    path = db_path or live_database_path()
    conn = _connect_readonly(path)
    try:
        return introspect_schema(conn)
    finally:
        conn.close()


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
    try:
        with (
            closing(_connect_readonly(db_path)) as source,
            closing(sqlite3.connect(snapshot_path)) as destination,
        ):
            source.backup(destination)
    except BaseException:
        snapshot_path.unlink(missing_ok=True)
        raise
    return snapshot_path
