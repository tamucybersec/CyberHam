"""baseline

Revision ID: 0001
Revises:
Create Date: 2026-10-05 14:30:32.692133
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("date", sa.Text(), nullable=False),
        sa.Column("semester", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "register",
        sa.Column("ticket", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("time", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("ticket"),
    )
    op.create_table(
        "tokens",
        sa.Column("token", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created", sa.Text(), nullable=False),
        sa.Column("expires_after", sa.Text(), nullable=False),
        sa.Column("last_accessed", sa.Text(), nullable=False),
        sa.Column("revoked", sa.Integer(), nullable=False),
        sa.CheckConstraint("revoked IN (0, 1)"),
        sa.Column("permission", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("grad_semester", sa.Text(), nullable=False),
        sa.Column("grad_year", sa.Integer(), nullable=False),
        sa.Column("major", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("verified", sa.Integer(), nullable=False),
        sa.Column(
            "sponsor_email_opt_out",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("join_date", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.CheckConstraint("verified IN (0, 1)"),
        sa.CheckConstraint("sponsor_email_opt_out IN (0, 1)"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "verify",
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("code", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "attendance",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["code"], ["events.code"], onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "code"),
    )
    op.create_table(
        "flagged",
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("offenses", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "points",
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("semester", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "semester", "year"),
    )
    op.create_table(
        "resumes",
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("format", sa.Text(), nullable=False),
        sa.Column("upload_date", sa.Text(), nullable=False),
        sa.Column("is_valid", sa.Integer(), nullable=False),
        sa.CheckConstraint("is_valid IN (0, 1)"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "rsvp",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("reservation", sa.Integer(), nullable=False),
        sa.CheckConstraint("reservation IN (0, 1, 2)"),
        sa.ForeignKeyConstraint(["code"], ["events.code"], onupdate="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "code"),
    )


def downgrade() -> None:
    op.drop_table("rsvp")
    op.drop_table("resumes")
    op.drop_table("points")
    op.drop_table("flagged")
    op.drop_table("attendance")
    op.drop_table("verify")
    op.drop_table("users")
    op.drop_table("tokens")
    op.drop_table("register")
    op.drop_table("events")
