from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from enum import IntEnum
from typing import Any, Literal, TypedDict, cast


class Error:
    def __init__(self, message: str, err: str | None = None):
        self.message = message
        self.err = err

    def json(self) -> dict[str, str]:
        json: dict[str, str] = {}
        if self.message:
            json["details"] = self.message
        if self.err:
            json["error"] = self.err
        return json


type MaybeError = Error | None


class Permissions(IntEnum):
    NONE = 0
    SPONSOR = 1
    COMMITTEE = 2
    ADMIN = 3
    SUPER_ADMIN = 4


VALID_CATEGORIES = [
    "Cyber Policy",
    "Red Hat Academy",
    "Cyber Operations",
    "Hardware Hacking",
    "AWS Academy",
    "Cisco Networking Academy",
    "Palo Alto Academy",
    "Capture the Flag (legacy)",
    "Hack the Box (legacy)",
    "Tech Committee",
    "PR Committee",
    "Competition Committee",
    "Informational",
    "Bannering",
    "Competition",
    "Speaker",
    "Social",
    "Panel",
    "Beginner Meeting",
]
type Category = Literal[
    "Cyber Policy",
    "Red Hat Academy",
    "Cyber Operations",
    "Hardware Hacking",
    "AWS Academy",
    "Cisco Networking Academy",
    "Palo Alto Academy",
    "Capture the Flag (legacy)",
    "Hack the Box (legacy)",
    "Tech Committee",
    "PR Committee",
    "Competition Committee",
    "Informational",
    "Bannering",
    "Competition",
    "Speaker",
    "Social",
    "Panel",
    "Beginner Meeting",
]


class CalendarEvent(TypedDict):
    id: str
    name: str
    start: datetime
    end: datetime
    location: str
    category: str


type Semester = Literal["spring", "fall"]
type GradSemester = Literal["spring", "summer", "fall", "winter"]
type TableName = Literal[
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
]
type Item = Mapping[str, Any]


class User(TypedDict):
    user_id: str
    name: str
    grad_semester: GradSemester
    grad_year: int
    major: str
    email: str
    verified: int  # bool
    sponsor_email_opt_out: int  # bool
    join_date: str
    notes: str


type MaybeUser = User | None


class Resume(TypedDict):
    user_id: str
    filename: str
    format: str
    upload_date: str
    is_valid: int  # bool (1 or 0)


type MaybeResume = Resume | None


class Event(TypedDict):
    name: str
    code: str
    category: Category
    points: int
    date: str
    semester: Semester
    year: int


type MaybeEvent = Event | None


class Flagged(TypedDict):
    user_id: str
    offenses: int


type MaybeFlagged = Flagged | None


class Attendance(TypedDict):
    user_id: str
    code: str


type MaybeAttendance = Attendance | None


class Points(TypedDict):
    user_id: str
    points: int
    semester: Semester
    year: int


type MaybePoints = Points | None


class Tokens(TypedDict):
    name: str
    token: str
    created: str
    expires_after: str
    last_accessed: str
    revoked: int  # bool
    permission: Permissions


type MaybeTokens = Tokens | None


class Register(TypedDict):
    user_id: str
    ticket: str  # uuid
    time: str  # datetime.isoformat


class Verify(TypedDict):
    user_id: str
    code: int


class rsvp(TypedDict):
    user_id: str
    code: str
    reservation: int


def default_user(user_id: str):
    return deepcopy(
        User(
            user_id=user_id,
            name="",
            grad_semester=cast(GradSemester, ""),
            grad_year=cast(int, ""),
            major="",
            email="",
            verified=0,
            sponsor_email_opt_out=0,
            join_date="",
            notes="",
        )
    )
