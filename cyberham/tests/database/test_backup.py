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


class TestBackup:
    def test_backup_all(self):
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
        for flag in flagged:
            flag["user_id"] = str(flag["user_id"])
        flaggeddb.replace(flagged)

        attendance = load_latest_backup("attendance")
        for att in attendance:
            att["user_id"] = str(att["user_id"])
        attendancedb.replace(attendance)

        points = load_latest_backup("points")
        for point in points:
            point["user_id"] = str(point["user_id"])
        pointsdb.replace(points)

        tokens = load_latest_backup("tokens")
        tokensdb.replace(tokens)

        db.conn.execute("PRAGMA foreign_keys = ON")
        db.conn.commit()

        assert False

