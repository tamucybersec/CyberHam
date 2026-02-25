from typing import cast, Optional, Any, Mapping
from cyberham import website_url, dashboard_config
from cyberham.apis.auth import token_status
from cyberham.types import Permissions, User, default_user
from cyberham.backend.register import register, upload_resume
from cyberham.utils.transform import pretty_semester
from cyberham.database.typeddb import (
    readonlydb,
    usersdb,
    resumesdb,
    eventsdb,
    flaggeddb,
    attendancedb,
    pointsdb,
    tokensdb,
    registerdb,
)
from cyberham.types import Permissions
from cyberham.apis.auth import require_permission
from cyberham.utils.date import valid_registration_time
from cyberham.apis.crud_factory import create_crud_routes
from fastapi import FastAPI, Form, File, HTTPException, UploadFile, Depends
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import traceback
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[website_url],
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
        headers={"Access-Control-Allow-Origin": website_url},
    )


@app.get("/")
async def health_check() -> str:
    return "healthy"


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
    resume: Optional[UploadFile] = File(None),
):
    try:
        user_dict = json.loads(user_json)
        user = User(**user_dict)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user JSON")

    if resume is not None:
        success = await upload_resume(user["user_id"], resume)
        if not success:
            raise HTTPException(status_code=500, detail="Resume upload failed")
        # override user with uploaded resume info
    
    msg, err = register(ticket, user)
    if err is not None:
        return JSONResponse(err.json(), status_code=400)

    return {"message": msg}


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


routers = [
    create_crud_routes(
        prefix="users",
        db=usersdb,
        pk_names=["user_id"],
        get_perm=Permissions.SPONSOR,
        modify_perm=Permissions.ADMIN,
    ),
    create_crud_routes(
        prefix="resumes",
        db=resumesdb,
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
