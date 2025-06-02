from typing import TypeVar, Generic, TypeAlias, Optional, Callable, Mapping, Any
from copy import deepcopy

T = TypeVar("T", bound=Mapping[str, Any])
Maybe: TypeAlias = Optional[T]
Update: TypeAlias = Callable[[Maybe[T]], Maybe[T]]


class MockDB(Generic[T]):
    contents: dict[str, T]
    pk_names: list[str]

    def __init__(
        self,
        initial_contents: list[T],
        pk_names: list[str],
    ) -> None:
        self.contents = {}
        self.pk_names = pk_names

        for item in initial_contents:
            self.contents[self._key(item)] = deepcopy(item)

    def create(self, item: T) -> None:
        if self._key(item) in self.contents:
            raise Exception("Entry already exists")

        self.contents[self._key(item)] = deepcopy(item)

    def get(self, pk_values: list[Any]) -> Maybe[T]:
        key = self._key_vals(pk_values)
        if key in self.contents:
            return deepcopy(self.contents[key])
        else:
            return None

    def update(
        self, update: Update[T], *, pk_values: list[Any] = [], original: Maybe[T] = None
    ) -> Maybe[T]:
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
            del self.contents[self._key(original)]
            self.contents[self._key(updated)] = deepcopy(updated)
            return deepcopy(updated)

    def delete(self, pk_values: list[Any]) -> Maybe[T]:
        key = self._key_vals(pk_values)
        if key in self.contents:
            item = self.contents[key]
            del self.contents[key]
            return item
        else:
            return None

    def get_all(self) -> list[T]:
        return list(self.contents.values())

    def get_count(self) -> int:
        return len(self.get_all())

    def reset(self):
        self.contents = {}

    def _key(self, item: T):
        return self._key_vals([item[pk] for pk in self.pk_names])

    def _key_vals(self, pk_values: list[Any]) -> str:
        return f"({", ".join([str(v) for v in pk_values])})"
