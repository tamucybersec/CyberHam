from datetime import datetime
from cyberham.dynamodb.types import Response, User, RegistrationStatus
from cyberham.dynamodb.usersdb import usersdb


# register
def register(
    name: str, grad_year: int, email: str, user_id: int, user_name: str, guild_id: int
) -> Response:
    """
    Register for the club.
    """
    _: User = usersdb.get_user(user_id)

    if not valid_grad_year(grad_year):
        return registration_response_fail(
            "Please set your graduation year in the format YYYY (e.g. 2022)"
        )
    if not valid_email(email):
        return registration_response_fail("Please set a proper TAMU email address")

    status: RegistrationStatus = register_email(email, user_id, guild_id)

    return registration_response(
        f"You have successfully updated your profile! {status.message}"
    )


def valid_grad_year(year: int) -> bool:
    now = datetime.now()
    return now.year - 100 < year < now.year + 8


def valid_email(email: str) -> bool:
    return (
        "," in email
        or ";" in email
        or email.count("@") != 1
        or not email.endswith("tamu.edu")
    )


# register_email
def register_email(email: str, user_id: int, guild_id: int) -> RegistrationStatus:
    user: User = usersdb.get_user(user_id)

    if user_with_email_exists(user, email):
        return registration_status("")

    if user_in_pending(user):
        offense_count: int = update_offense_count()

        if offense_count >= 3:
            return registration_status_fail(
                "Too many failed attempts for email verification. Please contact an officer."
            )
        else:
            return registration_status_fail("This email has already been registered.")

    send_verification_email()

    return registration_status(
        "Please use /verify with the code you received in your email."
    )


def registration_status_fail(message: str) -> RegistrationStatus:
    return RegistrationStatus(message, "warning")


def registration_status(message: str) -> RegistrationStatus:
    return RegistrationStatus(message, "successful")


def user_with_email_exists(user: User, email: str) -> bool:
    return user is not None and user.email == email


def update_offense_count() -> int:
    return 0


def send_verification_email() -> None:
    # TODO
    pass


# verify_email
def verify_email(code: int, user_id: int) -> Response:
    user: User = usersdb.get_user(user_id) # TODO: temp value

    if not user_in_pending(user):
        return registration_response_fail("Please use /register to submit your email")

    if not verification_code_matches():
        return registration_response_fail("This code is not correct!")

    complete_verification()

    return registration_response("Email verified! It is now visible on your /profile")


def registration_response_fail(message: str) -> Response:
    return registration_response(message)


def registration_response(message: str) -> Response:
    return Response(message)


def user_in_pending(user: User) -> bool:
    # TODO
    return False


def verification_code_matches() -> bool:
    # TODO
    return False


def complete_verification() -> None:
    # TODO
    # Update user and remove from pending
    pass


# remove_pending
def remove_pending(user_id: int) -> None:
    # TODO
    pass
