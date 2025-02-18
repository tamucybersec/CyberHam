import os
import json
from typing import Sequence
from cyberham.dynamodb.types import TableName, Item
from cyberham.dynamodb.typeddb import usersdb, eventsdb, flaggeddb

path = "backups"


class TestBackup:
    def test_backup_all(self):
        assert True, "Only backup the database when necessary."
        return

        users = usersdb.get_all()
        self._write_backup("users", users)

        events = eventsdb.get_all()
        self._write_backup("events", events)

        flagged = flaggeddb.get_all()
        self._write_backup("flagged", flagged)

    def _write_backup(self, table: TableName, data: Item | Sequence[Item]):
        if not os.path.exists(path):
            os.mkdir(path)

        with open(f"{path}/{table}.json", "w") as file:
            file.write(json.dumps(data))
