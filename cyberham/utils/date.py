from datetime import datetime
from pytz import timezone
from cyberham.database.types import Semester


# central timezone
cst_tz = timezone("US/Central")

def to_central_time(dt: datetime) -> datetime:
    return dt.astimezone(cst_tz)


def format_central_time(dt: datetime) -> str:
    return to_central_time(dt).strftime("%I:%M%p").lstrip("0").replace(" 0", " ")


def datetime_to_datestr(dt: datetime) -> str:
    return dt.date().strftime("%m/%d/%Y")


def datestr_to_datetime(datestr: str) -> datetime:
    return datetime.strptime(datestr, "%m/%d/%Y")


def current_semester() -> Semester:
    if datetime.now().month <= 6:
        return "spring"
    return "fall"


def current_year() -> int:
    return datetime.now().year
