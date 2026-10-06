from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from cyberham.database.sqlite import ALEMBIC_INI, SQLiteDB
from cyberham.database.tables import metadata


def _diff(db: SQLiteDB) -> list[object]:
    ctx = MigrationContext.configure(db.conn, opts={"render_as_batch": True})
    return list(compare_metadata(ctx, metadata))


def test_single_migration_head():
    heads = ScriptDirectory.from_config(Config(ALEMBIC_INI)).get_heads()
    assert len(heads) == 1, f"multiple alembic heads, merge them: {heads}"


def test_migrations_match_tables():
    db = SQLiteDB(":memory:")
    diff = _diff(db)
    assert not diff, (
        "tables.py differs from migrations, run "
        f"`uv run alembic revision --autogenerate`: {diff}"
    )


def test_migrations_roundtrip():
    db = SQLiteDB(":memory:")
    cfg = Config(ALEMBIC_INI)
    cfg.attributes["connection"] = db.conn

    command.downgrade(cfg, "base")
    tables = inspect(db.conn).get_table_names()
    assert tables == ["alembic_version"], f"downgrade left tables: {tables}"

    command.upgrade(cfg, "head")
    assert not _diff(db)
