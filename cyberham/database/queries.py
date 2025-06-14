# keep all special raw SQL queries in this file for safety
# this way if the schema changes, we know where to look for fixes

from collections import defaultdict
from cyberham.database.typeddb import db
from cyberham.database.types import Semester
from cyberham.utils.date import current_semester, current_year


def attendance_for_user(
    user_id: str,
    semester: Semester = current_semester(),
    year: int = current_year(),
) -> int:
    db.cursor.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        JOIN events ON attendance.code = events.code
        WHERE attendance.user_id = ?
            AND events.semester = ?
            AND events.year = ?
    """,
        (user_id, semester, year),
    )
    return db.cursor.fetchone()[0]


def attendance_for_all_users(
    semester: Semester = current_semester(),
    year: int = current_year(),
) -> dict[str, int]:
    db.cursor.execute(
        """
        SELECT attendance.user_id, COUNT(*) AS attendance
        FROM attendance
        JOIN events ON attendance.code = events.code
        WHERE events.semester = ?
            AND events.year = ?
        GROUP BY attendance.user_id
        """,
        (semester, year),
    )

    return {row["user_id"]: row["attendance"] for row in db.cursor.fetchall()}


def points_for_user(
    user_id: str,
    semester: Semester = current_semester(),
    year: int = current_year(),
) -> int:
    points: int = 0
    db.cursor.execute(
        """
        SELECT points
        FROM points
        WHERE user_id = ?
            AND semester = ?
            AND year = ?
    """,
        (user_id, semester, year),
    )
    row = db.cursor.fetchone()
    if row:
        points += row[0]

    db.cursor.execute(
        """
        SELECT SUM(events.points) AS points
        FROM attendance
        JOIN events ON attendance.code = events.code
        WHERE attendance.user_id = ? 
            AND events.semester = ?
            AND events.year = ?
        GROUP BY attendance.user_id
    """,
        (user_id, semester, year),
    )
    row = db.cursor.fetchone()
    if row:
        points += row[0]

    return points


def points_for_all_users(
    semester: Semester = current_semester(),
    year: int = current_year(),
) -> dict[str, int]:
    points: dict[str, int] = defaultdict(int)

    db.cursor.execute(
        """
        SELECT user_id, points
        FROM points
        WHERE semester = ?
            AND year = ?
    """,
        (semester, year),
    )
    for row in db.cursor.fetchall():
        points[row["user_id"]] = row["points"]

    db.cursor.execute(
        """
        SELECT attendance.user_id, SUM(events.points) AS points
        FROM attendance
        JOIN events ON attendance.code = events.code
        WHERE events.semester = ?
            AND events.year = ?
        GROUP BY attendance.user_id
    """,
        (semester, year),
    )
    for row in db.cursor.fetchall():
        points[row["user_id"]] += row["points"]

    return points


def user_attendance_counts_for_events(codes: list[str]) -> dict[str, int]:
    placeholders = ", ".join("?" for _ in codes)
    db.cursor.execute(
        f"""
        SELECT user_id, COUNT(*) as count
        FROM attendance
        WHERE code IN ({placeholders})
        GROUP BY user_id
        """,
        codes,
    )

    rows = db.cursor.fetchall()
    return {row["user_id"]: row["count"] for row in rows}
