from cyberham.database.sqlite import SQLiteDB
from cyberham.database.types import (
    TableName,
    User,
    Event,
    Flagged,
    Attendance,
    Points,
    Item,
)
from typing import (
    cast,
    TypeVar,
    Generic,
    TypeAlias,
    Optional,
    Callable,
    Mapping,
    Any,
    overload,
    Sequence,
)
from copy import deepcopy

T = TypeVar("T", bound=Mapping[str, Any])
Maybe: TypeAlias = Optional[T]
Update: TypeAlias = Callable[[Maybe[T]], Maybe[T]]


# Change pk_values to be strongly typed
class TypedDB(Generic[T]):
    _db: SQLiteDB
    table: TableName
    pk_names: list[str]

    def __init__(
        self,
        db: SQLiteDB,
        table: TableName,
        pk_names: list[str],
    ) -> None:
        self._db = db
        self.table = table
        self.pk_names = pk_names

    def create(self, item: T) -> None:
        """
        Returns None. Item must be new, otherwise the operation will fail.
        """

        self._db.create_row(self.table, item)

    def get(self, pk_values: list[Any]) -> Maybe[T]:
        return self._cast(self._db.get_row(self.table, self.pk_names, pk_values))

    @overload
    def update(
        self,
        update: Update[T],
        *,
        pk_values: list[Any],
    ) -> Maybe[T]: ...

    @overload
    def update(
        self,
        update: Update[T],
        *,
        original: Maybe[T],
    ) -> Maybe[T]: ...

    def update(
        self,
        update: Update[T],
        *,
        pk_values: list[Any] = [],
        original: Maybe[T] = None,
    ) -> Maybe[T]:
        """
        Access an item, change its contents, and the upload the change.
        The accessed item can be None (the item doesn't exist) and you can return None (delete the item).
        Returns the updated item.
        """

        if (not pk_values) == (original is None):
            raise ValueError("Either pk_values or original_item must be provided")
        elif pk_values:
            original = self.get(pk_values)
        elif original is not None:
            pk_values = [original[pk] for pk in self.pk_names]

        updated = update(deepcopy(original))

        if updated is None:
            if original is not None:
                self.delete(pk_values)
            return None
        elif original is None:
            self.create(updated)
            return updated
        else:
            self._db.update_row(self.table, self.pk_names, original, updated)
            return updated

    def delete(self, pk_values: list[Any]) -> Maybe[T]:
        """
        Returns the item that was deleted.
        """

        return self._cast(self._db.delete_row(self.table, self.pk_names, pk_values))

    def get_batch(self, pk_values: list[list[Any]]) -> list[Maybe[T]]:
        return cast(
            list[Maybe[T]], self._db.get_batch(self.table, self.pk_names, pk_values)
        )

    def get_all(self) -> list[T]:
        return cast(list[T], self._db.get_all_rows(self.table))

    def get_count(self) -> int:
        return self._db.get_count(self.table)

    def replace(self, items: Sequence[Item]):
        """
        Resets and replaces the entire database with the given values.
        Use under extreme caution.
        """

        return self._db.replace_table(self.table, items)

    def reset(self):
        self._db.reset_table(self.table)

    def _cast(self, item: Maybe[Item]) -> Maybe[T]:
        return cast(Maybe[T], item)


db = SQLiteDB("cyberham.db")
usersdb = TypedDB[User](db, "users", ["user_id"])
eventsdb = TypedDB[Event](db, "events", ["code"])
flaggeddb = TypedDB[Flagged](db, "flagged", ["user_id"])
attendancedb = TypedDB[Attendance](db, "attendance", ["user_id", "code"])
pointsdb = TypedDB[Points](db, "points", ["user_id", "semester", "year"])
