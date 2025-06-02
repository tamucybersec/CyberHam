import pytest
from cyberham.database.types import MaybeUser
from cyberham.tests.models import (
    valid_user,
    valid_user_2,
    unregistered_user,
    unregistered_user_2,
)
from cyberham.database.typeddb import testdb

pk_name = "user_id"


class TestTypedDB:
    @pytest.fixture(autouse=True)
    def setup_database(self):
        testdb.reset()
        testdb.create(valid_user)
        testdb.create(valid_user_2)

    def test_create_item(self):
        testdb.create(unregistered_user)
        after = testdb.get([unregistered_user[pk_name]])
        assert after == unregistered_user

    def test_create_item_fails_overwrite(self):
        with pytest.raises(Exception):
            testdb.create(valid_user)

    def test_get_item(self):
        item = testdb.get([valid_user[pk_name]])
        assert item and valid_user == item

    def test_get_non_existent_item(self):
        item = testdb.get([unregistered_user[pk_name]])
        assert item is None

    def test_update_item_using_pk(self):
        # create
        item = testdb.update(_test_update_func, pk_values=[unregistered_user[pk_name]])
        assert item == unregistered_user

        # update
        item = testdb.update(_test_update_func, pk_values=[unregistered_user[pk_name]])
        assert item == unregistered_user_2

        # delete
        item = testdb.update(
            _test_update_func, pk_values=[unregistered_user_2[pk_name]]
        )
        assert item is None

    def test_update_item_using_original(self):
        # create
        testdb.create(unregistered_user)

        # update
        item = testdb.update(_test_update_func, original=unregistered_user)
        assert item == unregistered_user_2

        # delete
        item = testdb.update(_test_update_func, original=unregistered_user_2)
        assert item is None

    def test_delete_item(self):
        old_item = testdb.delete([valid_user[pk_name]])
        assert old_item == valid_user

    def test_delete_non_existent_item(self):
        old_item = testdb.delete([unregistered_user[pk_name]])
        assert old_item is None

    def test_get_all_items(self):
        items = testdb.get_all()
        got = sorted(items, key=lambda item: item["user_id"])
        expected = sorted(
            [
                valid_user,
                valid_user_2,
            ],
            key=lambda item: str(item["user_id"]),
        )
        assert got == expected

    def test_get_count(self):
        assert testdb.get_count() == 2


def _test_update_func(item: MaybeUser) -> MaybeUser:
    if item is None:
        return unregistered_user
    elif item == unregistered_user:
        return unregistered_user_2
    else:
        return None
