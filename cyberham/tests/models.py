from copy import deepcopy
from typing import Any
from datetime import datetime, timedelta
from cyberham.database.types import User, Event, Flagged, Attendance, Points
from cyberham.apis.types import EmailPending
from cyberham.utils.date import (
    current_semester,
    current_year,
    cst_tz,
    datetime_to_datestr,
)

now = datetime.now(cst_tz)
today = datetime_to_datestr(now)
yesterday = datetime_to_datestr(now - timedelta(days=1))
tomorrow = datetime_to_datestr(now + timedelta(days=1))
last_year = datetime_to_datestr(now - timedelta(weeks=52))


# all models are functions to promote immutability between test cases
# this was an issue in the past, causing ugly deepcopy()s on every test
# (in python with pytest, if one field of the model was accidentally
# changed the variable for every subsequent test)


def valid_user() -> User:
    return deepcopy(
        User(
            user_id=0,
            name="Lane",
            grad_year=2024,
            email="lane@tamu.edu",
            verified=True,
        )
    )


def valid_user_2() -> User:
    return deepcopy(
        User(
            user_id=1,
            name="Stella",
            grad_year=2025,
            email="stella@tamu.edu",
            verified=True,
        )
    )


def updated_user() -> User:
    return deepcopy(
        User(
            user_id=2,
            name="Emma",
            grad_year=2027,
            email="emma@tamu.edu",
            verified=True,
        )
    )


def updated_user_2() -> User:
    return deepcopy(
        User(
            user_id=3,
            name="Colby",
            grad_year=0,
            email="colby@tamu.edu",
            verified=True,
        )
    )


def flagged_user() -> User:
    return deepcopy(
        User(
            user_id=4,
            name="Damian",
            grad_year=2026,
            email="",
            verified=True,
        )
    )


def no_email_user() -> User:
    return deepcopy(
        User(
            user_id=5,
            name="Javi",
            grad_year=2027,
            email="",
            verified=True,
        )
    )


def unregistered_user() -> User:
    return deepcopy(
        User(
            user_id=9,
            name="Owen",
            grad_year=2027,
            email="owen@tamu.edu",
            verified=True,
        )
    )


def unregistered_user_2() -> User:
    return deepcopy(
        User(
            user_id=10,
            name="Zach",
            grad_year=2027,
            email="zach@tamu.edu",
            verified=True,
        )
    )


def valid_user_item() -> dict[str, Any]:
    return deepcopy(dict(valid_user()))


def valid_user_2_item() -> dict[str, Any]:
    return deepcopy(dict(valid_user_2()))


def unregistered_user_item() -> dict[str, Any]:
    return deepcopy(dict(unregistered_user()))


def users() -> list[User]:
    return deepcopy(
        [
            valid_user(),
            valid_user_2(),
            updated_user(),
            updated_user_2(),
            flagged_user(),
            no_email_user(),
        ]
    )


def valid_event() -> Event:
    return deepcopy(
        Event(
            name="AWS Academy",
            code="AWSAC",
            points=50,
            date=today,
            semester=current_semester(),
            year=current_year(),
        )
    )


def valid_event_2() -> Event:
    return deepcopy(
        Event(
            name="Hardware Hacking",
            code="HRDHK",
            points=50,
            date=today,
            semester=current_semester(),
            year=current_year(),
        )
    )


def past_event() -> Event:
    return deepcopy(
        Event(
            name="Red Hat Academy",
            code="RDHAT",
            points=50,
            date=yesterday,
            semester=current_semester(),
            year=current_year(),
        )
    )


def future_event() -> Event:
    return deepcopy(
        Event(
            name="Palo Alto Academy",
            code="PALAL",
            points=50,
            date=tomorrow,
            semester=current_semester(),
            year=current_year(),
        )
    )


def attended_event() -> Event:
    return deepcopy(
        Event(
            name="Cisco Networking Academy",
            code="CISCO",
            points=50,
            date=today,
            semester=current_semester(),
            year=current_year(),
        )
    )


def attended_event_2() -> Event:
    return deepcopy(
        Event(
            name="Cisco Networking Academy",
            code="CISC2",
            points=50,
            date=today,
            semester=current_semester(),
            year=current_year(),
        )
    )


def attended_past_event() -> Event:
    return deepcopy(
        Event(
            name="Policy",
            code="PLICY",
            points=50,
            date=last_year,
            semester=current_semester(),
            year=current_year() - 1,
        )
    )


def unregistered_event() -> Event:
    return deepcopy(
        Event(
            name="Hack the Box",
            code="HKBOX",
            points=50,
            date=today,
            semester=current_semester(),
            year=current_year(),
        )
    )


def events() -> list[Event]:
    return deepcopy(
        [
            valid_event(),
            valid_event_2(),
            past_event(),
            future_event(),
            attended_event(),
            attended_event_2(),
            attended_past_event(),
        ]
    )


def flagged_users() -> list[Flagged]:
    return deepcopy(
        [
            Flagged(
                user_id=flagged_user()["user_id"],
                offenses=3,
            ),
        ]
    )


# caps are marked as constants
NEW_EMAIL = "NEW_EMAIL@tamu.edu"
VERIFICATION_CODE = 1234


def attendance() -> list[Attendance]:
    return deepcopy(
        [
            Attendance(
                user_id=valid_user()["user_id"],
                code=attended_event()["code"],
            ),
            Attendance(
                user_id=valid_user_2()["user_id"],
                code=attended_event()["code"],
            ),
            Attendance(
                user_id=valid_user()["user_id"],
                code=attended_past_event()["code"],
            ),
            Attendance(
                user_id=valid_user_2()["user_id"],
                code=attended_past_event()["code"],
            ),
        ]
    )


def points() -> list[Points]:
    return deepcopy(
        [
            Points(
                user_id=valid_user()["user_id"],
                points=50,
                semester=current_semester(),
                year=current_year(),
            ),
            Points(
                user_id=valid_user_2()["user_id"],
                points=1000,
                semester=current_semester(),
                year=current_year(),
            ),
            Points(
                user_id=updated_user()["user_id"],
                points=70,
                semester=current_semester(),
                year=current_year(),
            ),
            # update_user_2 skip for edge case detection
            Points(
                user_id=no_email_user()["user_id"],
                points=10,
                semester=current_semester(),
                year=current_year(),
            ),
        ]
    )


def pending_users() -> list[EmailPending]:
    return deepcopy(
        [
            EmailPending(
                user_id=flagged_user()["user_id"],
                email=NEW_EMAIL,
                code=VERIFICATION_CODE,
                time=now,
            )
        ]
    )


def extended_pending_users() -> list[EmailPending]:
    return deepcopy(
        pending_users()
        + [
            EmailPending(
                user_id=valid_user()["user_id"],
                email=NEW_EMAIL,
                code=VERIFICATION_CODE,
                time=now,
            )
        ]
    )
