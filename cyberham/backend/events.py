import random
import string

from datetime import datetime
from cyberham.apis.google_apis import google
from cyberham.database.queries import user_attendance_counts_for_events
from cyberham.database.typeddb import usersdb, eventsdb, attendancedb
from cyberham.types import (
    Error,
    MaybeError,
    CalendarEvent,
    Event,
    MaybeEvent,
    Attendance,
    Category,
    VALID_CATEGORIES,
)
from cyberham.utils.date import (
    cst_tz,
    current_semester,
    current_year,
    datetime_to_datestr,
    sort_events_by_date,
)


def create_event(
    name: str, points: int, date: str, category: Category
) -> tuple[str, MaybeError]:
    if name == "":
        return "", Error("Event name cannot be empty.")

    if not (category in VALID_CATEGORIES):
        return "", Error(
            f"Event '{name}' does not have a valid category ({category}). Valid categories: {VALID_CATEGORIES}"
        )

    # code generation
    event_code: str = ""
    while True:
        event_code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        if eventsdb.get((event_code,)) is None:
            break

    # event creation
    event = Event(
        name=name,
        code=event_code,
        points=points,
        date=date,
        semester=current_semester(),
        year=current_year(),
        category=category,
    )
    eventsdb.create(event)

    return event_code, None


def attend_event(code: str, user_id: str) -> tuple[str, MaybeEvent]:
    code = code.upper()

    # user validation
    user = usersdb.get((user_id,))
    if user is None or user["grad_year"] == 0:
        return "Please use /register to make a profile first!", None

    email_reminder = ""
    if user["verified"] == False:
        email_reminder = "Please verify your email address with /verify or request a new code if it timed out using /register."

    # event validation
    event = eventsdb.get((code,))
    if event is None:
        return f"{code} does not exist!", None

    attendance = attendancedb.get((user["user_id"], event["code"]))
    if attendance is not None:
        return f"You have already redeemed {code}!", None

    today = datetime_to_datestr(datetime.now(cst_tz))

    if (
        event["date"] != today
        or event["semester"] != current_semester()
        or event["year"] != current_year()
    ):
        return "You must redeem an event on the day it occurs!", None

    # attend event
    attendancedb.create(Attendance(user_id=user_id, code=code))
    return f"Successfully registered for {code}! {email_reminder}", event


def find_event(code: str = "") -> tuple[str, MaybeEvent, int]:
    if code == "":
        return "Please include an event name or code.", None, 0

    event = eventsdb.get((code,))
    if event is None:
        return "This event does not exist.", None, 0
    else:
        attendance = user_attendance_counts_for_events([code])
        return "", event, len(attendance.keys())


def event_list() -> list[Event]:
    all = eventsdb.get_all()
    sort_events_by_date(all, True)
    return all


def event_count() -> int:
    return eventsdb.get_count()


def calendar_events() -> tuple[list[CalendarEvent], MaybeError]:
    return google.client.get_events()
