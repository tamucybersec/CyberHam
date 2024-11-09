'''
create event
attend event
find event
event list
'''

from datetime import datetime, date
from typing import Any
from helper import get_user, get_event
from types import Attendance, AttendanceData, User, Event

def attend_event(code: str, user_id: int, user_name: str) -> Attendance:
	"""
	Register a user as attending an event.

	Returns a message and the attendance data, if successful.
	"""

	code = code.upper()
	user: User = get_user()
	event: Event = get_event()

	if user is None:
		return attendance_response_fail("Please user /register to make a profile!")
	if event is None:
		return attendance_response_fail(f"{code} does not exist!")
	if user_in_attended():
		return attendance_response_fail(f"You have already redeemed {code}!")
	if not event_today():
		return attendance_response_fail(f"You must redeem an event on the day it occurs!")

	update_points()
	update_num_attended()
	update_attended()

	return attendance_response(f"Successfully registered for {code}!", "", 0, datetime.now(), "")

def attendance_response_fail(message: str) -> Attendance:
	return Attendance(message, None)

def attendance_response(message: str, name: str, points: int, date: date, resources: Any) -> Attendance:
	return Attendance(message, data=AttendanceData(name, points, date, resources))

def user_in_attended() -> bool:
	# TODO
	return False

def event_today() -> bool:
	# TODO
	return False

def update_points() -> None:
	# TODO
	# Update the points for a user
	pass

def update_num_attended() -> None:
	# TODO
	# Update the number of events attended by the user
	pass

def update_attended() -> None:
	# TODO
	# Update the list of attended for the event 
	pass