import random
import string

from typing import Literal
from datetime import datetime
from pytz import timezone

from cyberham import conn, c
from cyberham.google_apis import GoogleClient, EmailPending, CalendarEvent
from cyberham.dynamodb.types import (
    User,
    MaybeUser,
    Event,
    MaybeEvent,
    Flagged,
    DummyEvent,
)
from cyberham.dynamodb.typeddb import usersdb, eventsdb, flaggeddb

# dict[user_id, EmailPending]
pending_emails: dict[int, EmailPending] = {}
google_client = GoogleClient()


# TODO
def init_db():
    # users: user_id, name, points, attended_dates, grad_year, tamu_email
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "users(user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER, attended INTEGER, grad_year INTEGER, email TEXT)"
    )
    # events: name, code, points, date (mm/dd/yy), resources, attended_users
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "events(name TEXT, code TEXT PRIMARY KEY, points INTEGER, date TEXT, resources TEXT, attended_users TEXT)"
    )
    # flagged: user_id, offenses
    c.execute(
        "CREATE TABLE IF NOT EXISTS "
        "flagged(user_id INTEGER PRIMARY KEY, offences INTEGER)"
    )
    conn.commit()


# NOTE removed functionality of awarding creator with points for event
# FIXME should throw error if name is "", as find_event does
def create_event(name: str, points: int, date: str, resources: str) -> str:
    # code generation
    event_code: str = ""
    existing_event = DummyEvent
    while existing_event is not None:
        event_code = "".join([random.choice(string.ascii_uppercase) for _ in range(5)])
        existing_event = eventsdb.get(event_code)

    # user validation and update
    # user = usersdb.get(user_id)
    # if user is None:
    #     return f'Only registered users can create an event.'
    # else:
    #     user["attended"] += 1
    #     user["points"] += points
    # usersdb.put(user)

    # event creation
    event = Event(
        name=name,
        code=event_code,
        points=points,
        date=date,
        resources=resources,
        attended_users=[],
    )
    eventsdb.put(event)

    return event_code


# FIXME concurrency concerns
# use consistent read
def attend_event(code: str, user_id: int) -> tuple[str, MaybeEvent]:
    code = code.upper()

    # user validation
    user = usersdb.get(user_id)
    if user is None or user["grad_year"] == 0:
        return "Please use /register to make a profile!", None

    # event validation
    event = eventsdb.get(code)

    if event is None:
        return f"{code} does not exist!", None

    if user_id in event["attended_users"]:
        return f"You have already redeemed {code}!", None

    cst_tz = timezone("America/Chicago")
    event_date = datetime.strptime(event["date"], "%m/%d/%Y").date()
    today = datetime.now(cst_tz).date()

    if event_date != today:
        return "You must redeem an event on the day it occurs!", None

    # attend event
    user["points"] += event["points"]
    user["attended"] += 1
    event["attended_users"].append(user_id)

    usersdb.put(user)
    eventsdb.put(event)

    return f"Successfully registered for {code}!", event


def leaderboard(axis: Literal["points", "attended"], lim: int = 10) -> list[User]:
    users = usersdb.get_all()

    if axis == "points":
        users.sort(key=lambda user: user["points"], reverse=True)
    else:
        users.sort(key=lambda user: user["attended"], reverse=True)

    return users[:lim]


# FIXME inefficient
# fetch all users at once or individually?
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
        for user_id in event["attended_users"]:
            if user_id in counts:
                counts[user_id] += 1
            else:
                counts[user_id] = 1

    # map ids to names
    leaderboard: list[tuple[str, int]] = []
    for user_id, count in counts.items():
        user = usersdb.get(user_id)

        if user is None:
            raise Exception(f"User {user_id} is in events but not in users.")

        leaderboard.append((user["name"], count))

    return leaderboard


# NOTE register can also update a user's information
def register(
    name: str,
    grad_year_str: str,
    email: str,
    user_id: int,
    user_name: str,
    guild_id: int | None,
) -> str:
    # validate grad year
    try:
        grad_year = int(grad_year_str)
    except ValueError:
        return "Please set your graduation year in the format YYYY (e.g. 2022)"
    if not datetime.now().year - 100 < grad_year < datetime.now().year + 5:
        return "Please set your graduation year in the format YYYY (e.g. 2022)"

    # validate email
    email = email.lower()
    if (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    ):
        return "Please set a proper TAMU email address"

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

    usersdb.update(update, user_id)

    return f"You have successfully updated your profile! {ask_to_verify}"


def register_email(user_id: int, email: str, guild_id: int | None) -> str:
    user = usersdb.get(user_id)
    if user is not None and user["email"] == email:
        return ""

    # check offenses
    if user_id in pending_emails:
        flagged = flaggeddb.get(user_id)

        if flagged is None:
            flagged = Flagged(user_id=user_id, offenses=1)
        else:
            flagged["offenses"] += 1

        flaggeddb.put(flagged)

        if flagged["offenses"] >= 3:
            return "Too many failed attempts to email verification, please contact an officer"

    # send email
    verification = EmailPending(
        user_id, email, random.randint(1000, 10000), datetime.now()
    )
    pending_emails[user_id] = verification

    # FIXME hardcoded GuildID
    google_client.send_email(
        email,
        str(verification.code),
        "Texas A&M Cybersecurity Club" if guild_id == 631254092332662805 else "TAMUctf",
    )

    return "Please use /verify with the code you received in your email."


def verify_email(code: int, user_id: int) -> str:
    if user_id not in pending_emails:
        return "Please use /register to submit your email"

    pending = pending_emails[user_id]

    if pending.code != code:
        return "This code is not correct!"

    def update(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["email"] = pending.email
        return user

    usersdb.update(update, user_id)
    pending_emails.pop(user_id)
    return "Email verified! It is now visible on your /profile"


def remove_pending(user_id: int = 0) -> None:
    del pending_emails[user_id]


def profile(user_id: int) -> tuple[str, MaybeUser]:
    user = usersdb.get(user_id)

    if user is None:
        return "Your profile does not exist", None

    return "", user


def find_event(code: str = "") -> tuple[str, MaybeEvent]:
    if code == "":
        return "Please include an event name or code.", None

    event = eventsdb.get(code)
    if event is None:
        return "This event does not exist", None
    else:
        return "", event


def event_list() -> list[Event]:
    return eventsdb.get_all()


def event_count() -> int:
    return eventsdb.get_count()


def award(user_id: int, user_name: str, points: int) -> str:
    user = usersdb.get(user_id)

    if user is None:
        return "This user has not registered yet!"

    user["points"] += points

    return f"Successfully added {points} points to {user_name} ({user["name"]})."


def calendar_events() -> list[CalendarEvent] | None:
    return google_client.get_events()
