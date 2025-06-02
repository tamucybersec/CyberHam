from cyberham.database.types import Event


def user_attended(event: Event, user_id: int) -> bool:
    users = attendees(event)
    return user_id in users


def add_attendee(event: Event, user_id: int):
    if event["attended_users"] == "":
        event["attended_users"] = f"{user_id}"
    else:
        event["attended_users"] += f",{user_id}"


def attendees(event: Event) -> list[int]:
    spl = [] if event["attended_users"] == "" else event["attended_users"].split(",")
    return [int(id) for id in spl]
