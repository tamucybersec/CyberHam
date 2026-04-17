from cyberham.database.typeddb import db


def migrate_users_schema() -> None:
    db.cursor.execute("PRAGMA table_info(users)")
    columns = db.cursor.fetchall()
    column_names = {column["name"] for column in columns}

    if "sponsor_email_opt_out" not in column_names:
        db.conn.execute(
            """
            ALTER TABLE users
            ADD COLUMN sponsor_email_opt_out INTEGER NOT NULL DEFAULT 0 CHECK(sponsor_email_opt_out IN (0, 1))
            """
        )


if __name__ == "__main__":
    migrate_users_schema()
