from datetime import datetime, timedelta
from pytz import timezone
from cyberham.database.types import User, Event, Flagged, Attendance, Points
from cyberham.apis.types import EmailPending
from cyberham.utils.date import current_semester, current_year

cst_tz = timezone("America/Chicago")
now = datetime.now(cst_tz).date()
today = now.strftime("%m/%d/%Y")
yesterday = (now - timedelta(days=1)).strftime("%m/%d/%Y")
tomorrow = (now + timedelta(days=1)).strftime("%m/%d/%Y")


valid_user = User(
    user_id=0,
    name="Lane",
    grad_year=2024,
    email="lane@tamu.edu",
    verified=True,
)
valid_user_2 = User(
    user_id=1,
    name="Stella",
    grad_year=2025,
    email="stella@tamu.edu",
    verified=True,
)
updated_user = User(
    user_id=2,
    name="Emma",
    grad_year=2027,
    email="emma@tamu.edu",
    verified=True,
)
updated_user_2 = User(
    user_id=3,
    name="Colby",
    grad_year=0,
    email="colby@tamu.edu",
    verified=True,
)
flagged_user = User(
    user_id=4,
    name="Damian",
    grad_year=2026,
    email="",
    verified=True,
)
no_email_user = User(
    user_id=5,
    name="Javi",
    grad_year=2027,
    email="",
    verified=True,
)
unregistered_user = User(
    user_id=9,
    name="Owen",
    grad_year=2027,
    email="owen@tamu.edu",
    verified=True,
)
unregistered_user_2 = User(
    user_id=10,
    name="Zach",
    grad_year=2027,
    email="zach@tamu.edu",
    verified=True,
)

valid_user_item = dict(valid_user)
valid_user_2_item = dict(valid_user_2)
unregistered_user_item = dict(unregistered_user)
users = [
    valid_user,
    valid_user_2,
    updated_user,
    updated_user_2,
    flagged_user,
    no_email_user,
]
ids = ",".join([str(user["user_id"]) for user in users])
fewer_ids = ",".join([str(valid_user["user_id"]), str(valid_user_2["user_id"])])

valid_event = Event(
    name="AWS Academy",
    code="AWSAC",
    points=50,
    date=today,
    semester=current_semester(),
    year=current_year(),
)
valid_event_2 = Event(
    name="Hardware Hacking",
    code="HRDHK",
    points=50,
    date=today,
    semester=current_semester(),
    year=current_year(),
)
past_event = Event(
    name="Red Hat Academy",
    code="RDHAT",
    points=50,
    date=yesterday,
    semester=current_semester(),
    year=current_year(),
)
future_event = Event(
    name="Palo Alto Academy",
    code="PALAL",
    points=50,
    date=tomorrow,
    semester=current_semester(),
    year=current_year(),
)
attended_event = Event(
    name="Cisco Networking Academy",
    code="CISCO",
    points=50,
    date=today,
    semester=current_semester(),
    year=current_year(),
)
attended_event_2 = Event(
    name="Cisco Networking Academy",
    code="CISC2",
    points=50,
    date=today,
    semester=current_semester(),
    year=current_year(),
)
unregistered_event = Event(
    name="Hack the Box",
    code="HKBOX",
    points=50,
    date=today,
    semester=current_semester(),
    year=current_year(),
)


events = [
    valid_event,
    valid_event_2,
    past_event,
    future_event,
    attended_event,
    attended_event_2,
]

flagged_users = [
    Flagged(
        user_id=flagged_user["user_id"],
        offenses=3,
    ),
]

NEW_EMAIL = "NEW_EMAIL@tamu.edu"
VERIFICATION_CODE = 1234

attendance: list[Attendance] = [
    Attendance(user_id=valid_user["user_id"], code=attended_event["code"]),
    Attendance(user_id=valid_user_2["user_id"], code=attended_event["code"]),
]

points: list[Points] = [
    Points(
        user_id=valid_user["user_id"],
        points=100,
        semester=current_semester(),
        year=current_year(),
    ),
    Points(
        user_id=valid_user_2["user_id"],
        points=1000,
        semester=current_semester(),
        year=current_year(),
    ),
    Points(
        user_id=updated_user["user_id"],
        points=0,
        semester=current_semester(),
        year=current_year(),
    ),
    # update_user_2 skip for edge case detection
    Points(
        user_id=no_email_user["user_id"],
        points=10,
        semester=current_semester(),
        year=current_year(),
    ),
]

pending_users = [
    EmailPending(
        user_id=flagged_user["user_id"],
        email=NEW_EMAIL,
        code=VERIFICATION_CODE,
        time=datetime.now(),
    )
]

extended_pending_users: list[EmailPending] = pending_users + [
    EmailPending(
        user_id=valid_user["user_id"],
        email=NEW_EMAIL,
        code=VERIFICATION_CODE,
        time=datetime.now(),
    )
]
