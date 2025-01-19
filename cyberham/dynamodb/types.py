from dataclasses import dataclass
from datetime import date
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    TypeAlias,
    TypeVar,
    Generic,
    Mapping,
    Dict,
)
from mypy_boto3_dynamodb.type_defs import (
    UniversalAttributeValueTypeDef,
    AttributeValueTypeDef,
    # QueryOutputTableTypeDef,
    # ScanOutputTableTypeDef,
    # UpdateItemOutputTableTypeDef,
)


T = TypeVar("T")

# region General Types


@dataclass
class Response:
    message: str


@dataclass
class ResponseWithData(Response, Generic[T]):
    data: Optional[T]


@dataclass
class UserData:
    user_id: int
    name: str
    points: int
    attended: int
    grad_year: int
    email: str


User: TypeAlias = Optional[UserData]


@dataclass
class EventData:
    name: str
    code: str
    points: int
    date: str
    resources: str
    attended_users: list[str]


Event: TypeAlias = Optional[EventData]

# endregion

# region Events Types


@dataclass
class AttendanceData:
    name: str
    points: int
    date: date
    resources: Any


Attendance: TypeAlias = ResponseWithData[AttendanceData]

# endregion

# region Users Types


@dataclass
class RegistrationStatus(Response):
    status: Literal["successful", "warning"]


@dataclass
class Leaderboard:
    x_title: str
    x: list[str]
    y_title: str
    y: list[int]


type Axis = Literal["points", "attended"]

# endregion

# region dynamo

type TableName = Literal["users", "events", "tests"]

Item: TypeAlias = Dict[str, Any]
MaybeItem: TypeAlias = Optional[Item]
SerializedItem: TypeAlias = Dict[str, AttributeValueTypeDef]

Key: TypeAlias = Item
SerializedDict: TypeAlias = Mapping[str, UniversalAttributeValueTypeDef]

UpdateItem: TypeAlias = Callable[[MaybeItem], MaybeItem]

# endregion
