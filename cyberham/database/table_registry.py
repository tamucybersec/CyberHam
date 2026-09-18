from dataclasses import dataclass
from typing import Any

from cyberham.database.typeddb import (
    TypedDB,
    attendancedb,
    eventsdb,
    flaggeddb,
    pointsdb,
    registerdb,
    resumesdb,
    rsvpdb,
    tokensdb,
    usersdb,
    verifydb,
)
from cyberham.types import Permissions, TableName


@dataclass(frozen=True)
class TableRegistryEntry:
    name: TableName
    db: TypedDB[Any, Any]
    purpose: str
    dashboard_path: str | None
    get_permission: Permissions | None
    modify_permission: Permissions | None


TABLE_REGISTRY: tuple[TableRegistryEntry, ...] = (
    TableRegistryEntry(
        name="users",
        db=usersdb,
        purpose="Stores each club member profile used throughout the dashboard, registration flow, and event tracking.",
        dashboard_path="/dashboard/members",
        get_permission=Permissions.SPONSOR,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="resumes",
        db=resumesdb,
        purpose="Stores resume metadata for members who uploaded files during registration or profile updates.",
        dashboard_path=None,
        get_permission=Permissions.SPONSOR,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="events",
        db=eventsdb,
        purpose="Stores club events, including their codes, dates, categories, and point values.",
        dashboard_path="/dashboard/events",
        get_permission=Permissions.SPONSOR,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="flagged",
        db=flaggeddb,
        purpose="Tracks registration or verification offenses for members who need additional review.",
        dashboard_path="/dashboard/flagged",
        get_permission=Permissions.COMMITTEE,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="attendance",
        db=attendancedb,
        purpose="Records which members attended which events.",
        dashboard_path="/dashboard/attendance",
        get_permission=Permissions.SPONSOR,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="points",
        db=pointsdb,
        purpose="Stores awarded points by member and academic term.",
        dashboard_path="/dashboard/points",
        get_permission=Permissions.SPONSOR,
        modify_permission=Permissions.ADMIN,
    ),
    TableRegistryEntry(
        name="tokens",
        db=tokensdb,
        purpose="Stores dashboard access tokens and the permission level each token grants.",
        dashboard_path="/dashboard/tokens",
        get_permission=Permissions.SUPER_ADMIN,
        modify_permission=Permissions.SUPER_ADMIN,
    ),
    TableRegistryEntry(
        name="register",
        db=registerdb,
        purpose="Stores temporary registration tickets that connect a registration link to a member id and timestamp.",
        dashboard_path=None,
        get_permission=None,
        modify_permission=None,
    ),
    TableRegistryEntry(
        name="verify",
        db=verifydb,
        purpose="Stores email verification codes for members who still need to confirm their email address.",
        dashboard_path=None,
        get_permission=None,
        modify_permission=None,
    ),
    TableRegistryEntry(
        name="rsvp",
        db=rsvpdb,
        purpose="Stores RSVP responses for event forms before or alongside live attendance.",
        dashboard_path=None,
        get_permission=None,
        modify_permission=None,
    ),
)

TABLE_REGISTRY_BY_NAME = {entry.name: entry for entry in TABLE_REGISTRY}
