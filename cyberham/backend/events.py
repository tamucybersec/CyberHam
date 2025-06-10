import random
import string

from datetime import datetime
from cyberham.apis.google_apis import google_client
from cyberham.apis.types import CalendarEvent
from cyberham.database.queries import user_attendance_counts_for_events
from cyberham.database.typeddb import usersdb, eventsdb, attendancedb
from cyberham.database.types import Event, MaybeEvent, Attendance
from cyberham.utils.date import (
    cst_tz,
    current_semester,
    current_year,
    datetime_to_datestr,
)


# FIXME should throw error if name is "", as find_event does
def create_event(name: str, points: int, date: str) -> str:
    # code generation
    event_code: str = ""
    while True:
        event_code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        if eventsdb.get([event_code]) is None:
            break

    # event creation
    event = Event(
        name=name,
        code=event_code,
        points=points,
        date=date,
        semester=current_semester(),
        year=current_year(),
    )
    eventsdb.create(event)

    return event_code


def attend_event(code: str, user_id: int) -> tuple[str, MaybeEvent]:
    code = code.upper()

    # user validation
    user = usersdb.get([user_id])
    if user is None or user["grad_year"] == 0:
        return "Please use /register to make a profile first!", None

    email_reminder = ""
    if user["verified"] == False:
        email_reminder = "Please verify your email address with /verify or request a new code if it timed out using /register."

    # event validation
    event = eventsdb.get([code])
    if event is None:
        return f"{code} does not exist!", None

    attendance = attendancedb.get([user["user_id"], event["code"]])
    if attendance is not None:
        return f"You have already redeemed {code}!", None

    today = datetime_to_datestr(datetime.now(cst_tz))

    if event["date"] != today:
        return "You must redeem an event on the day it occurs!", None

    # attend event
    attendancedb.create(Attendance(user_id=user_id, code=code))
    return f"Successfully registered for {code}! {email_reminder}", event


def find_event(code: str = "") -> tuple[str, MaybeEvent, int]:
    if code == "":
        return "Please include an event name or code.", None, 0

    event = eventsdb.get([code])
    if event is None:
        return "This event does not exist.", None, 0
    else:
        attendance = user_attendance_counts_for_events([code])
        return "", event, len(attendance.keys())


def event_list() -> list[Event]:
    return eventsdb.get_all()


def event_count() -> int:
    return eventsdb.get_count()


def calendar_events() -> list[CalendarEvent] | None:
    return google_client.get_events()
