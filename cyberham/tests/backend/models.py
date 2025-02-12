from datetime import datetime
from pytz import timezone
from cyberham.dynamodb.types import User, Event

cst_tz = timezone("America/Chicago")
today = datetime.now(cst_tz).date().strftime("%m/%d/%Y")
yesterday = datetime.now(cst_tz).date().strftime("%m/%d/%Y")
tomorrow = datetime.now(cst_tz).date().strftime("%m/%d/%Y")

valid_user = User(
    points=100,
    attended=5,
    user_id="0",
    name="Lane",
    grad_year=2024,
    email="lane@tamu.edu",
)
no_grad_year_user = User(
    points=200,
    attended=1,
    user_id="1",
    name="Colby",
    grad_year=0,
    email="colby@tamu.edu",
)
no_email_user = User(
    points=50,
    attended=50,
    user_id="2",
    name="Damian",
    grad_year=2026,
    email="",
)
user4 = User(
    points=0,
    attended=15,
    user_id="3",
    name="Stella",
    grad_year=2025,
    email="stella@tamu.edu",
)
user5 = User(
    points=1000,
    attended=0,
    user_id="4",
    name="Emma",
    grad_year=2027,
    email="emma@tamu.edu",
)
unregistered_user = User(
    points=1000000,
    attended=0,
    user_id="9",
    name="Owen",
    grad_year=2027,
    email="owen@tamu.edu",
)

current_event = Event(
    name="AWS Academy",
    code="AWSAC",
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
event4 = Event(
    name="Cisco Networking Academy",
    code="CISCO",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)
event5 = Event(
    name="Hardware Hacking",
    code="HRDHK",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)
unregistered_event = Event(
    name="Hack the Box",
    code="HKBOX",
    points=50,
    date=today,
    resources="",
    attended_users=[],
)

users = [valid_user, no_grad_year_user, no_email_user, user4, user5]
events = [current_event, past_event, future_event, event4, event5]
