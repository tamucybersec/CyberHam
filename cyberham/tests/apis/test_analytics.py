import asyncio
from datetime import date
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from cyberham.apis.analytics import read_report
from cyberham.apis.dashboard import app
from cyberham.types import Permissions

client = TestClient(app)
HEADERS = {"Authorization": "Bearer dashboard-test"}
DATES = {"start": "2026-01-01", "end": "2026-01-03"}


@pytest.mark.parametrize(
    "permission,valid",
    [
        (Permissions.NONE, False),
        (Permissions.SPONSOR, True),
        (Permissions.ADMIN, False),
        (Permissions.SUPER_ADMIN, False),
    ],
)
def test_analytics_denies_unauthorized_tokens(permission, valid):
    with patch("cyberham.apis.auth.token_status", return_value=(permission, valid)):
        assert (
            client.get("/analytics", params=DATES, headers=HEADERS).status_code == 403
        )


def test_analytics_requires_token():
    assert client.get("/analytics", params=DATES).status_code == 403


@pytest.mark.parametrize(
    "params,status",
    [
        ({"start": "2026-01-03", "end": "2026-01-01"}, 400),
        ({"start": "2026-01-01", "end": "2026-04-01"}, 400),
        ({"start": "2999-01-01", "end": "2999-01-01"}, 400),
        ({"start": "invalid", "end": "2026-01-01"}, 422),
    ],
)
def test_analytics_validates_dates(params, status):
    with patch(
        "cyberham.apis.auth.token_status", return_value=(Permissions.COMMITTEE, True)
    ):
        assert (
            client.get("/analytics", params=params, headers=HEADERS).status_code
            == status
        )


def test_unconfigured_analytics(monkeypatch):
    monkeypatch.delenv("GOATCOUNTER_API_TOKEN", raising=False)
    with patch(
        "cyberham.apis.auth.token_status", return_value=(Permissions.COMMITTEE, True)
    ):
        assert (
            client.get("/analytics", params=DATES, headers=HEADERS).status_code == 503
        )


def hit(path_id, path, count, event=False):
    return {
        "path_id": path_id,
        "path": path,
        "count": count,
        "event": event,
        "stats": [{"day": "2026-01-01", "daily": count}],
    }


