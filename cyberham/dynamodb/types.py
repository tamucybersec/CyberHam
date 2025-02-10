from dataclass_dict_convert import dataclass_dict_convert  # type: ignore
from stringcase import camelcase  # type: ignore
from dataclasses import dataclass
from datetime import datetime
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
    Type,
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


@dataclass(kw_only=True)
class Response:
    message: str


@dataclass(kw_only=True)
class ResponseWithData(Response, Generic[T]):
    data: Optional[T]


@dataclass_dict_convert(dict_letter_case=camelcase)  # type: ignore
@dataclass(kw_only=True)
class User:
    user_id: int
    name: str
    points: int
    attended: int
    grad_year: int
    email: str


MaybeUser: TypeAlias = Optional[User]


@dataclass_dict_convert(dict_letter_case=camelcase)  # type: ignore
@dataclass(kw_only=True)
class Event:
    name: str
    code: str
    points: int
    date: str
    resources: str
    attended_users: list[str]


MaybeEvent: TypeAlias = Optional[Event]

# endregion

# region Events Types


@dataclass_dict_convert(dict_letter_case=camelcase)  # type: ignore
@dataclass(kw_only=True)
class AttendanceData:
    name: str
    points: int
    date: datetime
    resources: Any


Attendance: TypeAlias = ResponseWithData[AttendanceData]

# endregion

# region Users Types


@dataclass(kw_only=True)
class RegistrationStatus(Response):
    status: Literal["successful", "warning"]


@dataclass(kw_only=True)
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
UpdateItem: TypeAlias = Callable[[MaybeItem], MaybeItem]

Key: TypeAlias = Item
SerializedDict: TypeAlias = Mapping[str, UniversalAttributeValueTypeDef]

MaybeData: TypeAlias = Optional[T]
UpdateData: TypeAlias = Callable[[MaybeData[T]], MaybeData[T]]

UpdateUser: TypeAlias = Callable[[MaybeUser], MaybeUser]
UpdateEvent: TypeAlias = Callable[[MaybeEvent], MaybeEvent]

DummyUser: User = User(user_id=0, name="", points=0, attended=0, grad_year=0, email="")
DummyEvent: Event = Event(
    name="", code="", points=0, date="", resources="", attended_users=[]
)


def data_to_item(data: MaybeData[T]) -> MaybeItem:
    if data is None:
        return None

    return data.to_dict()  # type: ignore


def item_to_data(item: MaybeItem, cls: Type[T]) -> MaybeData[T]:
    if item is None:
        return None
    else:
        return cls.from_dict(item)  # type: ignore


# endregion
