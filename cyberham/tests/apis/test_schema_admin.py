import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError
from starlette.types import Message

from cyberham.apis.dashboard import app, export_database
from cyberham.database.engine import make_engine
from cyberham.database.schema import (
    canonical_schema,
    live_schema,
    live_schema_sql,
    snapshot_database,
)
from cyberham.database.table_registry import TABLE_REGISTRY
from cyberham.database.tables import create_tables, metadata
from cyberham.types import Permissions

client = TestClient(app)


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer schema-test-token"}


def test_schema_and_export_use_configured_data_directory(tmp_path: Path) -> None:
    _make_database(tmp_path / "cyberham.db")
    with (
        patch("cyberham.database.schema.data_path", tmp_path),
        patch(
            "cyberham.apis.auth.token_status",
            return_value=(Permissions.SUPER_ADMIN, True),
        ),
    ):
        schema = client.get("/schema", headers=_headers())
        schema_sql = client.get("/schema/sql", headers=_headers())
        exported = client.get("/database/export", headers=_headers())
    assert schema.status_code == 200
    assert len(schema.json()["tables"]) == 10
    assert schema.json()["drift"] == []
    assert schema_sql.status_code == 200
    assert "CREATE TABLE users" in schema_sql.text
    assert exported.status_code == 200
    assert exported.content[:16] == b"SQLite format 3" + bytes([0])


def _make_database(db_path: Path, *, legacy_resume_columns: bool = False) -> None:
    engine = make_engine(db_path)
    try:
        with engine.begin() as conn:
            create_tables(conn)
            if legacy_resume_columns:
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN resume_format TEXT NOT NULL DEFAULT ''"
                )
                conn.exec_driver_sql(
                    "ALTER TABLE users ADD COLUMN resume_filename TEXT NOT NULL DEFAULT ''"
                )
    finally:
        engine.dispose()


