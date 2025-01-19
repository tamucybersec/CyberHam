from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import MaybeItem
from cyberham.tests.models import (
    table,
    partition_key,
    sort_key,
    existing_item,
    non_existent_item,
    new_item,
    update_item,
)


class TestDynamoCrud:
    dynamo: DynamoDB

    @classmethod
    def setup_class(cls):
        cls.dynamo = DynamoDB()

    def test_get_item(self):
        key = self.dynamo.create_key(
            partition_key,
            existing_item[partition_key],
            sort_key,
            existing_item[sort_key],
        )
        item = self.dynamo.get_item(table, key)
        assert item and existing_item == item

    def test_get_non_existent_item(self):
        key = self.dynamo.create_key(
            partition_key,
            non_existent_item[partition_key],
            sort_key,
            non_existent_item[sort_key],
        )
        item = self.dynamo.get_item(table, key)
        assert item is None

    def test_put_and_delete_item(self):
        self._test_put_item()
        self._test_delete_item()

    def _test_put_item(self):
        old_item = self.dynamo.put_item(table, new_item)
        assert old_item is None

    def _test_delete_item(self):
        key = self.dynamo.create_key(
            partition_key,
            new_item[partition_key],
            sort_key,
            new_item[sort_key],
        )
        old_item = self.dynamo.delete_item(table, key)
        assert old_item == new_item

    def test_update_item(self):
        key = self.dynamo.create_key(
            partition_key,
            update_item[partition_key],
            sort_key,
            update_item[sort_key],
        )

        item1 = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item1 == update_item

        item2 = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item2 is None


def _test_update_item_func(item: MaybeItem) -> MaybeItem:
    if item is None:
        return update_item
    else:
        return None
