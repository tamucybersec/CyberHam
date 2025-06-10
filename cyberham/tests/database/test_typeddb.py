import pytest
from cyberham.database.types import MaybeUser
from cyberham.tests.models import (
    valid_user,
    valid_user_2,
    unregistered_user,
    unregistered_user_2,
)
from cyberham.tests.backend.backend_patcher import BackendPatcher
from cyberham.database.typeddb import usersdb


class TestTypedDB(BackendPatcher):
    def setup_method(self):
        self.initial_users = [valid_user(), valid_user_2()]
        super().setup_method()

    def test_create_item(self):
        usersdb.create(unregistered_user())
        after = usersdb.get([unregistered_user()["user_id"]])
        assert after == unregistered_user()

    def test_create_item_fails_overwrite(self):
        with pytest.raises(Exception):
            usersdb.create(valid_user())

    def test_get_item(self):
        item = usersdb.get([valid_user()["user_id"]])
        assert item and valid_user() == item

    def test_get_non_existent_item(self):
        item = usersdb.get([unregistered_user()["user_id"]])
        assert item is None

    def test_update_item_using_pk(self):
        # create
        item = usersdb.update(
            _test_update_func, pk_values=[unregistered_user()["user_id"]]
        )
        assert item == unregistered_user()

        # update
        item = usersdb.update(
            _test_update_func, pk_values=[unregistered_user()["user_id"]]
        )
        assert item == unregistered_user_2()

        # delete
        item = usersdb.update(
            _test_update_func, pk_values=[unregistered_user_2()["user_id"]]
        )
        assert item is None

    def test_update_item_using_original(self):
        # create
        usersdb.create(unregistered_user())

        # update
        item = usersdb.update(_test_update_func, original=unregistered_user())
        assert item == unregistered_user_2()

        # delete
        item = usersdb.update(_test_update_func, original=unregistered_user_2())
        assert item is None

    def test_delete_item(self):
        old_item = usersdb.delete([valid_user()["user_id"]])
        assert old_item == valid_user()

    def test_delete_non_existent_item(self):
        old_item = usersdb.delete([unregistered_user()["user_id"]])
        assert old_item is None

    def test_get_all_items(self):
        items = usersdb.get_all()
        got = sorted(items, key=lambda item: item["user_id"])
        expected = sorted(
            [
                valid_user(),
                valid_user_2(),
            ],
            key=lambda item: str(item["user_id"]),
        )
        assert got == expected

    def test_get_count(self):
        assert usersdb.get_count() == 2


def _test_update_func(item: MaybeUser) -> MaybeUser:
    if item is None:
        return unregistered_user()
    elif item == unregistered_user():
        return unregistered_user_2()
    else:
        return None
