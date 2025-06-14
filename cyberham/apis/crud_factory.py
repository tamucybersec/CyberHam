from cyberham.database.typeddb import TypedDB, T, PK
from fastapi import APIRouter, Depends
from cyberham.database.types import Permissions
from cyberham.apis.auth import require_permission
from typing import Any, Sequence, cast
from pydantic import BaseModel
from fastapi.responses import JSONResponse


class CreateDeletePayload[T](BaseModel):
    item: T


class UpdatePayload[T](BaseModel):
    original: T
    updated: T


class ReplacePayload[T](BaseModel):
    replacement: Sequence[T]


def create_crud_routes(
    *,
    prefix: str,
    db: TypedDB[T, PK],
    pk_names: list[str],
    get_perm: Permissions,
    modify_perm: Permissions,
):
    router = APIRouter(prefix=f"/{prefix}")

    @router.get("", dependencies=[Depends(require_permission(get_perm))])
    async def get_all():
        return db.get_all()

    @router.post("/create", dependencies=[Depends(require_permission(modify_perm))])
    async def create(body: CreateDeletePayload[T]):
        db.create(body.item)
        return {"message": "created"}

    @router.post("/update", dependencies=[Depends(require_permission(modify_perm))])
    async def update(body: UpdatePayload[T]):
        db.update(lambda _: body.updated, original=body.original)
        return {"message": "updated"}

    @router.post("/delete", dependencies=[Depends(require_permission(modify_perm))])
    async def delete(body: CreateDeletePayload[T]):
        pk_values: PK = cast(PK, tuple(body.item[pk] for pk in pk_names))
        db.delete(pk_values)
        return {"message": "deleted"}

    @router.post(f"/replace", dependencies=[Depends(require_permission(modify_perm))])
    async def replace(body: ReplacePayload[T]):
        res = db.replace(body.replacement)
        if "error" in res:
            return JSONResponse(
                status_code=500,
                content={"details": res["details"], "error": res["error"]},
            )
        return {"message": "replaced"}

    # satisfy type checker
    _: list[Any] = [get_all, create, update, delete, replace]
    return router
