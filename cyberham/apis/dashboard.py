import ipaddress
import json
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import uvicorn
from discord.ext import ipcx
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.types import Receive, Scope, Send

from cyberham import dashboard_config, ipc_key, ipc_port, website_url
from cyberham.apis.auth import require_permission, token_status
from cyberham.apis.crud_factory import create_crud_routes
from cyberham.backend.register import register, upload_resume
from cyberham.database.schema import (
    detect_schema_drift,
    live_database_path,
    live_schema,
    snapshot_database,
)
from cyberham.database.table_registry import TABLE_REGISTRY, TABLE_REGISTRY_BY_NAME
from cyberham.database.typeddb import (
    readonlydb,
    registerdb,
    resumesdb,
    usersdb,
)
from cyberham.types import Permissions, User, default_user
from cyberham.utils.date import valid_registration_time
from cyberham.utils.transform import pretty_semester

app = FastAPI()
ipc = ipcx.Client(secret_key=ipc_key, port=ipc_port)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[website_url],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(Exception)
async def catch_exceptions(request: Request, exc: Exception):
    print("Unhandled exception:", exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"details": str(exc), "error": "Internal Server Error"},
        headers={"Access-Control-Allow-Origin": website_url},
    )


@app.get("/")
async def health_check() -> str:
    return "healthy"


def _normalize_ip(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        return str(addr.ipv4_mapped)
    return str(addr)


@app.get("/ip")
async def get_ip(request: Request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        candidates = [_normalize_ip(ip.strip()) for ip in x_forwarded_for.split(",") if ip.strip()]
    else:
        candidates = [request.client.host] if request.client else []
        candidates = [_normalize_ip(ip) for ip in candidates]

    if not candidates:
        return "Unknown"

    for ip in candidates:
        try:
            if isinstance(ipaddress.ip_address(ip), ipaddress.IPv4Address):
                return ip
        except ValueError:
            continue

    return candidates[0]


@app.get("/login")
async def login(token: str) -> Permissions:
    permission, _ = token_status(token)
    return permission


@app.get("/self/{ticket}")
async def get_self(ticket: str) -> Mapping[str, Any]:
    registration = registerdb.get((ticket,))
    if registration is None:
        raise HTTPException(400, "Invalid registration link.")
    elif not valid_registration_time(registration["time"]):
        raise HTTPException(400, "Registration link has expired")    
    user = usersdb.get((registration["user_id"],)) or default_user(registration["user_id"])
    resume = resumesdb.get((registration["user_id"],))
    # get resume data to pass to front end if there's a db row for that resume
    resume_data: Mapping[str, Any] = {}
    if resume is not None:
        resume_data = {
            "filename": resume["filename"],
            "format": resume["format"],
            "upload_date": resume["upload_date"],
            "is_valid": bool(resume["is_valid"])
            }
        
    if "sponsor_email_opt_out" not in user:
        user["sponsor_email_opt_out"] = 0

    return {
        "user": {**dict(user),"grad_semester": pretty_semester(user["grad_semester"])},
        "resume": resume_data,
    }


@app.post("/register/{ticket}")
async def register_user(
    ticket: str,
    user_json: str = Form(...),
    resume: UploadFile | None = File(None),
):
    try:
        user_dict = json.loads(user_json)
        user = User(**user_dict)
    except Exception as err:
        raise HTTPException(status_code=400, detail="Invalid user JSON") from err

    msg, err = register(ticket, user)
    if err is not None:
        return JSONResponse(err.json(), status_code=400)

    if resume is not None:
        success = await upload_resume(user["user_id"], resume)
        if not success:
            raise HTTPException(status_code=500, detail="Resume upload failed")

    return {"message": msg}

@app.get('/user/{user_id}')
async def username(user_id: int):
    try:
        user = await ipc.request("fetch_username",user_id=user_id) # type: ignore
        return user
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"details": str(exc), "error": "Internal Server Error"},
            headers={"Access-Control-Allow-Origin": website_url},
        )

class QueryPayload(BaseModel):
    sql: str


@app.post(
    "/query/readonly",
    dependencies=[Depends(require_permission(Permissions.SUPER_ADMIN))],
)
async def query_readonly(body: QueryPayload):
    try:
        return readonlydb.execute(body.sql)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get(
    "/schema",
    dependencies=[Depends(require_permission(Permissions.SUPER_ADMIN))],
)
def get_schema() -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    live = live_schema()
    drift = detect_schema_drift(live=live)

    for name, table in live.items():
        entry = TABLE_REGISTRY_BY_NAME.get(name)
        tables.append(
            {
                "name": name,
                "purpose": (
                    entry.purpose if entry else "This table has not been documented yet."
                ),
                "dashboard_path": entry.dashboard_path if entry else None,
                "view_permission": entry.get_permission if entry else None,
                "modify_permission": entry.modify_permission if entry else None,
                "primary_key": table.primary_key,
                "columns": [
                    {
                        "name": column.name,
                        "type": column.type,
                        "not_null": column.not_null,
                        "default_value": column.default_value,
                        "is_primary_key": column.primary_key_index > 0,
                    }
                    for column in table.columns
                ],
                "foreign_keys": [
                    {
                        "column": foreign_key.column,
                        "references_table": foreign_key.references_table,
                        "references_column": foreign_key.references_column,
                        "on_update": foreign_key.on_update,
                        "on_delete": foreign_key.on_delete,
                    }
                    for foreign_key in table.foreign_keys
                ],
            }
        )

    return {
        "tables": tables,
        "drift": [
            {
                "table": item.table,
                "missing_columns": item.missing_columns,
                "extra_columns": item.extra_columns,
                "changed_columns": item.changed_columns,
                "relationships_changed": item.relationships_changed,
            }
            for item in drift
        ],
    }


class DatabaseExportResponse(FileResponse):
    """Remove the temporary snapshot on success, errors, and cancellation."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            Path(self.path).unlink(missing_ok=True)


@app.get(
    "/database/export",
    dependencies=[Depends(require_permission(Permissions.SUPER_ADMIN))],
)
def export_database():
    database_path = live_database_path()
    if not database_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found.")

    snapshot_path = snapshot_database(database_path)
    return DatabaseExportResponse(
        path=snapshot_path,
        media_type="application/x-sqlite3",
        filename=database_path.name,
        headers={"Cache-Control": "no-store"},
    )


routers = [
    create_crud_routes(
        prefix=entry.name,
        db=entry.db,
        pk_names=entry.db.pk_names,
        get_perm=entry.get_permission,
        modify_perm=entry.modify_permission,
    )
    for entry in TABLE_REGISTRY
    if entry.get_permission is not None and entry.modify_permission is not None
]


for router in routers:
    app.include_router(router)


def run_api():
    uvicorn.run(
        app,
        host=cast(str, dashboard_config["host"]),
        port=int(dashboard_config["port"]),
    )
