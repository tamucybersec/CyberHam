'''
leaderboard
leaderboard search
profile
award
'''

from cyberham.dynamodb.helper import get_user
from cyberham.dynamodb.types import Axis, Leaderboard, User

def leaderboard(axis: Axis, limit: int = 10) -> Leaderboard:
	"""
	Get the leaderboard for the club on either a point or attendance basis.
	"""

	if axis == "points":
		return points_leaderboard(limit)
	else:
		return attended_leaderboard(limit)

def points_leaderboard(limit: int) -> Leaderboard:
	# TODO
	return dummy_leaderboard()

def attended_leaderboard(limit: int) -> Leaderboard:
	# TODO
	return dummy_leaderboard()

def dummy_leaderboard() -> Leaderboard:
	return Leaderboard(x_title="", x=[], y_title="", y=[])