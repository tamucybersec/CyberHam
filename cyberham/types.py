from enum import IntEnum
from datetime import datetime
from typing import (
    Any,
    Literal,
    Optional,
    TypeAlias,
    Mapping,
    TypedDict,
)


class Error:
    def __init__(self, message: str | None = None, err: str | None = None):
        self.msg = message
        self.err = err

    def is_err(self) -> bool:
        return self.msg is not None

    def message(self) -> str:
        if self.msg is not None:
            return self.msg
        return ""

    def json(self) -> dict[str, str]:
        json: dict[str, str] = {}
        if self.msg:
            json["details"] = self.msg
        if self.err:
            json["error"] = self.err
        return json


MaybeError: TypeAlias = Optional[Error]


class Permissions(IntEnum):
    NONE = 0
    SPONSOR = 1
    COMMITTEE = 2
    ADMIN = 3
    SUPER_ADMIN = 4


class EmailPending(TypedDict):
    user_id: str
    email: str
    code: int
    time: datetime


class CalendarEvent(TypedDict):
    id: str
    name: str
    start: datetime
    end: datetime
    location: str
    category: str


type Semester = Literal["spring", "fall"]
type TableName = Literal["users", "events", "flagged", "attendance", "points", "tokens"]

Item: TypeAlias = Mapping[str, Any]


class User(TypedDict):
    user_id: str
    name: str
    grad_year: int
    email: str
    verified: bool


MaybeUser: TypeAlias = Optional[User]


class Event(TypedDict):
    name: str
    code: str
    points: int
    date: str
    semester: Semester
    year: int


MaybeEvent: TypeAlias = Optional[Event]


class Flagged(TypedDict):
    user_id: str
    offenses: int


MaybeFlagged: TypeAlias = Optional[Flagged]


class Attendance(TypedDict):
    user_id: str
    code: str


MaybeAttendance: TypeAlias = Optional[Attendance]


class Points(TypedDict):
    user_id: str
    points: int
    semester: Semester
    year: int


MaybePoints: TypeAlias = Optional[Points]


class Tokens(TypedDict):
    name: str
    token: str
    created: str
    expires_after: str
    last_accessed: str
    revoked: bool
    permission: Permissions


MaybeTokens: TypeAlias = Optional[Tokens]
