import random
from uuid import uuid4
from datetime import datetime

from cyberham import website_url
from cyberham.apis.google_apis import google
from cyberham.database.typeddb import usersdb, flaggeddb, registerdb, verifydb
from cyberham.database.queries import insert_registration
from cyberham.types import (
    User,
    MaybeUser,
    Flagged,
    MaybeFlagged,
    Error,
    MaybeError,
    Register,
    Verify,
)
from cyberham.utils.date import (
    datetime_to_datestr,
    valid_registration_time,
)
from fastapi import UploadFile
import os
import aiofiles


async def upload_resume(user_id: str, resume: UploadFile) -> tuple[str, str, bool]:
    try:
        os.makedirs("resumes", exist_ok=True)

        # get original filename
        filename = resume.filename
        if filename is None:
            return "", "", False
        filename = os.path.basename(filename) # to prevent unwanted path traversal
        # get file format
        format = os.path.splitext(filename)[-1].lstrip(".").lower()
        if not format:
            return "", "", False

        # Write the file to disk at resumes/{user_id}
        path = os.path.join("resumes", user_id)
        async with aiofiles.open(path, "wb") as out_file:
            content = await resume.read()
            await out_file.write(content)

        return filename, format, True

    except Exception as e:
        print(f"Upload failed for user {user_id}: {e}")
        return "", "", False


def register(ticket: str, user: User) -> tuple[str, MaybeError]:
    registration = registerdb.get((ticket,))
    if registration is None:
        return "", Error(
            "You have no registration pending. Use /register to get a link first."
        )
    if registration["user_id"] != user["user_id"]:
        return "", Error(
            "Your registration link is invalid. Get a new link with /register."
        )
    if not valid_registration_time(registration["time"]):
        return "", Error(
            "Your registration has expired. Get a new link with /register."
        )

    def update_user(u: MaybeUser) -> MaybeUser:
        if u is None:
            user["join_date"] = datetime_to_datestr(datetime.now())
            return user

        # shouldn't change on register
        user["notes"] = u["notes"]
        if not u["join_date"]:
            user["join_date"] = datetime_to_datestr(datetime.now())

        verified = u["email"] == user["email"] and user["verified"]
        user["verified"] = 1 if verified else 0
        return user

    usersdb.update(update_user, pk_values=(user["user_id"],))
    registerdb.delete((registration["ticket"],))
    return register_email(user["user_id"], user["email"])


def generate_registration_url(user_id: str) -> str:
    ticket = uuid4()
    registration = Register(
        user_id=user_id,
        ticket=str(ticket),
        time=datetime.now().isoformat(),
    )
    insert_registration(registration)
    return f"{website_url}/register?ticket={ticket}"



# NOTE update's a user's email if it differs from their original email
def register_email(user_id: str, email: str) -> tuple[str, MaybeError]:
    user = usersdb.get((user_id,))
    if user is not None and user["email"] == email and user["verified"]:
        return "", None

    # check offenses
    if verifydb.get((user_id,)) is not None:

        def update_flagged(flagged: MaybeFlagged) -> MaybeFlagged:
            if flagged is None:
                return Flagged(user_id=user_id, offenses=1)
            else:
                flagged["offenses"] += 1
                return flagged

        flagged = flaggeddb.update(update_flagged, pk_values=(user_id,))

        if flagged is not None and flagged["offenses"] >= 3:
            return "", Error(
                "Too many failed attempts for/without email verification, please contact an officer."
            )

    # send email
    verification = Verify(
        user_id=user_id,
        code=random.randint(1000, 10000),
    )
    verifydb.update(lambda _: verification, pk_values=(user_id,))

    google.client.send_email(
        email,
        str(verification["code"]),
        "Texas A&M Cybersecurity Club",
    )

    return (
        "Please use /verify with the code you received in your email. Be sure the check your spam folder as well. Subject: CyberHam Verification Code",
        None,
    )


def verify_email(code: int, user_id: str) -> str:
    user = usersdb.get((user_id,))
    if user is None:
        return "Please use /register first."
    verification = verifydb.get((user_id,))
    if not verification:
        return "Please use /register to set your email first."

    if verification["code"] != code:
        return "This code is not correct!"

    def update_user(user: MaybeUser) -> MaybeUser:
        if user is not None:
            user["verified"] = True
        return user

    usersdb.update(update_user, original=user)
    flaggeddb.delete((verification["user_id"],))
    verifydb.delete((verification["user_id"],))
    return "Email verified! It is now visible using /profile."


def remove_pending(user_id: str) -> None:
    verifydb.delete((user_id,))
