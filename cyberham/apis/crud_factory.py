from cyberham.database.typeddb import TypedDB
from fastapi import APIRouter
from cyberham.apis.types import Permissions
from cyberham.apis.auth import require_permission, require_permission_only
from typing import TypeVar, Any, Mapping, TypeAlias, Optional, Sequence

T = TypeVar("T", bound=Mapping[str, Any])
Maybe: TypeAlias = Optional[T]


def create_crud_routes(
    *,
    prefix: str,
    db: TypedDB[T],
    pk_names: list[str],
    get_perm: Permissions,
    modify_perm: Permissions,
):
    router = APIRouter(prefix=f"/{prefix}")

    # get
    @router.post(f"{prefix}/get", dependencies=[require_permission_only(get_perm)])
    async def get_all():
        return db.get_all()

    # put
    @router.post(f"{prefix}/create", dependencies=[require_permission(modify_perm)])
    async def create(item: T):
        db.create(item)
        return {"message": "created"}

    # post
    @router.post(f"{prefix}/update", dependencies=[require_permission(modify_perm)])
    async def update(original: T, new: T):
        def updater(_: Maybe[T]) -> Maybe[T]:
            return new

        db.update(updater, original=original)
        return {"message": "updated"}

    # delete
    @router.post(f"{prefix}/delete", dependencies=[require_permission(modify_perm)])
    async def delete(item: T):
        pk_values = [item[pk] for pk in pk_names]
        db.delete(pk_values)
        return {"message": "deleted"}

    @router.post(f"{prefix}/replace", dependencies=[require_permission(modify_perm)])
    async def replace(replacement: Sequence[T]):
        return db.replace(replacement)

    # satisfy type checker
    _: list[Any] = [get_all, create, update, delete, replace]
    return router
