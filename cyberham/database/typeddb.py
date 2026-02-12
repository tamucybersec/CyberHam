from cyberham.database.sqlite import SQLiteDB
from cyberham.database.readonly import ReadonlyDB
from cyberham.types import (
    TableName,
    User,
    Resume,
    Event,
    Flagged,
    Attendance,
    Points,
    Tokens,
    Register,
    Verify,
    Item,
    Semester,
    rsvp
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

PK = TypeVar("PK", bound=tuple[Any, ...])


class TypedDB(Generic[T, PK]):
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

    def get(self, pk_values: PK) -> Maybe[T]:
        return self._cast(self._db.get_row(self.table, self.pk_names, pk_values))

    @overload
    def update(
        self,
        update: Update[T],
        *,
        pk_values: PK,
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
        pk_values: PK | None = None,
        original: Maybe[T] = None,
    ) -> Maybe[T]:
        """
        Access an item, change its contents, and the upload the change.
        The accessed item can be None (the item doesn't exist) and you can return None (delete the item).
        NOTE: Accessing an item using original will NOT reach out the database, instead assuming you have done so very recently.
        Returns the updated item.
        """

        if (pk_values is None) == (original is None):
            raise ValueError("Either pk_values or original_item must be provided")
        elif pk_values is not None:
            original = self.get(pk_values)
        elif original is not None:
            pk_values = cast(PK, tuple(original[pk] for pk in self.pk_names))

        updated = update(deepcopy(original))

        if updated is None:
            if original is not None:
                self.delete(cast(PK, pk_values))
            return None
        elif original is None:
            self.create(updated)
            return updated
        else:
            self._db.update_row(self.table, self.pk_names, original, updated)
            return updated

    def delete(self, pk_values: PK) -> Maybe[T]:
        """
        Returns the item that was deleted.
        """

        return self._cast(self._db.delete_row(self.table, self.pk_names, pk_values))

    def get_batch(self, pk_values: list[PK]) -> list[Maybe[T]]:
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
readonlydb = ReadonlyDB("cyberham.db")
usersdb = TypedDB[User, tuple[str]](db, "users", ["user_id"])
resumesdb = TypedDB[Resume, tuple[str]](db, "resumes", ["user_id"])
eventsdb = TypedDB[Event, tuple[str]](db, "events", ["code"])
flaggeddb = TypedDB[Flagged, tuple[str]](db, "flagged", ["user_id"])
attendancedb = TypedDB[Attendance, tuple[str, str]](
    db, "attendance", ["user_id", "code"]
)
pointsdb = TypedDB[Points, tuple[str, Semester, int]](
    db, "points", ["user_id", "semester", "year"]
)
tokensdb = TypedDB[Tokens, tuple[str]](db, "tokens", ["token"])
registerdb = TypedDB[Register, tuple[str]](db, "register", ["ticket"])
verifydb = TypedDB[Verify, tuple[str]](db, "verify", ["user_id"])
rsvpdb=TypedDB[rsvp, tuple[str, str, int]](
    db, "rsvp", ["user_id", "code", "reservation"]
)
