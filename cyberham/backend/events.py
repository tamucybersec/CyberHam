import random
import string

from datetime import datetime
from pytz import timezone

from cyberham.apis.google_apis import google_client
from cyberham.apis.types import CalendarEvent
from cyberham.database.typeddb import usersdb, eventsdb
from cyberham.database.types import MaybeUser, Event, MaybeEvent
from cyberham.utils.events import user_attended, add_attendee


# FIXME should throw error if name is "", as find_event does
def create_event(name: str, points: int, date: str, resources: str) -> str:
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
        resources=resources,
        attended_users="",
    )
    eventsdb.create(event)

    return event_code


# FIXME concurrency concerns -- to be fixed with separate attendance table
def attend_event(code: str, user_id: int) -> tuple[str, MaybeEvent]:
    code = code.upper()

    # user validation
    user = usersdb.get([user_id])
    if user is None or user["grad_year"] == 0:
        return "Please use /register to make a profile first!", None

    # event validation
    event = eventsdb.get([code])

    if event is None:
        return f"{code} does not exist!", None

    if user_attended(event, user_id):
        return f"You have already redeemed {code}!", None

    cst_tz = timezone("America/Chicago")
    event_date = datetime.strptime(event["date"], "%m/%d/%Y").date()
    today = datetime.now(cst_tz).date()

    if event_date != today:
        return "You must redeem an event on the day it occurs!", None

    # attend event
    def update_user(usr: MaybeUser) -> MaybeUser:
        if usr is not None:
            usr["points"] += event["points"]
            usr["attended"] += 1
        return usr

    def update_event(evt: MaybeEvent) -> MaybeEvent:
        if evt is not None:
            add_attendee(evt, user_id)
        return evt

    usersdb.update(update_user, original=user)
    updated_event = eventsdb.update(update_event, original=event)

    return f"Successfully registered for {code}!", updated_event


def find_event(code: str = "") -> tuple[str, MaybeEvent]:
    if code == "":
        return "Please include an event name or code.", None

    event = eventsdb.get([code])
    if event is None:
        return "This event does not exist.", None
    else:
        return "", event


def event_list() -> list[Event]:
    return eventsdb.get_all()


def event_count() -> int:
    return eventsdb.get_count()


def calendar_events() -> list[CalendarEvent] | None:
    return google_client.get_events()