def test_report_paginates_filters_and_combines_campaigns():
    requests = []

    def respond(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer stats-only"
        params = request.url.params
        assert params["start"] == "2026-01-01T00:00:00Z"
        assert params["end"] == "2026-01-03T23:59:59Z"
        if request.url.path.endswith("hits"):
            if params["exclude_paths"] == "":
                return httpx.Response(
                    200, json={"hits": [hit(1, "/qr", 8), hit(2, "/", 3)], "more": True}
                )
            assert params["exclude_paths"] == "1,2"
            return httpx.Response(
                200,
                json={
                    "hits": [
                        hit(3, "qr-join", 2, True),
                        hit(4, "qr-learn-more", 1, True),
                        hit(5, "/register", 100),
                        hit(6, "unknown", 40, True),
                    ],
                    "more": False,
                },
            )
        if request.url.path.endswith("toprefs"):
            assert params["include_paths"] == "1"
            return httpx.Response(
                200, json={"stats": [{"name": "msc", "count": 8}], "more": False}
            )
        if "/stats/hits/" in request.url.path:
            count = 2 if request.url.path.endswith("/3") else 1
            return httpx.Response(
                200,
                json={
                    "refs": [
                        {"name": "campaign:poster-a", "count": count},
                        {"name": "https://ignored.example", "count": 20},
                    ],
                    "more": False,
                },
            )
        path_id = params["include_paths"]
        if path_id == "1" and params["offset"] == "0":
            return httpx.Response(
                200, json={"stats": [{"name": "poster-a", "count": 5}], "more": True}
            )
        if path_id == "1":
            assert params["offset"] == "1"
            return httpx.Response(
                200, json={"stats": [{"name": "poster-b", "count": 3}], "more": False}
            )
        return httpx.Response(
            200,
            json={
                "stats": [{"name": "poster-a", "count": 2 if path_id == "3" else 1}],
                "more": False,
            },
        )

    async def run():
        async with httpx.AsyncClient(
            base_url="https://analytics.example/api/v0/",
            headers={"Authorization": "Bearer stats-only"},
            transport=httpx.MockTransport(respond),
        ) as upstream:
            return await read_report(upstream, date(2026, 1, 1), date(2026, 1, 3))

    report = asyncio.run(run())
    assert report["page_visits"] == 11
    assert report["qr_visits"] == 8
    assert report["clicks"] == {"join": 2, "learn_more": 1}
    assert [day["count"] for day in report["trend"]] == [11, 0, 0]
    assert report["campaigns"] == [
        {"name": "poster-a", "visits": 5, "join": 2, "learn_more": 1},
        {"name": "poster-b", "visits": 3, "join": 0, "learn_more": 0},
    ]
    assert report["referrers"] == [{"label": "msc", "count": 8}]


@pytest.mark.parametrize(
    "failure", [401, 429, 500, "timeout", "bad-json", "bad-shape", "redirect"]
)
def test_upstream_failures_are_sanitized(monkeypatch, failure):
    monkeypatch.setenv("GOATCOUNTER_URL", "https://analytics.example")
    monkeypatch.setenv("GOATCOUNTER_API_TOKEN", "private-upstream-token")
    original = httpx.AsyncClient

    def respond(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("private-upstream-token", request=request)
        if failure == "bad-json":
            return httpx.Response(200, text="private-upstream-token")
        if failure == "bad-shape":
            return httpx.Response(200, json={"hits": "private-upstream-token"})
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://other.example/"})
        return httpx.Response(failure, text="private-upstream-token")

    def factory(**kwargs):
        assert kwargs["follow_redirects"] is False
        assert kwargs["trust_env"] is False
        return original(**kwargs, transport=httpx.MockTransport(respond))

    with (
        patch(
            "cyberham.apis.auth.token_status", return_value=(Permissions.ADMIN, True)
        ),
        patch("cyberham.apis.analytics.httpx.AsyncClient", side_effect=factory),
    ):
        response = client.get("/analytics", params=DATES, headers=HEADERS)
    assert response.status_code == 502
    assert "private-upstream-token" not in response.text


@pytest.mark.parametrize(
    "permission", [Permissions.COMMITTEE, Permissions.ADMIN, Permissions.SUPER_ADMIN]
)
def test_empty_report_and_authorized_roles(monkeypatch, permission):
    monkeypatch.setenv("GOATCOUNTER_URL", "https://analytics.example")
    monkeypatch.setenv("GOATCOUNTER_API_TOKEN", "stats-token")
    original = httpx.AsyncClient

    def respond(request):
        # Missing paths must never turn into unfiltered campaign/referral requests.
        assert request.url.path == "/api/v0/stats/hits"
        return httpx.Response(200, json={"hits": None, "more": False})

    with (
        patch("cyberham.apis.auth.token_status", return_value=(permission, True)),
        patch(
            "cyberham.apis.analytics.httpx.AsyncClient",
            side_effect=lambda **kwargs: original(
                **kwargs, transport=httpx.MockTransport(respond)
            ),
        ),
    ):
        response = client.get("/analytics", params=DATES, headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["campaigns"] == []
    assert response.json()["clicks"] == {"join": 0, "learn_more": 0}


def test_goatcounter_default_rate_limit_is_retried():
    from cyberham.apis.analytics import get_stats

    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            429 if len(calls) == 1 else 200, json={"hits": [], "more": False}
        )

    async def run():
        async with httpx.AsyncClient(
            base_url="https://analytics.example/",
            transport=httpx.MockTransport(respond),
        ) as upstream:
            return await get_stats(upstream, "stats/hits", {})

    assert asyncio.run(run()) == {"hits": [], "more": False}
    assert len(calls) == 2
