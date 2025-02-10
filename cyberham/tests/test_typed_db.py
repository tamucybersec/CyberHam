from cyberham.dynamodb.types import TestItem
from cyberham.tests.dynamo_models import (
    existing_test_item,
    non_existent_test_item,
    new_test_item,
    update_test_item,
)
from cyberham.dynamodb.typeddb import testdb


class TestDynamoCrud:
    def test_get_item(self):
        item = testdb.get(existing_test_item["partition"], existing_test_item["sort"])
        assert item and existing_test_item == item

    def test_get_non_existent_item(self):
        item = testdb.get(
            non_existent_test_item["partition"], non_existent_test_item["sort"]
        )
        assert item is None

    def test_put_and_delete_item(self):
        self._test_put_item()
        self._test_delete_item()

    def _test_put_item(self):
        old_item = testdb.put(new_test_item)
        assert old_item is None

    def _test_delete_item(self):
        old_item = testdb.delete(new_test_item["partition"], new_test_item["sort"])
        assert old_item == new_test_item

    def test_update_item(self):
        item1 = testdb.update(
            _test_update_item_func,
            update_test_item["partition"],
            update_test_item["sort"],
        )
        assert item1 == update_test_item

        item2 = testdb.update(
            _test_update_item_func,
            update_test_item["partition"],
            update_test_item["sort"],
        )
        assert item2 is None


def _test_update_item_func(item: TestItem | None) -> TestItem | None:
    if item is None:
        return update_test_item
    else:
        return None
