from typing import TypedDict
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


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


class Body(BaseModel):
    credentials: Credentials


class Permissions(Enum):
    ADMIN = "ADMIN"
    SPONSOR = "SPONSOR"
    DENIED = "DENIED"
