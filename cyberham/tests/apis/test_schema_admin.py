from pathlib import Path
import sqlite3
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from cyberham.apis.dashboard import app
from cyberham.database.schema import (
    canonical_schema,
    load_schema_sql,
    snapshot_database,
)
from cyberham.database.table_registry import TABLE_REGISTRY
from cyberham.types import Permissions

client = TestClient(app)


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer schema-test-token"}


def test_schema_and_export_use_configured_data_directory(tmp_path):
    _make_database(tmp_path / "cyberham.db")
    with (
        patch("cyberham.database.schema.data_path", tmp_path),
        patch("cyberham.apis.auth.token_status", return_value=(Permissions.SUPER_ADMIN, True)),
    ):
        schema = client.get("/schema", headers=_headers())
        exported = client.get("/database/export", headers=_headers())
    assert schema.status_code == 200
    assert len(schema.json()["tables"]) == 10
    assert schema.json()["drift"] == []
    assert exported.status_code == 200
    assert exported.content[:16] == b"SQLite format 3" + bytes([0])


def _make_database(db_path: Path, *, legacy_resume_columns: bool = False) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(load_schema_sql())
        if legacy_resume_columns:
            conn.execute(
                "ALTER TABLE users ADD COLUMN resume_format TEXT NOT NULL DEFAULT ''"
            )
            conn.execute(
                "ALTER TABLE users ADD COLUMN resume_filename TEXT NOT NULL DEFAULT ''"
            )
        conn.commit()
    finally:
        conn.close()


class TestSchemaAdminApi:
    @patch("cyberham.apis.auth.token_status")
    def test_schema_lists_all_tables(
        self,
        mock_token_status,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.COMMITTEE, True)
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
        mock_token_status,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.COMMITTEE, True)
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
        mock_token_status,
        tmp_path: Path,
    ) -> None:
        mock_token_status.return_value = (Permissions.COMMITTEE, True)
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
        mock_token_status,
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


@pytest.mark.parametrize("endpoint", ["/schema", "/database/export"])
@pytest.mark.parametrize("permission,valid", [
    (Permissions.NONE, False),
    (Permissions.SPONSOR, True),
    (Permissions.SUPER_ADMIN, False),
])
def test_schema_endpoints_deny_insufficient_or_invalid_tokens(endpoint, permission, valid):
    with patch("cyberham.apis.auth.token_status", return_value=(permission, valid)):
        response = client.get(endpoint, headers=_headers())
    assert response.status_code == 403


@pytest.mark.parametrize("endpoint", ["/schema", "/database/export"])
def test_schema_endpoints_require_authentication(endpoint):
    assert client.get(endpoint).status_code == 403


def test_export_denies_admin():
    with patch("cyberham.apis.auth.token_status", return_value=(Permissions.ADMIN, True)):
        assert client.get("/database/export", headers=_headers()).status_code == 403


def test_export_missing_database(tmp_path):
    missing = tmp_path / "missing.db"
    with (
        patch("cyberham.apis.auth.token_status", return_value=(Permissions.SUPER_ADMIN, True)),
        patch("cyberham.apis.dashboard.live_database_path", return_value=missing),
    ):
        assert client.get("/database/export", headers=_headers()).status_code == 404
    assert not missing.exists()


def test_export_includes_wal_and_removes_temporary_snapshot(tmp_path):
    db_path = tmp_path / "source.db"
    _make_database(db_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("INSERT INTO verify VALUES ('snapshot-user', 12345)")
    connection.commit()
    snapshots = []

    def capture_snapshot(path):
        snapshot = snapshot_database(path)
        snapshots.append(snapshot)
        return snapshot

    try:
        with (
            patch("cyberham.apis.auth.token_status", return_value=(Permissions.SUPER_ADMIN, True)),
            patch("cyberham.apis.dashboard.live_database_path", return_value=db_path),
            patch("cyberham.apis.dashboard.snapshot_database", side_effect=capture_snapshot),
        ):
            response = client.get("/database/export", headers=_headers())
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert snapshots and not snapshots[0].exists()
        downloaded = tmp_path / "download.db"
        downloaded.write_bytes(response.content)
        with sqlite3.connect(downloaded) as exported:
            assert exported.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert exported.execute("SELECT code FROM verify WHERE user_id = 'snapshot-user'").fetchone() == (12345,)
    finally:
        connection.close()


def test_schema_uses_live_definitions_and_reports_missing_tables(tmp_path):
    db_path = tmp_path / "schema.db"
    _make_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute("DROP TABLE verify")
        connection.execute("CREATE TABLE verify (user_id INTEGER PRIMARY KEY, code TEXT DEFAULT 'pending')")
        connection.execute("DROP TABLE rsvp")
        connection.execute("CREATE TABLE rsvp (user_id TEXT NOT NULL, code TEXT NOT NULL, reservation INTEGER NOT NULL, PRIMARY KEY (user_id, code))")
        connection.execute("DROP TABLE register")
        connection.execute("CREATE TABLE \"extra'table\" (id TEXT)")
    with (
        patch("cyberham.apis.auth.token_status", return_value=(Permissions.COMMITTEE, True)),
        patch("cyberham.database.schema.live_database_path", return_value=db_path),
    ):
        response = client.get("/schema", headers=_headers())
    assert response.status_code == 200
    tables = {table["name"]: table for table in response.json()["tables"]}
    assert "register" not in tables
    assert "extra'table" in tables
    assert tables["verify"]["columns"][1]["type"] == "TEXT"
    assert tables["verify"]["columns"][1]["default_value"] == "'pending'"
    drift = {item["table"]: item for item in response.json()["drift"]}
    assert drift["verify"]["changed_columns"] == ["code", "user_id"]
    assert drift["rsvp"]["relationships_changed"] is True
    assert drift["register"]["missing_columns"] == ["ticket", "time", "user_id"]


def test_registry_documents_all_canonical_tables_and_preserves_crud_permissions():
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
            assert (entry.get_permission, entry.modify_permission) == expected[entry.name]
            assert canonical[entry.name].primary_key == entry.db.pk_names
        else:
            assert entry.get_permission is None and entry.modify_permission is None
