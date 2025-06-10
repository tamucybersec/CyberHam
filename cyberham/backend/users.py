from typing import Literal

from cyberham.database.typeddb import usersdb, eventsdb, pointsdb
from cyberham.database.types import User, MaybeUser, Points, MaybePoints
from cyberham.database.queries import (
    attendance_for_all_users,
    points_for_all_users,
    user_attendance_counts_for_events,
)
from cyberham.utils.date import current_semester, current_year


def leaderboard(
    sort_by: Literal["points", "attended"], limit: int = 10
) -> list[tuple[User, int]]:
    users = usersdb.get_all()

    if sort_by == "points":
        stats = points_for_all_users()
    else:
        stats = attendance_for_all_users()

    filtered_users = [user for user in users if stats.get(user["user_id"], 0) > 0]
    filtered_users.sort(key=lambda user: stats.get(user["user_id"], 0), reverse=True)
    return [(user, stats.get(user["user_id"], 0)) for user in filtered_users[:limit]]


def leaderboard_search(activity: str) -> list[tuple[str, int]]:
    """
    Gets a ranked list of users' names who attended the most meetings that contain the string activity
    """

    events = eventsdb.get_all()
    codes: list[str] = []

    # get codes
    for event in events:
        if activity.lower() in event["name"].lower():
            codes.append(event["code"])

    # get sorted list of ids based on attendance
    attendance = user_attendance_counts_for_events(codes)
    user_ids = [(user_id,) for user_id in attendance.keys()]
    user_ids.sort(key=lambda user_id: attendance[user_id[0]], reverse=True)
    users = usersdb.get_batch(user_ids)

    # map ids to names
    leaderboard: list[tuple[str, int]] = []
    for user in users:
        if user is not None:
            entry = (user["name"], attendance[user["user_id"]])
            leaderboard.append(entry)

    return leaderboard


def profile(user_id: int) -> tuple[str, MaybeUser]:
    user = usersdb.get((user_id,))

    if user is None:
        return "Your profile does not exist.", None

    return "", user


def award(user_id: int, user_name: str, points: int) -> str:
    user = usersdb.get((user_id,))
    if user is None:
        return "This user has not registered yet!"

    def update_points(pts: MaybePoints) -> MaybePoints:
        if pts is None:
            return Points(
                user_id=user_id,
                points=points,
                semester=current_semester(),
                year=current_year(),
            )
        else:
            pts["points"] += points
            return pts

    pointsdb.update(
        update_points, pk_values=(user_id, current_semester(), current_year())
    )

    return f"Successfully added {points} points to {user_name} {user["name"]}."
