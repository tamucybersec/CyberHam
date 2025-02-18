from pytest import MonkeyPatch
from cyberham.dynamodb.mockdb import MockDB
from cyberham.tests.dynamodb.test_typeddb import TestTypedDB as TypedDB
from cyberham.tests.models import valid_user, valid_user_2


class TestMockDB:
    def setup_method(self):
        self.mp = MonkeyPatch()
        self.testdb = MockDB([valid_user, valid_user_2], "user_id", None)
        self.mp.setattr("cyberham.tests.dynamodb.test_typeddb.testdb", self.testdb)
        self.typeddb = TypedDB()

    def test_get_item(self):
        self.typeddb.test_get_item()

    def test_get_all_items(self):
        self.typeddb.test_get_all_items()

    def test_get_non_existent_item(self):
        self.typeddb.test_get_non_existent_item()

    def test_put_and_delete_item(self):
        self.typeddb.test_put_and_delete_item()

    def test_update_item(self):
        self.typeddb.test_update_item()
