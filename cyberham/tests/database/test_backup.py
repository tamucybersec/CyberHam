from cyberham.database.typeddb import (
    db,
    usersdb,
    eventsdb,
    flaggeddb,
    attendancedb,
    pointsdb,
    tokensdb,
)
from cyberham.database.backup import write_backup, load_latest_backup

# these tests are useful when updating the schema:
# just backup the current data to json
# drop the current table so it gets remade
# then reupload it, making any changes to the data when necessary


class TestBackup:
    def test_backup_all(self):
        assert True, "only backup when needed"
        return

        write_backup("users", usersdb.get_all())
        write_backup("events", eventsdb.get_all())
        write_backup("flagged", flaggeddb.get_all())
        write_backup("attendance", attendancedb.get_all())
        write_backup("points", pointsdb.get_all())
        write_backup("tokens", tokensdb.get_all())


class TestRecovery:
    def test_recover_all(self):
        assert True, "Only recover the database when necessary"
        return

        db.conn.execute("PRAGMA foreign_keys = OFF")
        db.conn.commit()

        users = load_latest_backup("users")
        usersdb.replace(users)

        events = load_latest_backup("events")
        eventsdb.replace(events)

        flagged = load_latest_backup("flagged")
        flaggeddb.replace(flagged)

        attendance = load_latest_backup("attendance")
        attendancedb.replace(attendance)

        points = load_latest_backup("points")
        pointsdb.replace(points)

        tokens = load_latest_backup("tokens")
        tokensdb.replace(tokens)

        db.conn.execute("PRAGMA foreign_keys = ON")
        db.conn.commit()

        assert False
