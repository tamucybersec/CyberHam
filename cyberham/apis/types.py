from typing import TypedDict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from functools import total_ordering


class EmailPending(TypedDict):
    user_id: int
    email: str
    code: int
    time: datetime


class CalendarEvent(TypedDict):
    id: str
    name: str
    start: datetime
    end: datetime
    location: str


class Credentials(BaseModel):
    username: str
    password: str


class AuthenticationRequest(BaseModel):
    credentials: Credentials


@total_ordering
class Permissions(Enum):
    NONE = 0
    DENIED = 1
    SPONSOR = 2
    ADMIN = 3

    def __lt__(self, other: Any):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class ValidateBody(BaseModel):
    password: str
    credentials: Credentials
