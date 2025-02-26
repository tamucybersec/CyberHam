from copy import deepcopy
from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import MaybeItem, TableName, Key
from cyberham.tests.models import (
    valid_user_item,
    valid_user_2_item,
    updated_user_item,
    updated_user_2_item,
    unregistered_user_item,
)

table: TableName = "tests"
pk = "user_id"


class TestDynamoCrud:
    dynamo: DynamoDB

    @classmethod
    def setup_class(cls):
        cls.dynamo = DynamoDB()

    def test_get_item(self):
        key = self._create_key(valid_user_item)
        item = self.dynamo.get_item(table, key)
        assert item and valid_user_item == item

    def test_get_non_existent_item(self):
        key = self._create_key(unregistered_user_item)
        item = self.dynamo.get_item(table, key)
        assert item is None

    def test_get_all(self):
        items = self.dynamo.get_all(table)
        got = sorted(items, key=lambda item: item["user_id"])
        expected = sorted(
            [
                valid_user_item,
                valid_user_2_item,
            ],
            key=lambda item: str(item["user_id"]),
        )
        assert got == expected

    def test_get_count(self):
        assert self.dynamo.get_count(table) == 2

    def test_put_and_delete_item(self):
        self._test_delete_non_existent_item()
        self._test_put_item()
        self._test_put_overwrite_item()
        self._test_delete_item()

    def _test_delete_non_existent_item(self):
        key = self._create_key(updated_user_2_item)
        old_item = self.dynamo.delete_item(table, key)
        assert old_item is None

    def _test_put_item(self):
        old_item = self.dynamo.put_item(table, updated_user_2_item)
        assert old_item is None

    def _test_put_overwrite_item(self):
        mutated_item = deepcopy(updated_user_2_item)
        mutated_item["name"] = "mutated"

        old_item = self.dynamo.put_item(table, mutated_item)
        assert old_item == updated_user_2_item

        old_item = self.dynamo.put_item(table, updated_user_2_item)
        assert old_item == mutated_item

    def _test_delete_item(self):
        key = self._create_key(updated_user_2_item)
        old_item = self.dynamo.delete_item(table, key)
        assert old_item == updated_user_2_item

    def test_update_item(self):
        key = self._create_key(updated_user_item)

        item = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item == updated_user_item

        item = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item is None

    def _create_key(self, model: dict[str, object]) -> Key:
        return self.dynamo.create_key(pk, int(str(model[pk])))


def _test_update_item_func(item: MaybeItem) -> MaybeItem:
    if item is None:
        return updated_user_item
    else:
        return None
