from typing import cast, Annotated
from cyberham.apis.auth import (
    public_key,
    authenticate_only,
    decrypt,
)
from cyberham import dashboard_credentials
from cyberham.apis.types import Permissions, ValidateBody
from cyberham.database.typeddb import usersdb, eventsdb, flaggeddb
from cyberham.apis.crud_factory import create_crud_routes
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

PermsOnly = Annotated[Permissions, Depends(authenticate_only)]

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"], # astro default port
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return "healthy"


@app.get("/key")
async def get_public_key():
    return {"key": public_key}


@app.post("/login")
async def login(perms: PermsOnly):
    return {"perms": perms}


@app.post("/validate")
async def validate(validation: ValidateBody):
    return decrypt(validation.password) == decrypt(validation.credentials.password)


routers = [
    create_crud_routes(
        prefix="users",
        db=usersdb,
        pk_names=["user_id"],
        get_perm=Permissions.SPONSOR,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="events",
        db=eventsdb,
        pk_names=["code"],
        get_perm=Permissions.SPONSOR,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="flagged",
        db=flaggeddb,
        pk_names=["user_id"],
        get_perm=Permissions.ADMIN,
        modify_perm=Permissions.ADMIN,
    ),
]


for router in routers:
    app.include_router(router)


def run_api():
    uvicorn.run(
        app,
        host=cast(str, dashboard_credentials["host"]),
        port=int(dashboard_credentials["port"]),
    )
