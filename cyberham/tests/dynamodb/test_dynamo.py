from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import MaybeItem, TableName
from cyberham.tests.models import (
    valid_user_item,
    updated_user_item,
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
        key = self.dynamo.create_key(pk, str(valid_user_item[pk]))
        item = self.dynamo.get_item(table, key)
        assert item and valid_user_item == item

    def test_get_non_existent_item(self):
        key = self.dynamo.create_key(pk, str(unregistered_user_item[pk]))
        item = self.dynamo.get_item(table, key)
        assert item is None

    def test_put_and_delete_item(self):
        self._test_put_item()
        self._test_delete_item()

    def _test_put_item(self):
        old_item = self.dynamo.put_item(table, updated_user_item)
        assert old_item is None

    def _test_delete_item(self):
        key = self.dynamo.create_key(pk, str(updated_user_item[pk]))
        old_item = self.dynamo.delete_item(table, key)
        assert old_item == updated_user_item

    def test_update_item(self):
        key = self.dynamo.create_key(pk, str(updated_user_item[pk]))

        item1 = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item1 == updated_user_item

        item2 = self.dynamo.update_item(table, key, _test_update_item_func)
        assert item2 is None


def _test_update_item_func(item: MaybeItem) -> MaybeItem:
    if item is None:
        return updated_user_item
    else:
        return None
