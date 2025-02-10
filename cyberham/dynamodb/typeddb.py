from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import (
    TableName,
    TestItem,
    User,
    Event,
    Key,
)
from typing import cast, TypeVar, Generic, TypeAlias, Optional, Callable, Mapping, Any

T = TypeVar("T", bound=Mapping[str, Any])
Maybe: TypeAlias = Optional[T]
Update: TypeAlias = Callable[[Maybe[T]], Maybe[T]]


class _TypedDB(Generic[T]):
    db: DynamoDB
    table: TableName
    partition_key_name: str
    sort_key_name: str | None

    def __init__(
        self,
        db: DynamoDB,
        table: TableName,
        partition_key_name: str,
        sort_key_name: str | None,
    ) -> None:
        self.db = db
        self.table = table
        self.partition_key_name = partition_key_name
        self.sort_key_name = sort_key_name

    def put(self, item: T) -> None:
        self.db.put_item(self.table, item)

    def get(self, partition_key: str, sort_key: Optional[str] = None) -> Maybe[T]:
        key = self._get_key(partition_key, sort_key)
        return cast(Maybe[T], self.db.get_item(self.table, key))

    def update(
        self, update: Update[T], partition_key: str, sort_key: Optional[str] = None
    ) -> Maybe[T]:
        """
        Access an user, change its contents, and the upload the change.
        The accessed user can be None (the user doesn't exist) and you can return None (delete the user).
        Returns the updated user.
        """

        item = self.get(partition_key, sort_key)
        updated_item = update(item)

        if updated_item is None:
            self.delete(partition_key, sort_key)
            return None
        else:
            self.put(updated_item)
            return updated_item

    def delete(self, partition_key: str, sort_key: Optional[str] = None) -> Maybe[T]:
        """
        Returns the user that was deleted.
        """

        key = self._get_key(partition_key, sort_key)
        return cast(Maybe[T], self.db.delete_item(self.table, key))

    def get_all(self) -> list[T]:
        return cast(list[T], self.db.get_all(self.table))
    
    def get_count(self) -> int:
        return self.db.get_count(self.table)

    def _get_key(self, partition_key: str, sort_key: Optional[str]) -> Key:
        if self.sort_key_name is None:
            if sort_key is not None:
                raise Exception(f"A sort key is not needed for the {self.table} table.")
            return self.db.create_key(self.partition_key_name, partition_key)
        else:
            if sort_key is None:
                raise Exception(f"A sort key is needed for the {self.table} table.")
            return self.db.create_key(
                self.partition_key_name, partition_key, self.sort_key_name, sort_key
            )


_db = DynamoDB()
testdb = _TypedDB[TestItem](_db, "tests", "partition", "sort")
usersdb = _TypedDB[User](_db, "users", "user_id", None)
eventsdb = _TypedDB[Event](_db, "events", "code", None)
