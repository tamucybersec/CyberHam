from enum import IntEnum
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    TypeAlias,
    TypeVar,
    Mapping,
    TypedDict,
    Union,
)

type Semester = Literal["spring", "fall"]


class Permissions(IntEnum):
    NONE = 0
    SPONSOR = 1
    COMMITTEE = 2
    ADMIN = 3
    SUPER_ADMIN = 4


T = TypeVar("T")


class User(TypedDict):
    user_id: int
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
    user_id: int
    offenses: int


MaybeFlagged: TypeAlias = Optional[Flagged]


class Attendance(TypedDict):
    user_id: int
    code: str


MaybeAttendance: TypeAlias = Optional[Attendance]


class Points(TypedDict):
    user_id: int
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


type TableName = Literal["users", "events", "flagged", "attendance", "points", "tokens"]

Item: TypeAlias = Mapping[str, Any]
MaybeItem: TypeAlias = Optional[Item]
UpdateItem: TypeAlias = Callable[[MaybeItem], MaybeItem]


TestItem: TypeAlias = Mapping[str, Union[str, int]]
