import random
import string

from typing import Literal
from datetime import datetime
from pytz import timezone

from cyberham.apis.google_apis import google_client
from cyberham.apis.types import EmailPending, CalendarEvent
from cyberham.database.typeddb import usersdb, eventsdb, flaggeddb
from cyberham.database.types import (
    User,
    MaybeUser,
    Event,
    MaybeEvent,
    Flagged,
    MaybeFlagged,
)
from cyberham.utils.utils import user_attended, add_attendee, attendees


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


def leaderboard(axis: Literal["points", "attended"], lim: int = 10) -> list[User]:
    users = usersdb.get_all()

    if axis == "points":
        users.sort(key=lambda user: user["points"], reverse=True)
    else:
        users.sort(key=lambda user: user["attended"], reverse=True)

    return users[:lim]


# FIXME inefficient
# fetch all users at once or individually? implement a batch get
def leaderboard_search(activity: str) -> list[tuple[str, int]]:
    """
    Gets a ranked list of users' names who attended the most meetings that contain the string activity
    """

    events = eventsdb.get_all()
    counts: dict[int, int] = {}

    # sum frequencies
    for event in events:
        if activity.lower() not in event["name"].lower():
            continue
        for user_id in attendees(event):
            if user_id in counts:
                counts[user_id] += 1
            else:
                counts[user_id] = 1

    # map ids to names
    leaderboard: list[tuple[str, int]] = []
    for user_id, count in counts.items():
        user = usersdb.get([user_id])

        if user is not None:
            leaderboard.append((user["name"], count))

        # raise Exception(f"User {user_id} is in events but not in users.")

    return leaderboard


# NOTE register can also update a user's information
def register(
    name: str,
    grad_year_str: str,
    email: str,
    user_id: int,
    guild_id: int | None,
) -> str:
    # validate grad year
    try:
        grad_year = int(grad_year_str)
    except ValueError:
        return "Please set your graduation year in the format YYYY (e.g. 2022)."

    if not datetime.now().year - 100 < grad_year < datetime.now().year + 8:
        return "Please set your graduation year in the format YYYY (e.g. 2022)."

    # validate email
    email = email.lower()
    if (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    ):
        return "Please use a proper TAMU email address."

    ask_to_verify: str = register_email(user_id, email, guild_id)

    # update user information
    def update(user: MaybeUser) -> MaybeUser:
        if user is None:
            return User(
                user_id=user_id,
                name=name,
                points=0,
                attended=0,
                grad_year=grad_year,
                email=email,
            )
        else:
            user["name"] = name
            user["grad_year"] = grad_year
            user["email"] = email
            return user

    usersdb.update(update, pk_values=[user_id])

    return f"You have successfully updated your profile! {ask_to_verify}"


# NOTE update's a user's email if it differs from their original email
def register_email(user_id: int, email: str, guild_id: int | None) -> str:
    user = usersdb.get([user_id])
    if user is not None and user["email"] == email:
        return ""

    # check offenses
    if google_client.has_pending_email(user_id):

        def update_flagged(flagged: MaybeFlagged) -> MaybeFlagged:
            if flagged is None:
                flagged = Flagged(user_id=user_id, offences=1)
            else:
                flagged["offences"] += 1
            return flagged

        flagged = flaggeddb.update(update_flagged, pk_values=[user_id])

        if flagged is not None and flagged["offences"] >= 3:
            return "Too many failed attempts to email verification, please contact an officer."

    # send email
    verification = EmailPending(
        user_id=user_id,
        email=email,
        code=random.randint(1000, 10000),
        time=datetime.now(),
    )
    google_client.set_pending_email(user_id, verification)

    google_client.send_email(
        email,
        str(verification["code"]),
        "Texas A&M Cybersecurity Club",
    )

    return "Please use /verify with the code you received in your email. Be sure the check your spam folder as well."


def verify_email(code: int, user_id: int) -> str:
    user = usersdb.get([user_id])
    if user is None:
        return "Please use /register first."
    elif not google_client.has_pending_email(user_id):
        return "Please use /register to set your email first."

    pending = google_client.get_pending_email(user_id)
    if pending["code"] != code:
        return "This code is not correct!"

    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["email"] = pending["email"]
        return user

    usersdb.update(update_user, original=user)

    google_client.remove_pending_email(user_id)
    return "Email verified! It is now visible using /profile."


def remove_pending(user_id: int = 0) -> None:
    google_client.remove_pending_email(user_id)


def profile(user_id: int) -> tuple[str, MaybeUser]:
    user = usersdb.get([user_id])

    if user is None:
        return "Your profile does not exist.", None

    return "", user


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


def award(user_id: int, user_name: str, points: int) -> str:
    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["points"] += points
        return user

    user = usersdb.update(update_user, pk_values=[user_id])

    if user is None:
        return "This user has not registered yet!"
    return f"Successfully added {points} points to {user_name} {user["name"]}."


def calendar_events() -> list[CalendarEvent] | None:
    return google_client.get_events()
