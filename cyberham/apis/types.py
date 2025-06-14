from typing import TypedDict
from datetime import datetime


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
