# Read CONTRIBUTING.md#database-schema-changes to see
# what to do if you need to change this file

from sqlalchemy import (
    CheckConstraint,
    Column,
    Connection,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)

metadata = MetaData()


def create_tables(conn: Connection) -> None:
    metadata.create_all(conn)


users = Table(
    "users",
    metadata,
    Column("user_id", Text, primary_key=True, nullable=True),
    Column("name", Text, nullable=False),
    Column("grad_semester", Text, nullable=False),
    Column("grad_year", Integer, nullable=False),
    Column("major", Text, nullable=False),
    Column("email", Text, nullable=False),
    Column("verified", Integer, CheckConstraint("verified IN (0, 1)"), nullable=False),
    Column(
        "sponsor_email_opt_out",
        Integer,
        CheckConstraint("sponsor_email_opt_out IN (0, 1)"),
        nullable=False,
        server_default=text("0"),
    ),
    Column("join_date", Text, nullable=False),
    Column("notes", Text, nullable=False),
)

resumes = Table(
    "resumes",
    metadata,
    Column(
        "user_id",
        Text,
        ForeignKey("users.user_id", onupdate="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column("filename", Text, nullable=False),
    Column("format", Text, nullable=False),
    Column("upload_date", Text, nullable=False),
    Column("is_valid", Integer, CheckConstraint("is_valid IN (0, 1)"), nullable=False),
)

events = Table(
    "events",
    metadata,
    Column("code", Text, primary_key=True, nullable=True),
    Column("name", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("points", Integer, nullable=False),
    Column("date", Text, nullable=False),
    Column("semester", Text, nullable=False),
    Column("year", Integer, nullable=False),
)

flagged = Table(
    "flagged",
    metadata,
    Column(
        "user_id",
        Text,
        ForeignKey("users.user_id", onupdate="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column("offenses", Integer, nullable=False),
)

attendance = Table(
    "attendance",
    metadata,
    Column(
        "user_id",
        Text,
        ForeignKey("users.user_id", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "code",
        Text,
        ForeignKey("events.code", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

points = Table(
    "points",
    metadata,
    Column(
        "user_id",
        Text,
        ForeignKey("users.user_id", onupdate="CASCADE"),
        primary_key=True,
        nullable=True,
    ),
    Column("points", Integer, nullable=False),
    Column("semester", Text, primary_key=True, nullable=False),
    Column("year", Integer, primary_key=True, nullable=False),
)

tokens = Table(
    "tokens",
    metadata,
    Column("token", Text, primary_key=True, nullable=True),
    Column("name", Text, nullable=False),
    Column("created", Text, nullable=False),
    Column("expires_after", Text, nullable=False),
    Column("last_accessed", Text, nullable=False),
    Column("revoked", Integer, CheckConstraint("revoked IN (0, 1)"), nullable=False),
    Column("permission", Integer, nullable=False),
)

register = Table(
    "register",
    metadata,
    Column("ticket", Text, primary_key=True, nullable=True),
    Column("user_id", Text, nullable=False),
    Column("time", Text, nullable=False),
)

verify = Table(
    "verify",
    metadata,
    Column("user_id", Text, primary_key=True, nullable=True),
    Column("code", Integer),
)

rsvp = Table(
    "rsvp",
    metadata,
    Column(
        "user_id",
        Text,
        ForeignKey("users.user_id", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "code",
        Text,
        ForeignKey("events.code", onupdate="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "reservation",
        Integer,
        CheckConstraint("reservation IN (0, 1, 2)"),
        nullable=False,
    ),
)
