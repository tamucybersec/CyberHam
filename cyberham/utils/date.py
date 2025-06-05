import datetime
from pytz import timezone


def to_central_time(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(timezone("US/Central"))


def format_central_time(dt: datetime.datetime) -> str:
    return to_central_time(dt).strftime("%I:%M%p").lstrip("0").replace(" 0", " ")


def datetime_to_datestr(dt: datetime.datetime) -> str:
    return ""  # TODO


def datestr_to_datetime(datestr: str) -> datetime.datetime:
    return datetime.datetime.now()  # TODO
