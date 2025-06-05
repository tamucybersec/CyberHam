from typing import Literal

from cyberham.database.typeddb import usersdb, eventsdb
from cyberham.database.types import (
    User,
    MaybeUser,
)
from cyberham.utils.events import attendees


def leaderboard(sort_by: Literal["points", "attended"], lim: int = 10) -> list[User]:
    users = usersdb.get_all()

    if sort_by == "points":
        users.sort(key=lambda user: user["points"], reverse=True)
    else:
        users.sort(key=lambda user: user["attended"], reverse=True)

    return users[:lim]


# FIXME inefficient
# fetch all users at once or individually? implement a batch get
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
        for user_id in attendees(event):
            if user_id in counts:
                counts[user_id] += 1
            else:
                counts[user_id] = 1

    # map ids to names
    leaderboard: list[tuple[str, int]] = []
    for user_id, count in counts.items():
        user = usersdb.get([user_id])

        if user is not None:
            leaderboard.append((user["name"], count))

        # raise Exception(f"User {user_id} is in events but not in users.")

    return leaderboard


def profile(user_id: int) -> tuple[str, MaybeUser]:
    user = usersdb.get([user_id])

    if user is None:
        return "Your profile does not exist.", None

    return "", user


def award(user_id: int, user_name: str, points: int) -> str:
    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["points"] += points
        return user

    user = usersdb.update(update_user, pk_values=[user_id])

    if user is None:
        return "This user has not registered yet!"
    return f"Successfully added {points} points to {user_name} {user["name"]}."
