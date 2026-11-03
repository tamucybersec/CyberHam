"""This file is here to migrate legacy semesters in the current database format.
Currently, there are two files that contain legacy semester data:
1. attendance.db for Fall 2022 - Spring 2023
2. fall_attendance.db for Fall 2023 - (partially) Spring 2024
"""

import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

LEGACY_FILES = {
    "attendance.db": (2022, 2023),
    "fall_attendance.db": (2023, 2024),
}
DATE_FORMAT = "%m/%d/%Y"  # how the current DB stores dates, e.g. 09/01/2022
LEGACY_CATEGORY = "legacy"
SKIP_EVENT_CODES = {"ZPATQ"}  # test event
USER_NOTE = "Imported from legacy 2022-2024 attendance database"


def parse_date(raw: str, fall_year: int, spring_year: int) -> date:
    """'9/14', '09/14/22' or '4-13-2023' -> date."""
    month, day, *year = [int(p) for p in re.split(r"[/-]", raw.strip())]
    if year:
        y = year[0] + 2000 if year[0] < 100 else year[0]
    else:
        y = fall_year if month >= 8 else spring_year
    return date(y, month, day)


def semester_of(d: date) -> str:
    # same rule as cyberham.utils.date.current_semester; the app only knows spring/fall
    return "spring" if d.month <= 6 else "fall"


def load_legacy(legacy_dir: Path):
    """Read users, events, attendance and flagged from the old files."""
    users: dict[str, dict[str, Any]] = {}
    events: dict[str, dict[str, Any]] = {}
    attendance: set[tuple[str, str]] = set()  # (user_id, event code)
    flagged: dict[str, int] = {}

    for fname, (fall_year, spring_year) in LEGACY_FILES.items():
        path = legacy_dir / fname
        if not path.exists():
            raise FileNotFoundError(f"Missing legacy file: {path}")
        old = sqlite3.connect(f"file:{path}?mode=ro", uri=True)

        for uid, name, grad_year, email in old.execute(
            "SELECT user_id, name, grad_year, email FROM users"
        ):
            users[str(uid)] = dict(
                name=name or "", grad_year=grad_year or 0, email=email or ""
            )

        # old events store attendees as a space-separated string of user ids
        for name, code, points, raw_date, attended in old.execute(
            "SELECT name, code, points, date, attended_users FROM events"
        ):
            if code in SKIP_EVENT_CODES:
                continue
            events[code] = dict(
                name=name,
                points=points or 0,
                day=parse_date(raw_date, fall_year, spring_year),
            )
            attendance.update((uid, code) for uid in (attended or "").split())

        for uid, offences in old.execute("SELECT user_id, offences FROM flagged"):
            flagged[str(uid)] = offences
        old.close()

    return users, events, attendance, flagged


def migrate(conn: sqlite3.Connection, legacy_dir: Path, dry_run: bool):
    users, events, attendance, flagged = load_legacy(legacy_dir)

    # Skip legacy events whose code is already used by a different live event
    live_events = dict(conn.execute("SELECT code, name FROM events").fetchall())
    for code in [
        c for c in events if live_events.get(c, events[c]["name"]) != events[c]["name"]
    ]:
        print(
            f"!! Skipping legacy event {code}: code already used by '{live_events[code]}'"
        )
        del events[code]

    # Keep only attendance for kept events and people who have a user record somewhere
    live_users = {r[0] for r in conn.execute("SELECT user_id FROM users")}
    attendance = {
        (u, c) for u, c in attendance if c in events and (u in users or u in live_users)
    }

    # Join date is the first event attended; points are summed per semester
    first_seen: dict[str, date] = {}
    points: dict[tuple[str, str, int], int] = defaultdict(int)
    for uid, code in attendance:
        day = events[code]["day"]
        first_seen[uid] = min(day, first_seen.get(uid, day))
        points[(uid, semester_of(day), day.year)] += events[code]["points"]
    fallback_join: date = min(e["day"] for e in events.values())

    inserts = {
        "users": (
            """INSERT OR IGNORE INTO users (user_id, name, grad_semester, grad_year, major,
                   email, verified, sponsor_email_opt_out, join_date, notes)
               VALUES (?, ?, '', ?, '', ?, 0, 0, ?, ?)""",
            [
                (
                    uid,
                    u["name"],
                    u["grad_year"],
                    u["email"],
                    first_seen.get(uid, fallback_join).strftime(DATE_FORMAT),
                    USER_NOTE,
                )
                for uid, u in users.items()
            ],
        ),
        "events": (
            """INSERT OR IGNORE INTO events (code, name, category, points, date, semester, year)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    code,
                    e["name"],
                    LEGACY_CATEGORY,
                    e["points"],
                    e["day"].strftime(DATE_FORMAT),
                    semester_of(e["day"]),
                    e["day"].year,
                )
                for code, e in events.items()
            ],
        ),
        "attendance": (
            "INSERT OR IGNORE INTO attendance (user_id, code) VALUES (?, ?)",
            list(attendance),
        ),
        "points": (
            "INSERT OR IGNORE INTO points (user_id, semester, year, points) VALUES (?, ?, ?, ?)",
            [(*key, pts) for key, pts in points.items()],
        ),
        "flagged": (
            "INSERT OR IGNORE INTO flagged (user_id, offenses) VALUES (?, ?)",
            list(flagged.items()),
        ),
    }
    # Crash or a dry run saves nothing
    for table, (sql, rows) in inserts.items():
        added = conn.executemany(sql, rows).rowcount
        print(f"  {table:<11} {added:>5} added, {len(rows) - added:>5} already there")

    if dry_run:
        conn.rollback()
        print("DRY RUN -- nothing was saved")
    else:
        conn.commit()
        print("Migration complete")


if __name__ == "__main__":
    from cyberham import data_path
    from cyberham.database.backup import write_full_backup
    from cyberham.database.typeddb import db

    dry_run = "--dry-run" in sys.argv
    if not dry_run:
        write_full_backup()
    migrate(db.conn, Path(data_path) / "legacy", dry_run)
