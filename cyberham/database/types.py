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


T = TypeVar("T")


class User(TypedDict):
    user_id: int
    name: str
    points: int
    attended: int
    grad_year: int
    email: str


MaybeUser: TypeAlias = Optional[User]


class Event(TypedDict):
    name: str
    code: str
    points: int
    date: str
    resources: str
    attended_users: str


MaybeEvent: TypeAlias = Optional[Event]


class Flagged(TypedDict):
    user_id: int
    offences: int


MaybeFlagged: TypeAlias = Optional[Flagged]


type TableName = Literal["users", "events", "flagged", "tests"]

Item: TypeAlias = Mapping[str, Any]
MaybeItem: TypeAlias = Optional[Item]
UpdateItem: TypeAlias = Callable[[MaybeItem], MaybeItem]


TestItem: TypeAlias = Mapping[str, Union[str, int]]


DummyUser: User = User(user_id=0, name="", points=0, attended=0, grad_year=0, email="")
DummyEvent: Event = Event(
    name="", code="", points=0, date="", resources="", attended_users=""
)
