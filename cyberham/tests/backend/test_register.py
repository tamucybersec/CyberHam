# FIXME needs rewrite with new registration method

# from backend_patcher import BackendPatcher
# from cyberham.backend.register import legacy_register
# from cyberham.types import User
# from cyberham.tests.models import (
#     users,
#     valid_user,
#     flagged_user,
#     unregistered_user,
#     pending_verifies,
#     flagged_users,
# )
# from cyberham.database.typeddb import usersdb

# ignore the response from register email for these tests
# class TestRegister(BackendPatcher):
#     def setup_method(self):
#         self.initial_users = users()
#         self.initial_flagged = flagged_users()
#         self.initial_pending = pending_verifies()
#         super().setup_method()

#     def test_register(self):
#         self._assert_working(unregistered_user())

#     def test_flagged_user(self):
#         self._assert_working(flagged_user())

#     def _assert_working(self, user: User):
#         res = legacy_register(
#             user["name"],
#             str(user["grad_year"]),
#             user["email"],
#             user["user_id"],
#         )
#         assert res != ""

#         u = usersdb.get((user["user_id"],))
#         assert u is not None
#         assert u == user

#     def test_unparsable_date(self):
#         res = legacy_register(
#             unregistered_user()["name"],
#             "hello world",
#             unregistered_user()["email"],
#             unregistered_user()["user_id"],
#         )
#         assert res != ""

#         user = usersdb.get((unregistered_user()["user_id"],))
#         assert user is None, "Should not create user"

#     def test_invalid_date(self):
#         res = legacy_register(
#             unregistered_user()["name"],
#             "0",
#             unregistered_user()["email"],
#             unregistered_user()["user_id"],
#         )
#         assert res != ""

#         user = usersdb.get((unregistered_user()["user_id"],))
#         assert user is None, "Should not create user"

#     def test_invalid_emails(self):
#         emails = [
#             "",
#             "exam,ple@tamu.edu",
#             "exam;ple@tamu.edu",
#             "example.tamu.edu",
#             "exam@ple@tamu.edu",
#             "example@tamu.edu.",
#         ]

#         for email in emails:
#             res = legacy_register(
#                 unregistered_user()["name"],
#                 str(unregistered_user()["grad_year"]),
#                 email,
#                 unregistered_user()["user_id"],
#             )
#             assert res != ""

#             user = usersdb.get((unregistered_user()["user_id"],))
#             assert (
#                 user is None
#             ), f"Should not create user because email '{email}' is invalid"

#     def test_already_registered(self):
#         res = legacy_register(
#             valid_user()["name"],
#             str(valid_user()["grad_year"]),
#             valid_user()["email"],
#             valid_user()["user_id"],
#         )
#         assert res != ""

#         user = usersdb.get((valid_user()["user_id"],))
#         assert (
#             user == valid_user()
#         ), "Should not remove attributes like points or attended"

#     def test_update_information(self):
#         new_name = valid_user()["name"] + "_but_cooler"
#         new_grad = valid_user()["grad_year"] - 1
#         new_email = "cooler_" + valid_user()["email"]

#         res = legacy_register(
#             new_name,
#             str(new_grad),
#             new_email,
#             valid_user()["user_id"],
#         )
#         assert res != ""

#         user = usersdb.get((valid_user()["user_id"],))
#         assert user is not None
#         assert user["name"] == new_name
#         assert user["grad_year"] == new_grad
#         assert user["email"] == new_email
#         assert user["user_id"] == valid_user()["user_id"]
