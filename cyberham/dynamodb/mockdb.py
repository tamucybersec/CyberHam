from typing import TypeVar, Generic, TypeAlias, Optional, Callable, Mapping, Any
from copy import deepcopy

T = TypeVar("T", bound=Mapping[str, Any])
Maybe: TypeAlias = Optional[T]
Update: TypeAlias = Callable[[Maybe[T]], Maybe[T]]


class MockDB(Generic[T]):
    contents: dict[str, T]
    partition_key_name: str
    sort_key_name: str | None

    def __init__(
        self,
        initial_contents: list[T],
        partition_key_name: str,
        sort_key_name: str | None,
    ) -> None:
        self.contents = {}
        self.partition_key_name = partition_key_name
        self.sort_key_name = sort_key_name

        for item in initial_contents:
            self.contents[item[partition_key_name]] = deepcopy(item)

    def put(self, item: T) -> Maybe[T]:
        old = None
        if self.sort_key_name:
            old = self.get(item[self.partition_key_name], item[self.sort_key_name])
        else:
            old = self.get(item[self.partition_key_name])

        self.contents[item[self.partition_key_name]] = deepcopy(item)
        return old

    def get(self, partition_key: str | int, sort_key: Optional[str] = None) -> Maybe[T]:
        if partition_key in self.contents:
            return deepcopy(self.contents[partition_key])
        else:
            return None

    def update(
        self,
        update: Update[T],
        partition_key: str | int,
        sort_key: Optional[str] = None,
    ) -> Maybe[T]:
        item = self.get(partition_key, sort_key)
        updated_item = update(item)

        if updated_item is None:
            self.delete(partition_key, sort_key)
            return None
        else:
            self.put(updated_item)
            return updated_item

    def delete(
        self, partition_key: str | int, sort_key: Optional[str] = None
    ) -> Maybe[T]:
        if partition_key in self.contents:
            item = self.contents[partition_key]
            del self.contents[partition_key]
            return item
        else:
            return None

    def get_all(self) -> list[T]:
        return list(self.contents.values())

    def get_count(self) -> int:
        return len(self.get_all())
