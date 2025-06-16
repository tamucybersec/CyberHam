from typing import cast
from cyberham import cross_origin, dashboard_config
from cyberham.apis.auth import token_status
from cyberham.types import Permissions
from cyberham.database.typeddb import (
    usersdb,
    eventsdb,
    flaggeddb,
    attendancedb,
    pointsdb,
    tokensdb,
)
from cyberham.apis.crud_factory import create_crud_routes
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback
import uvicorn

app = FastAPI(root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[cross_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.exception_handler(Exception)
async def catch_exceptions(request: Request, exc: Exception):
    print("Unhandled exception:", exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"details": str(exc), "error": "Internal Server Error"},
        headers={"Access-Control-Allow-Origin": "http://localhost:4321"},
    )


@app.get("/")
async def health_check() -> str:
    return "healthy"


@app.get("/login")
async def login(token: str) -> Permissions:
    permission, _ = token_status(token)
    return permission


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
        get_perm=Permissions.COMMITTEE,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="attendance",
        db=attendancedb,
        pk_names=["user_id", "code"],
        get_perm=Permissions.SPONSOR,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="points",
        db=pointsdb,
        pk_names=["user_id", "semester", "year"],
        get_perm=Permissions.SPONSOR,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="tokens",
        db=tokensdb,
        pk_names=["token"],
        get_perm=Permissions.SUPER_ADMIN,
        modify_perm=Permissions.SUPER_ADMIN,
    ),
]


for router in routers:
    app.include_router(router)


def run_api():
    uvicorn.run(
        app,
        host=cast(str, dashboard_config["host"]),
        port=int(dashboard_config["port"]),
    )
