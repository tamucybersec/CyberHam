from datetime import datetime, timedelta
from pytz import timezone
from cyberham.dynamodb.types import User, Event

cst_tz = timezone("America/Chicago")
now = datetime.now(cst_tz).date()
today = now.strftime("%m/%d/%Y")
yesterday = (now - timedelta(days=1)).strftime("%m/%d/%Y")
tomorrow = (now + timedelta(days=1)).strftime("%m/%d/%Y")


valid_user = User(
    points=100,
    attended=5,
    user_id=0,
    name="Lane",
    grad_year=2024,
    email="lane@tamu.edu",
)
valid_user_2 = User(
    points=0,
    attended=15,
    user_id=1,
    name="Stella",
    grad_year=2025,
    email="stella@tamu.edu",
)
updated_user = User(
    points=1000,
    attended=0,
    user_id=2,
    name="Emma",
    grad_year=2027,
    email="emma@tamu.edu",
)
updated_user_2 = User(
    points=200,
    attended=1,
    user_id=3,
    name="Colby",
    grad_year=0,
    email="colby@tamu.edu",
)
no_grad_year_user = User(
    points=50,
    attended=50,
    user_id=4,
    name="Damian",
    grad_year=2026,
    email="",
)
no_email_user = User(
    points=1000000,
    attended=0,
    user_id=5,
    name="Owen",
    grad_year=2027,
    email="",
)
unregistered_user = User(
    points=1000000,
    attended=0,
    user_id=9,
    name="Owen",
    grad_year=2027,
    email="owen@tamu.edu",
)

valid_user_item = dict(valid_user)
valid_user_2_item = dict(valid_user_2)
updated_user_item = dict(updated_user)
updated_user_2_item = dict(updated_user_2)
no_grad_year_user_item = dict(no_grad_year_user)
no_email_user_item = dict(no_email_user)
unregistered_user_item = dict(unregistered_user)
users = [
    valid_user,
    valid_user_2,
    updated_user,
    updated_user_2,
    no_grad_year_user,
    no_email_user,
]
ids = [user["user_id"] for user in users]
fewer_ids = [valid_user["user_id"], valid_user_2["user_id"]]

valid_event = Event(
    name="AWS Academy",
    code="AWSAC",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)
valid_event_2 = Event(
    name="Hardware Hacking",
    code="HRDHK",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)
past_event = Event(
    name="Red Hat Academy",
    code="RDHAT",
    points=50,
    date=yesterday,
    resources="",
    attended_users=[],
)
future_event = Event(
    name="Palo Alto Academy",
    code="PALAL",
    points=50,
    date=tomorrow,
    resources="",
    attended_users=[],
)
attended_event = Event(
    name="Cisco Networking Academy",
    code="CISCO",
    points=50,
    date=today,
    resources="",
    attended_users=ids,
)
attended_event_2 = Event(
    name="Cisco Networking Academy",
    code="CISC2",
    points=50,
    date=today,
    resources="",
    attended_users=fewer_ids,
)
unregistered_event = Event(
    name="Hack the Box",
    code="HKBOX",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)


events = [
    valid_event,
    valid_event_2,
    past_event,
    future_event,
    attended_event,
    attended_event_2,
]
