from cyberham.database.typeddb import usersdb, eventsdb, flaggeddb
from cyberham.database.backup import write_backup, load_latest_backup


class TestBackup:
    def test_backup_all(self):
        users = usersdb.get_all()
        write_backup("users", users)

        events = eventsdb.get_all()
        write_backup("events", events)

        flagged = flaggeddb.get_all()
        write_backup("flagged", flagged)


class TestRecovery:
    def test_recover_all(self):
        assert True, "Only recover the database when necessary"
        return

        users = load_latest_backup("users")
        usersdb.replace(users)

        events = load_latest_backup("events")
        eventsdb.replace(events)

        flagged = load_latest_backup("flagged")
        flaggeddb.replace(flagged)
