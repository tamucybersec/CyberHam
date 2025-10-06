from typing import TypedDict, cast, Optional, Any, Mapping
from datetime import datetime, timezone
from cyberham import website_url, dashboard_config
from cyberham.apis.auth import token_status
from cyberham.types import Permissions, User, default_user
from cyberham.backend.register import register, upload_resume
from cyberham.utils.transform import pretty_semester, GradSemester
from cyberham.database.typeddb import (
    usersdb,
    eventsdb,
    flaggeddb,
    attendancedb,
    pointsdb,
    tokensdb,
    registerdb,
)
from cyberham.utils.date import valid_registration_time
from cyberham.apis.crud_factory import create_crud_routes
from fastapi import FastAPI, Form, File, HTTPException, UploadFile
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import traceback
import uvicorn
import os

def get_file_mtime_iso_utc(file_path: str) -> str:
    # Get the last modified time of a resume file (which should be when it was uploaded),
    # in UTC ISO 8601 format.
    try:
        timestamp = os.path.getmtime(file_path)
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt_utc.isoformat().replace("+00:00", "Z")
    except FileNotFoundError: # means the resume hasn't been uploaded but this function is being called.
        return ""
    except Exception: # Some other unexpected/unhandled error.
        print(f"Unexpected error getting file mtime for {file_path}:")
        traceback.print_exc()
        return ""


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
    
    user = usersdb.get((registration["user_id"],))
    if user is None:
        # no user in db yet, return default user with just user_id set
        return_user = default_user(registration["user_id"])
    else:
        return_user = dict(user) # copy of it so we don't modify db

    # get resume uploaded time from the file on disk (if any)
    resume_filename = str(return_user.get("resume_filename")) or "" # make sure its a str
    resume_uploaded_at = ""
    if resume_filename != "":
        # user exists and has a resume
        resume_path = os.path.join("resumes", registration["user_id"])
        resume_uploaded_at = get_file_mtime_iso_utc(resume_path)

    return {
        **return_user,
        "grad_semester": pretty_semester(cast(GradSemester, return_user["grad_semester"])),
        "resume_uploaded_at": resume_uploaded_at,
    }

class PostResponse(TypedDict):
        message: str
        user: User
        resume_uploaded_at: str

@app.post("/register/{ticket}")
async def register_user( # type: ignore[return-value]
    ticket: str,
    user_json: str = Form(...),
    resume: Optional[UploadFile] = File(None),
) -> JSONResponse | PostResponse:
    try:
        user_dict = json.loads(user_json)
        user = User(**user_dict)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user JSON")

    resume_filename = ""
    resume_format = ""
    resume_uploaded_at = ""
    if resume is not None:
        resume_filename, resume_format, success = await upload_resume(user["user_id"], resume)
        if not success:
            raise HTTPException(status_code=500, detail="Resume upload failed")

        user["resume_filename"] = resume_filename
        user["resume_format"] = resume_format

        # get upload time for server response
        saved_resume_path = os.path.join("resumes", user["user_id"])
        resume_uploaded_at = get_file_mtime_iso_utc(saved_resume_path)
    
    msg, err = register(ticket, user)
    if err is not None:
        return JSONResponse(err.json(), status_code=400)
    
    # Read user row to return to client
    db_user = usersdb.get((user["user_id"],))
    if db_user is None:
        return_user: User = default_user(user["user_id"])
    else:
        return_user: User =  cast(User, dict(db_user))  # ensure it's a real copy

    #return_user["resume_filename"] = resume_filename # set above if uploaded. but if not ill uncomment this

    # respond with the usual message, the user object, and the resume upload time (if any)
    return PostResponse({
        "message": msg,
        "user": return_user,
        "resume_uploaded_at": resume_uploaded_at,
    })


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