class TestSchemaAdminApi:
    @patch("cyberham.apis.auth.token_status")
    def test_schema_sql_recreates_live_schema(
        self,
        mock_token_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.SUPER_ADMIN, True)
        source = tmp_path / "source.db"
        _make_database(source)
        with sqlite3.connect(source) as conn:
            conn.execute("INSERT INTO verify VALUES ('private-user', 12345)")
            conn.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        with patch(
            "cyberham.database.schema.live_database_path",
            return_value=source,
        ):
            response = client.get("/schema/sql", headers=_headers())

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "private-user" not in response.text
        db_path = tmp_path / "generated.db"
        with sqlite3.connect(db_path) as conn:
            conn.executescript(response.text)

        engine = make_engine(db_path)
        try:
            with engine.connect() as conn:
                context = MigrationContext.configure(
                    conn, opts={"compare_server_default": True}
                )
                assert compare_metadata(context, metadata) == []
                inspector = inspect(conn)
                assert set(inspector.get_table_names()) == set(metadata.tables)
                assert inspector.get_check_constraints("rsvp") == [
                    {"sqltext": "reservation IN (0, 1, 2)", "name": None}
                ]
                assert conn.exec_driver_sql("SELECT * FROM verify").all() == []
        finally:
            engine.dispose()

    @patch("cyberham.apis.auth.token_status")
    def test_schema_lists_all_tables(
        self,
        mock_token_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.SUPER_ADMIN, True)
        db_path = tmp_path / "schema.db"
        _make_database(db_path)

        with patch("cyberham.database.schema.live_database_path", return_value=db_path):
            response = client.get("/schema", headers=_headers())

        assert response.status_code == 200
        body = response.json()

        table_names = {table["name"] for table in body["tables"]}
        assert body["drift"] == []
        assert table_names == {
            "users",
            "resumes",
            "events",
            "flagged",
            "attendance",
            "points",
            "tokens",
            "register",
            "verify",
            "rsvp",
        }

    @patch("cyberham.apis.auth.token_status")
    def test_schema_includes_relationships_and_permissions(
        self,
        mock_token_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.SUPER_ADMIN, True)
        db_path = tmp_path / "schema.db"
        _make_database(db_path)

        with patch("cyberham.database.schema.live_database_path", return_value=db_path):
            response = client.get("/schema", headers=_headers())

        assert response.status_code == 200
        body = response.json()
        tables = {table["name"]: table for table in body["tables"]}

        attendance = tables["attendance"]
        assert attendance["primary_key"] == ["user_id", "code"]
        assert attendance["dashboard_path"] == "/dashboard/attendance"
        assert attendance["view_permission"] == Permissions.SPONSOR
        assert attendance["modify_permission"] == Permissions.ADMIN
        assert {fk["references_table"] for fk in attendance["foreign_keys"]} == {
            "users",
            "events",
        }

        points = tables["points"]
        assert points["primary_key"] == ["user_id", "semester", "year"]
        assert points["foreign_keys"] == [
            {
                "column": "user_id",
                "references_table": "users",
                "references_column": "user_id",
                "on_update": "CASCADE",
                "on_delete": "NO ACTION",
            }
        ]

        resumes = tables["resumes"]
        assert resumes["dashboard_path"] is None
        assert resumes["foreign_keys"] == [
            {
                "column": "user_id",
                "references_table": "users",
                "references_column": "user_id",
                "on_update": "CASCADE",
                "on_delete": "NO ACTION",
            }
        ]

        rsvp = tables["rsvp"]
        assert rsvp["primary_key"] == ["user_id", "code"]
        assert {fk["references_table"] for fk in rsvp["foreign_keys"]} == {
            "users",
            "events",
        }

    @patch("cyberham.apis.auth.token_status")
    def test_schema_reports_legacy_resume_column_drift(
        self,
        mock_token_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.SUPER_ADMIN, True)
        db_path = tmp_path / "schema.db"
        _make_database(db_path, legacy_resume_columns=True)

        with patch("cyberham.database.schema.live_database_path", return_value=db_path):
            response = client.get("/schema", headers=_headers())

        assert response.status_code == 200
        body = response.json()

        assert {
            "table": "users",
            "missing_columns": [],
            "extra_columns": ["resume_filename", "resume_format"],
            "changed_columns": [],
            "relationships_changed": False,
        } in body["drift"]
        users = next(table for table in body["tables"] if table["name"] == "users")
        assert "resume_filename" in {column["name"] for column in users["columns"]}

    @patch("cyberham.apis.auth.token_status")
    def test_export_requires_super_admin(
        self,
        mock_token_status: MagicMock,
        tmp_path: Path,
    ) -> None:
        db_path = tmp_path / "schema.db"
        _make_database(db_path)

        with patch("cyberham.apis.dashboard.live_database_path", return_value=db_path):
            mock_token_status.return_value = (Permissions.COMMITTEE, True)
            denied = client.get("/database/export", headers=_headers())
            assert denied.status_code == 403

            mock_token_status.return_value = (Permissions.SUPER_ADMIN, True)
            allowed = client.get("/database/export", headers=_headers())

        assert allowed.status_code == 200
        assert allowed.headers["content-disposition"].endswith('filename="schema.db"')


@pytest.mark.parametrize("endpoint", ["/schema", "/schema/sql", "/database/export"])
@pytest.mark.parametrize(
    "permission,valid",
    [
        (Permissions.NONE, False),
        (Permissions.SPONSOR, True),
        (Permissions.SUPER_ADMIN, False),
    ],
)
def test_schema_endpoints_deny_insufficient_or_invalid_tokens(
    endpoint: str, permission: Permissions, valid: bool
) -> None:
    with patch("cyberham.apis.auth.token_status", return_value=(permission, valid)):
        response = client.get(endpoint, headers=_headers())
    assert response.status_code == 403


@pytest.mark.parametrize("endpoint", ["/schema", "/schema/sql", "/database/export"])
def test_schema_endpoints_require_authentication(endpoint: str) -> None:
    assert client.get(endpoint).status_code == 403


@pytest.mark.parametrize("endpoint", ["/schema", "/schema/sql", "/database/export"])
@pytest.mark.parametrize("permission", [Permissions.COMMITTEE, Permissions.ADMIN])
def test_schema_endpoints_deny_below_super_admin(
    endpoint: str, permission: Permissions
) -> None:
    with patch("cyberham.apis.auth.token_status", return_value=(permission, True)):
        assert client.get(endpoint, headers=_headers()).status_code == 403


