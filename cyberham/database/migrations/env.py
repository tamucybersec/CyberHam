from alembic import context
from sqlalchemy import Connection

from cyberham import data_path
from cyberham.database.engine import make_engine
from cyberham.database.tables import metadata


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=metadata, render_as_batch=True
    )
    with context.begin_transaction():
        context.run_migrations()


connection: Connection | None = context.config.attributes.get("connection")
if connection is not None:
    run_migrations(connection)
else:
    engine = make_engine(data_path / "cyberham.db")
    with engine.begin() as conn:
        run_migrations(conn)
