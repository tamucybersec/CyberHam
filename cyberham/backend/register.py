import random

from datetime import datetime

from cyberham.apis.google_apis import google_client
from cyberham.apis.types import EmailPending
from cyberham.database.typeddb import usersdb, flaggeddb
from cyberham.database.types import (
    User,
    MaybeUser,
    Flagged,
    MaybeFlagged,
)


# NOTE register can also update a user's information
def register(
    name: str,
    grad_year_str: str,
    email: str,
    user_id: int,
) -> str:
    # validate grad year
    try:
        grad_year = int(grad_year_str)
    except ValueError:
        return "Please set your graduation year in the format YYYY (e.g. 2022)."

    if not datetime.now().year - 100 < grad_year < datetime.now().year + 8:
        return "Please set your graduation year in the format YYYY (e.g. 2022)."

    # validate email
    email = email.lower()
    if (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    ):
        return "Please use a proper TAMU email address."

    ask_to_verify: str = register_email(user_id, email)

    # update user information
    def update(user: MaybeUser) -> MaybeUser:
        if user is None:
            return User(
                user_id=user_id,
                name=name,
                points=0,
                attended=0,
                grad_year=grad_year,
                email=email,
            )
        else:
            user["name"] = name
            user["grad_year"] = grad_year
            user["email"] = email
            return user

    usersdb.update(update, pk_values=[user_id])

    return f"You have successfully updated your profile! {ask_to_verify}"


# NOTE update's a user's email if it differs from their original email
def register_email(user_id: int, email: str) -> str:
    user = usersdb.get([user_id])
    if user is not None and user["email"] == email:
        return ""

    # check offenses
    if google_client.has_pending_email(user_id):

        def update_flagged(flagged: MaybeFlagged) -> MaybeFlagged:
            if flagged is None:
                flagged = Flagged(user_id=user_id, offences=1)
            else:
                flagged["offences"] += 1
            return flagged

        flagged = flaggeddb.update(update_flagged, pk_values=[user_id])

        if flagged is not None and flagged["offences"] >= 3:
            return "Too many failed attempts to email verification, please contact an officer."

    # send email
    verification = EmailPending(
        user_id=user_id,
        email=email,
        code=random.randint(1000, 10000),
        time=datetime.now(),
    )
    google_client.set_pending_email(user_id, verification)

    google_client.send_email(
        email,
        str(verification["code"]),
        "Texas A&M Cybersecurity Club",
    )

    return "Please use /verify with the code you received in your email. Be sure the check your spam folder as well."


def verify_email(code: int, user_id: int) -> str:
    user = usersdb.get([user_id])
    if user is None:
        return "Please use /register first."
    elif not google_client.has_pending_email(user_id):
        return "Please use /register to set your email first."

    pending = google_client.get_pending_email(user_id)
    if pending["code"] != code:
        return "This code is not correct!"

    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["email"] = pending["email"]
        return user

    usersdb.update(update_user, original=user)

    google_client.remove_pending_email(user_id)
    return "Email verified! It is now visible using /profile."


def remove_pending(user_id: int = 0) -> None:
    google_client.remove_pending_email(user_id)
