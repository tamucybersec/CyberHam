from cyberham.dynamodb.types import MaybeUser
from cyberham.tests.models import (
    valid_user,
    valid_user_2,
    updated_user,
    updated_user_2,
    unregistered_user,
)
from cyberham.dynamodb.typeddb import testdb


class TestTypedDB:
    def test_get_item(self):
        item = testdb.get(valid_user["user_id"])
        print(valid_user)
        print(item)
        assert valid_user == item
        assert (
            item and valid_user == item
        ), "Get should return the item with the given partition key"

    def test_get_all_items(self):
        items = testdb.get_all()
        assert sorted(
            items,
            key=lambda user: user["user_id"],
        ) == sorted(
            [valid_user, valid_user_2],
            key=lambda user: user["user_id"],
        ), "Get All should return all items in the database"

    def test_get_non_existent_item(self):
        item = testdb.get(unregistered_user["user_id"])
        assert (
            item is None
        ), "Get should not return if the item with the given partition key does not exist"

    def test_put_and_delete_item(self):
        self._test_put_item()
        self._test_delete_item()

    def _test_put_item(self):
        old_item = testdb.put(updated_user_2)
        assert old_item is None, "Put should not return any item"

    def _test_delete_item(self):
        old_item = testdb.delete(updated_user_2["user_id"])
        assert old_item == updated_user_2, "Delete should return the item being deleted"

    def test_update_item(self):
        item1 = testdb.update(
            _test_update_item_func,
            updated_user["user_id"],
        )
        assert (
            item1 == updated_user
        ), "Update should return the updated item if not None"

        item2 = testdb.update(
            _test_update_item_func,
            updated_user["user_id"],
        )
        assert item2 is None, "Update should return None if the updated item is None"


def _test_update_item_func(item: MaybeUser) -> MaybeUser:
    if item is None:
        return updated_user
    else:
        return None
