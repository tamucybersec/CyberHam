from pytest import MonkeyPatch
from cyberham.database.mockdb import MockDB
from cyberham.tests.database.test_typeddb import TestTypedDB
from cyberham.tests.models import valid_user, valid_user_2


class TestMockDB:
    def setup_method(self):
        self.mp = MonkeyPatch()
        self.testdb = MockDB([valid_user, valid_user_2], ["user_id"])
        self.mp.setattr("cyberham.tests.database.test_typeddb.testdb", self.testdb)
        self.typeddb = TestTypedDB()

    def test_get_item(self):
        self.typeddb.test_get_item()

    def test_get_non_existent_item(self):
        self.typeddb.test_get_non_existent_item()

    def test_update_item_using_pk(self):
        self.typeddb.test_update_item_using_pk()

    def test_update_item_using_original(self):
        self.typeddb.test_update_item_using_original()

    def test_delete_item(self):
        self.typeddb.test_delete_item()

    def test_delete_non_existent_item(self):
        self.typeddb.test_delete_non_existent_item()

    def test_get_all_items(self):
        self.typeddb.test_get_all_items()

    def test_get_count(self):
        self.typeddb.test_get_count()
