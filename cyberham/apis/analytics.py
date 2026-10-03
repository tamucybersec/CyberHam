"""Read-only GoatCounter reporting. No membership database access."""

import asyncio
import os
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from cyberham.apis.auth import require_permission
from cyberham.types import Permissions

router = APIRouter()
PUBLIC_PATHS = {"/", "/about", "/events", "/join", "/partnership", "/qr"}
EVENTS = {"qr-join": "join", "qr-learn-more": "learn_more"}


class UpstreamModel(BaseModel):
    model_config = ConfigDict(strict=True)


class Day(UpstreamModel):
    day: str
    daily: int = Field(ge=0)


class Hit(UpstreamModel):
    path_id: int
    path: str
    event: bool
    count: int = Field(ge=0)
    stats: list[Day] | None = None


class Hits(UpstreamModel):
    hits: list[Hit] | None
    more: bool


class Stat(UpstreamModel):
    name: str
    count: int = Field(ge=0)


class Refs(UpstreamModel):
    refs: list[Stat] | None
    more: bool


class Stats(UpstreamModel):
    stats: list[Stat] | None
    more: bool


async def get_stats(
    client: httpx.AsyncClient, endpoint: str, params: dict[str, str]
) -> dict[str, Any]:
    # GoatCounter defaults to four API requests per second. A complete report
    # needs at least five; retry a short burst without extending the overall
    # endpoint deadline or exposing upstream errors.
    for attempt in range(3):
        response = await client.get(endpoint, params=params)
        if response.status_code != 429 or attempt == 2:
            response.raise_for_status()
            return response.json()
        await asyncio.sleep(1)
    raise ValueError("Rate limit exceeded")


async def read_report(
    client: httpx.AsyncClient, start: date, end: date
) -> dict[str, Any]:
    params = {"start": f"{start}T00:00:00Z", "end": f"{end}T23:59:59Z", "limit": "100"}
    hits: list[Hit] = []
    seen: set[int] = set()
    for _ in range(20):
        payload = await get_stats(
            client,
            "stats/hits",
            {
                **params,
                "daily": "true",
                "exclude_paths": ",".join(map(str, sorted(seen))),
            },
        )
        page = Hits.model_validate(payload)
        new = page.hits or []
        if page.more and (not new or any(hit.path_id in seen for hit in new)):
            raise ValueError("Invalid pagination")
        hits.extend(new)
        seen.update(hit.path_id for hit in new)
        if not page.more:
            break
    else:
        raise ValueError("Report exceeds path limit")

    pages = [hit for hit in hits if not hit.event and hit.path in PUBLIC_PATHS]
    events = [hit for hit in hits if hit.event and hit.path in EVENTS]
    qr = [hit for hit in pages if hit.path == "/qr"]
    trend = {str(start + timedelta(days=i)): 0 for i in range((end - start).days + 1)}
    for hit in pages:
        for day in hit.stats or []:
            if day.day in trend:
                trend[day.day] += day.daily

    async def stats(endpoint: str, selected: list[Hit]) -> dict[str, int]:
        if not selected:
            return {}  # An empty include_paths means ALL paths in GoatCounter.
        result: dict[str, int] = {}
        offset = 0
        for _ in range(20):
            payload = await get_stats(
                client,
                f"stats/{endpoint}",
                {
                    **params,
                    "include_paths": ",".join(str(hit.path_id) for hit in selected),
                    "offset": str(offset),
                },
            )
            page = Stats.model_validate(payload)
            rows = page.stats or []
            for row in rows:
                result[row.name] = result.get(row.name, 0) + row.count
            if not page.more:
                return result
            if not rows:
                raise ValueError("Invalid pagination")
            offset += len(rows)
        raise ValueError("Report exceeds statistics limit")

    async def event_campaigns(path: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for hit in events:
            if hit.path != path:
                continue
            offset = 0
            for _ in range(20):
                payload = await get_stats(
                    client,
                    f"stats/hits/{hit.path_id}",
                    {**params, "offset": str(offset)},
                )
                page = Refs.model_validate(payload)
                rows = page.refs or []
                for row in rows:
                    if re.fullmatch(r"campaign/[a-zA-Z0-9_-]{1,80}", row.name):
                        name = row.name.removeprefix("campaign/")
                        result[name] = result.get(name, 0) + row.count
                if not page.more:
                    break
                if not rows:
                    raise ValueError("Invalid event referral pagination")
                offset += len(rows)
            else:
                raise ValueError("Report exceeds event referral limit")
        return result

    visits, joins, learns, referrers = await asyncio.gather(
        stats("campaigns", qr),
        event_campaigns("qr-join"),
        event_campaigns("qr-learn-more"),
        stats("toprefs", qr),
    )
    names = visits.keys() | joins.keys() | learns.keys()
    clicks = {
        name: sum(hit.count for hit in events if hit.path == path)
        for path, name in EVENTS.items()
    }
    return {
        "start": str(start),
        "end": str(end),
        "timezone": "UTC",
        "page_visits": sum(hit.count for hit in pages),
        "qr_visits": sum(hit.count for hit in qr),
        "clicks": clicks,
        "trend": [
            {"label": day, "title": day, "count": count} for day, count in trend.items()
        ],
        "campaigns": [
            {
                "name": name,
                "visits": visits.get(name, 0),
                "join": joins.get(name, 0),
                "learn_more": learns.get(name, 0),
            }
            for name in sorted(names, key=lambda name: (-visits.get(name, 0), name))
        ],
        "referrers": [
            {"label": name or "Direct / unknown", "count": count}
            for name, count in sorted(referrers.items(), key=lambda item: -item[1])
        ],
    }


@router.get(
    "/analytics", dependencies=[Depends(require_permission(Permissions.COMMITTEE))]
)
async def analytics(response: Response, start: date, end: date):
    today = datetime.now(UTC).date()
    if end < start or (end - start).days >= 90 or end > today:
        raise HTTPException(
            400,
            "Choose an ordered date range of at most 90 days, ending today or earlier (UTC).",
        )
    base = os.environ.get("GOATCOUNTER_URL", "").rstrip("/")
    token = os.environ.get("GOATCOUNTER_API_TOKEN", "")
    try:
        parsed = urlsplit(base)
    except ValueError:
        raise HTTPException(503, "Website analytics is not configured.") from None
    if (
        not token
        or parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(503, "Website analytics is not configured.")
    try:
        # Fixed server configuration only: callers cannot choose a URL or headers.
        async with (
            asyncio.timeout(30),
            httpx.AsyncClient(
                base_url=f"{base}/api/v0/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
                follow_redirects=False,
                trust_env=False,
            ) as client,
        ):
            report = await read_report(client, start, end)
    except (httpx.HTTPError, ValueError, TypeError, TimeoutError):
        # Never return upstream bodies, URLs, or authentication details.
        raise HTTPException(
            502, "Website analytics is temporarily unavailable. Please try again."
        ) from None
    response.headers["Cache-Control"] = "no-store"
    return report
