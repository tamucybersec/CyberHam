import random

from datetime import datetime

from cyberham.apis.google_apis import google
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
    user_id: str,
) -> str:
    year = datetime.now().year

    # validate grad year
    try:
        grad_year = int(grad_year_str)
    except ValueError:
        return f"Please set your graduation year in the format YYYY (e.g. {year})."

    if not year - 100 < grad_year < year + 8:
        return f"Please set your graduation year in the format YYYY (e.g. {year})."

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
                grad_year=grad_year,
                email=email,
                verified=True,
            )
        else:
            user["name"] = name
            user["grad_year"] = grad_year
            if email != user["email"]:
                user["email"] = email
                user["verified"] = False
            return user

    usersdb.update(update, pk_values=(user_id,))

    return f"You have successfully updated your profile! {ask_to_verify}"


# NOTE update's a user's email if it differs from their original email
def register_email(user_id: str, email: str) -> str:
    user = usersdb.get((user_id,))
    if user is not None and user["email"] == email:
        return ""

    # check offenses
    if google.client.has_pending_email(user_id):

        def update_flagged(flagged: MaybeFlagged) -> MaybeFlagged:
            if flagged is None:
                return Flagged(user_id=user_id, offenses=1)
            else:
                flagged["offenses"] += 1
                return flagged

        flagged = flaggeddb.update(update_flagged, pk_values=(user_id,))

        if flagged is not None and flagged["offenses"] >= 3:
            return "Too many failed attempts to email verification, please contact an officer."

    # send email
    verification = EmailPending(
        user_id=user_id,
        email=email,
        code=random.randint(1000, 10000),
        time=datetime.now(),
    )
    google.client.set_pending_email(user_id, verification)

    google.client.send_email(
        email,
        str(verification["code"]),
        "Texas A&M Cybersecurity Club",
    )

    return "Please use /verify with the code you received in your email. Be sure the check your spam folder as well."


def verify_email(code: int, user_id: str) -> str:
    user = usersdb.get((user_id,))
    if user is None:
        return "Please use /register first."
    elif not google.client.has_pending_email(user_id):
        return "Please use /register to set your email first."

    pending = google.client.get_pending_email(user_id)
    if pending["code"] != code:
        return "This code is not correct!"

    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["email"] = pending["email"]  # in case the email is being updated
            user["verified"] = True
        return user

    usersdb.update(update_user, original=user)

    google.client.remove_pending_email(user_id)
    return "Email verified! It is now visible using /profile."


def remove_pending(user_id: str) -> None:
    google.client.remove_pending_email(user_id)
