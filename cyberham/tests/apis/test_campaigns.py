import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from cyberham.apis.dashboard import app
from cyberham.database.schema import load_schema_sql
from cyberham.types import Permissions

client = TestClient(app)
HEADERS = {"Authorization": "Bearer campaign-test"}
PAYLOAD = {"name": "MSC entrance", "slug": "msc-entrance", "source": "msc"}


@pytest.fixture(autouse=True)
def isolated_campaigns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    with sqlite3.connect(tmp_path / "cyberham.db") as connection:
        connection.executescript(load_schema_sql())
    monkeypatch.setattr("cyberham.apis.campaigns.data_path", tmp_path)
    monkeypatch.setattr("cyberham.apis.campaigns.website_url", "https://cybr.club")


@pytest.mark.parametrize(
    "permission", [Permissions.COMMITTEE, Permissions.ADMIN, Permissions.SUPER_ADMIN]
)
def test_campaign_lifecycle_and_persistence(permission: Permissions):
    with patch("cyberham.apis.auth.token_status", return_value=(permission, True)):
        created = client.post(
            "/analytics/campaigns",
            json={**PAYLOAD, "slug": " MSC-Entrance ", "source": "MSC"},
            headers=HEADERS,
        )
        assert created.status_code == 201
        row = created.json()
        assert (
            row["url"]
            == "https://cybr.club/qr?utm_campaign=msc-entrance&utm_source=msc"
        )
        assert row["slug"] == "msc-entrance"
        assert row["source"] == "msc"
        # A separate client/request sees the saved row, without GoatCounter configured.
        listed = TestClient(app).get("/analytics/campaigns", headers=HEADERS)
        assert listed.json() == [row]
        assert listed.headers["cache-control"] == "no-store"
        for archived in (True, False):
            updated = client.post(
                "/analytics/campaigns/msc-entrance/archive",
                json={"archived": archived},
                headers=HEADERS,
            )
            assert updated.status_code == 200
            assert updated.json() == {**row, "archived": archived}
        assert (
            client.post(
                "/analytics/campaigns", json=PAYLOAD, headers=HEADERS
            ).status_code
            == 409
        )
        client.post(
            "/analytics/campaigns/msc-entrance/archive",
            json={"archived": True},
            headers=HEADERS,
        )
        assert (
            client.post(
                "/analytics/campaigns", json=PAYLOAD, headers=HEADERS
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/analytics/campaigns/missing/archive",
                json={"archived": True},
                headers=HEADERS,
            ).status_code
            == 404
        )


@pytest.mark.parametrize(
    "permission,valid",
    [
        (Permissions.SPONSOR, True),
        (Permissions.NONE, False),
        (Permissions.ADMIN, False),
    ],
)
def test_campaign_permissions(permission: Permissions, valid: bool):
    with patch("cyberham.apis.auth.token_status", return_value=(permission, valid)):
        assert client.get("/analytics/campaigns", headers=HEADERS).status_code == 403
        assert (
            client.post(
                "/analytics/campaigns", json=PAYLOAD, headers=HEADERS
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/analytics/campaigns/x/archive",
                json={"archived": True},
                headers=HEADERS,
            ).status_code
            == 403
        )
    assert client.get("/analytics/campaigns").status_code == 403


@pytest.mark.parametrize(
    "change",
    [
        {"slug": "bad/tag"},
        {"slug": "a" * 81},
        {"slug": ""},
        {"source": "person@example.com"},
        {"source": ""},
        {"name": "  "},
        {"name": "x" * 101},
        {"url": "https://untrusted.example"},
    ],
)
def test_campaign_validation(change: dict[str, str]):
    with patch(
        "cyberham.apis.auth.token_status", return_value=(Permissions.COMMITTEE, True)
    ):
        assert (
            client.post(
                "/analytics/campaigns", json={**PAYLOAD, **change}, headers=HEADERS
            ).status_code
            == 422
        )
        assert client.get("/analytics/campaigns", headers=HEADERS).json() == []


def test_campaign_schema_is_additive_and_backed_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from cyberham.database.backup import write_full_backup
    from cyberham.database.sqlite import SQLiteDB

    db = SQLiteDB(str(tmp_path / "cyberham.db"))
    db.conn.execute(
        "INSERT INTO outreach_campaigns VALUES ('poster', 'Poster', 'msc', '2026-01-01', 0)"
    )
    db.conn.commit()
    db.conn.close()
    # Startup schema application preserves existing campaigns.
    reopened = SQLiteDB(str(tmp_path / "cyberham.db"))
    assert len(reopened.get_all_rows("outreach_campaigns")) == 1
    reopened.conn.close()
    monkeypatch.setattr("cyberham.database.backup.data_path", tmp_path)
    monkeypatch.setattr("cyberham.database.backup.path", tmp_path / "backups")
    write_full_backup()
    assert len(list((tmp_path / "backups").glob("outreach_campaigns_*.json"))) == 1
