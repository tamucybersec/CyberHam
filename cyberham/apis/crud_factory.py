from cyberham.database.typeddb import TypedDB, T, Maybe, PK
from fastapi import APIRouter
from cyberham.apis.types import Permissions
from cyberham.apis.auth import require_permission, require_permission_only
from typing import Any, Sequence, cast


def create_crud_routes(
    *,
    prefix: str,
    db: TypedDB[T, PK],
    pk_names: list[str],
    get_perm: Permissions,
    modify_perm: Permissions,
):
    router = APIRouter(prefix=f"/{prefix}")

    # get
    @router.post(f"/get", dependencies=[require_permission_only(get_perm)])
    async def get_all():
        return db.get_all()

    # put
    @router.post(f"/create", dependencies=[require_permission(modify_perm)])
    async def create(item: T):
        db.create(item)
        return {"message": "created"}

    # post
    @router.post(f"/update", dependencies=[require_permission(modify_perm)])
    async def update(original: T, new: T):
        def updater(_: Maybe[T]) -> Maybe[T]:
            return new

        db.update(updater, original=original)
        return {"message": "updated"}

    # delete
    @router.post(f"/delete", dependencies=[require_permission(modify_perm)])
    async def delete(item: T):
        pk_values = [item[pk] for pk in pk_names]
        db.delete(cast(PK, pk_values))
        return {"message": "deleted"}

    @router.post(f"/replace", dependencies=[require_permission(modify_perm)])
    async def replace(replacement: Sequence[T]):
        return db.replace(replacement)

    # satisfy type checker
    _: list[Any] = [get_all, create, update, delete, replace]
    return router