def test_export_missing_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with (
        patch(
            "cyberham.apis.auth.token_status",
            return_value=(Permissions.SUPER_ADMIN, True),
        ),
        patch("cyberham.apis.dashboard.live_database_path", return_value=missing),
    ):
        assert client.get("/database/export", headers=_headers()).status_code == 404
    assert not missing.exists()


def test_schema_sql_does_not_create_missing_database(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(OperationalError):
        live_schema_sql(missing)
    assert not missing.exists()


def test_schema_sql_preserves_sqlite_definitions(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    table_sql = (
        "CREATE TABLE entries (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "label TEXT COLLATE NOCASE UNIQUE, payload)"
    )
    index_sql = (
        "CREATE INDEX entries_label_idx ON entries (lower(label)) "
        "WHERE label IS NOT NULL"
    )
    with sqlite3.connect(source) as conn:
        conn.execute(table_sql)
        conn.execute(index_sql)
        conn.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
        conn.execute("CREATE INDEX version_idx ON alembic_version (version_num)")
        conn.execute("CREATE VIEW labels AS SELECT label FROM entries")

    sql = live_schema_sql(source)
    assert sql == f"{table_sql};\n\n{index_sql};\n"
    with sqlite3.connect(tmp_path / "recreated.db") as conn:
        conn.executescript(sql)
        conn.execute("INSERT INTO entries (label) VALUES ('Example')")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO entries (label) VALUES ('example')")


def test_schema_sql_empty_database(tmp_path: Path) -> None:
    source = tmp_path / "empty.db"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE alembic_version (version_num TEXT PRIMARY KEY)")
    assert live_schema_sql(source) == ""


def test_export_includes_wal_and_removes_temporary_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "source.db"
    _make_database(db_path)
    # keep the writer open so the insert stays in the WAL instead of being checkpointed
    engine = make_engine(db_path)
    connection = engine.connect()
    connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    connection.exec_driver_sql("INSERT INTO verify VALUES ('snapshot-user', 12345)")
    connection.commit()
    snapshots: list[Path] = []

    def capture_snapshot(path: Path) -> Path:
        snapshot = snapshot_database(path)
        snapshots.append(snapshot)
        return snapshot

    try:
        with (
            patch(
                "cyberham.apis.auth.token_status",
                return_value=(Permissions.SUPER_ADMIN, True),
            ),
            patch("cyberham.apis.dashboard.live_database_path", return_value=db_path),
            patch(
                "cyberham.apis.dashboard.snapshot_database",
                side_effect=capture_snapshot,
            ),
        ):
            response = client.get("/database/export", headers=_headers())
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert snapshots and not snapshots[0].exists()
        downloaded = tmp_path / "download.db"
        downloaded.write_bytes(response.content)
        exported_engine = make_engine(downloaded, readonly=True)
        with exported_engine.connect() as exported:
            assert (
                exported.exec_driver_sql("PRAGMA integrity_check").scalar_one() == "ok"
            )
            assert (
                exported.exec_driver_sql(
                    "SELECT code FROM verify WHERE user_id = 'snapshot-user'"
                ).scalar_one()
                == 12345
            )
        exported_engine.dispose()
    finally:
        connection.close()
        engine.dispose()


@pytest.mark.parametrize(
    "range_header,expected_status",
    [("garbage", 400), ("bytes=999999999999-", 416), ("bytes=0-15", 206)],
)
def test_export_cleans_up_after_range_requests(
    tmp_path: Path, range_header: str, expected_status: int
) -> None:
    db_path = tmp_path / "source.db"
    _make_database(db_path)
    snapshots: list[Path] = []

    def capture_snapshot(path: Path) -> Path:
        snapshot = snapshot_database(path)
        snapshots.append(snapshot)
        return snapshot

    try:
        with (
            patch(
                "cyberham.apis.auth.token_status",
                return_value=(Permissions.SUPER_ADMIN, True),
            ),
            patch("cyberham.apis.dashboard.live_database_path", return_value=db_path),
            patch(
                "cyberham.apis.dashboard.snapshot_database",
                side_effect=capture_snapshot,
            ),
        ):
            response = client.get(
                "/database/export",
                headers={**_headers(), "Range": range_header},
            )
        assert response.status_code == expected_status
        assert snapshots and not snapshots[0].exists()
        if expected_status == 206:
            assert response.content == b"SQLite format 3" + bytes([0])
    finally:
        for snapshot in snapshots:
            snapshot.unlink(missing_ok=True)


@pytest.mark.parametrize("failure", [OSError, asyncio.CancelledError])
def test_export_cleans_up_when_sending_fails_or_is_cancelled(
    tmp_path: Path, failure: type[BaseException]
) -> None:
    db_path = tmp_path / "source.db"
    _make_database(db_path)
    with patch("cyberham.apis.dashboard.live_database_path", return_value=db_path):
        response = export_database()
    snapshot = Path(response.path)
    assert snapshot.exists()

    async def send(message: Message) -> None:
        if message["type"] == "http.response.body":
            raise failure()

    async def receive() -> Message:
        return {"type": "http.disconnect"}

    try:
        with pytest.raises(failure):
            asyncio.run(
                response(
                    {"type": "http", "method": "GET", "headers": []}, receive, send
                )
            )
        assert not snapshot.exists()
        assert db_path.exists()
    finally:
        snapshot.unlink(missing_ok=True)


def test_schema_uses_live_definitions_and_reports_missing_tables(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schema.db"
    _make_database(db_path)
    engine = make_engine(db_path)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE verify")
        connection.exec_driver_sql(
            "CREATE TABLE verify (user_id INTEGER PRIMARY KEY, code TEXT DEFAULT 'pending')"
        )
        connection.exec_driver_sql("DROP TABLE rsvp")
        connection.exec_driver_sql(
            "CREATE TABLE rsvp (user_id TEXT NOT NULL, code TEXT NOT NULL, reservation INTEGER NOT NULL, PRIMARY KEY (user_id, code))"
        )
        connection.exec_driver_sql("DROP TABLE register")
        connection.exec_driver_sql('CREATE TABLE "extra\'table" (id TEXT)')
        connection.exec_driver_sql("CREATE INDEX verify_code_idx ON verify (code)")
    engine.dispose()
    with (
        patch(
            "cyberham.apis.auth.token_status",
            return_value=(Permissions.SUPER_ADMIN, True),
        ),
        patch("cyberham.database.schema.live_database_path", return_value=db_path),
    ):
        response = client.get("/schema", headers=_headers())
        schema_sql = client.get("/schema/sql", headers=_headers())
    assert response.status_code == 200
    assert schema_sql.status_code == 200
    recreated = tmp_path / "recreated.db"
    with sqlite3.connect(recreated) as conn:
        conn.executescript(schema_sql.text)
        assert (
            conn.execute("PRAGMA index_list(verify)").fetchone()[1] == "verify_code_idx"
        )
    assert live_schema(recreated) == live_schema(db_path)
    tables = {table["name"]: table for table in response.json()["tables"]}
    assert "register" not in tables
    assert "extra'table" in tables
    assert tables["verify"]["columns"][1]["type"] == "TEXT"
    assert tables["verify"]["columns"][1]["default_value"] == "'pending'"
    drift = {item["table"]: item for item in response.json()["drift"]}
    assert drift["verify"]["changed_columns"] == ["code", "user_id"]
    assert drift["rsvp"]["relationships_changed"] is True
    assert drift["register"]["missing_columns"] == ["ticket", "time", "user_id"]


def test_registry_documents_all_canonical_tables_and_preserves_crud_permissions() -> (
    None
):
    canonical = canonical_schema()
    assert set(canonical) == {entry.name for entry in TABLE_REGISTRY}
    expected = {
        "users": (Permissions.SPONSOR, Permissions.ADMIN),
        "resumes": (Permissions.SPONSOR, Permissions.ADMIN),
        "events": (Permissions.SPONSOR, Permissions.ADMIN),
        "flagged": (Permissions.COMMITTEE, Permissions.ADMIN),
        "attendance": (Permissions.SPONSOR, Permissions.ADMIN),
        "points": (Permissions.SPONSOR, Permissions.ADMIN),
        "tokens": (Permissions.SUPER_ADMIN, Permissions.SUPER_ADMIN),
    }
    for entry in TABLE_REGISTRY:
        assert entry.purpose
        if entry.name in expected:
            assert (entry.get_permission, entry.modify_permission) == expected[
                entry.name
            ]
            assert canonical[entry.name].primary_key == entry.db.pk_names
        else:
            assert entry.get_permission is None and entry.modify_permission is None
