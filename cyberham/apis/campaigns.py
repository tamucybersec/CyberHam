"""Shared outreach metadata; no GoatCounter write access is required."""

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from cyberham import data_path, website_url
from cyberham.apis.auth import require_permission
from cyberham.types import Permissions

router = APIRouter(
    prefix="/analytics/campaigns",
    dependencies=[Depends(require_permission(Permissions.COMMITTEE))],
)
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_-]{1,80}$")]


class NewCampaign(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    slug: Slug
    source: Slug

    @field_validator("slug", "source", mode="before")
    @classmethod
    def normalize_tag(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class Campaign(NewCampaign):
    created_at: str
    archived: bool
    url: str


class ArchiveCampaign(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    archived: bool


def serialize(row: sqlite3.Row) -> Campaign:
    return Campaign(
        name=row["name"],
        slug=row["slug"],
        source=row["source"],
        created_at=row["created_at"],
        archived=bool(row["archived"]),
        url=f"{website_url.rstrip('/')}/qr?"
        + urlencode({"utm_campaign": row["slug"], "utm_source": row["source"]}),
    )


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(data_path / "cyberham.db")
    connection.row_factory = sqlite3.Row
    return connection


@router.get("")
async def list_campaigns(response: Response) -> list[Campaign]:
    response.headers["Cache-Control"] = "no-store"
    with closing(connect()) as connection:
        return [
            serialize(row)
            for row in connection.execute(
                "SELECT * FROM outreach_campaigns ORDER BY created_at DESC, slug"
            )
        ]


@router.post("", status_code=201)
async def create_campaign(body: NewCampaign) -> Campaign:
    try:
        with closing(connect()) as connection, connection:
            connection.execute(
                "INSERT INTO outreach_campaigns (slug, name, source, created_at) VALUES (?, ?, ?, ?)",
                (body.slug, body.name, body.source, datetime.now(UTC).isoformat()),
            )
            row = connection.execute(
                "SELECT * FROM outreach_campaigns WHERE slug = ?", (body.slug,)
            ).fetchone()
            return serialize(row)
    except sqlite3.IntegrityError:
        raise HTTPException(
            409,
            "That campaign tag already exists. Choose a unique tag or restore the archived campaign.",
        ) from None


@router.post("/{slug}/archive")
async def archive_campaign(slug: str, body: ArchiveCampaign) -> Campaign:
    with closing(connect()) as connection, connection:
        changed = connection.execute(
            "UPDATE outreach_campaigns SET archived = ? WHERE slug = ?",
            (int(body.archived), slug),
        )
        if not changed.rowcount:
            raise HTTPException(404, "Campaign not found.")
        return serialize(
            connection.execute(
                "SELECT * FROM outreach_campaigns WHERE slug = ?", (slug,)
            ).fetchone()
        )
