from pathlib import Path
from typing import Any

from sqlalchemy import URL, Engine, create_engine, event


def make_engine(path: str | Path, *, readonly: bool = False) -> Engine:
    if readonly:
        url = URL.create(
            "sqlite",
            database=Path(path).resolve().as_uri(),
            query={"mode": "ro", "uri": "true"},
        )
    else:
        url = URL.create("sqlite", database=str(path))
    engine = create_engine(url)
    event.listen(engine, "connect", _enable_foreign_keys)
    return engine


def _enable_foreign_keys(dbapi_connection: Any, _: Any) -> None:
    dbapi_connection.execute("PRAGMA foreign_keys = ON")
