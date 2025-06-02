from cyberham import dashboard_credentials
from cyberham.apis.auth import (
    public_key,
    authenticate,
    authenticate_only,
    require_permission,
    require_permission_only,
    decrypt,
)
from cyberham.apis.types import Permissions, ValidateBody
from cyberham.database.typeddb import usersdb, eventsdb, flaggeddb
from cyberham.database.types import (
    User,
    MaybeUser,
    Event,
    MaybeEvent,
    Flagged,
    MaybeFlagged,
)
from fastapi import FastAPI, Depends, HTTPException
from typing import Annotated
import uvicorn


app = FastAPI()

Perms = Annotated[Permissions, Depends(authenticate)]
PermsOnly = Annotated[Permissions, Depends(authenticate_only)]


@app.get("/key/")
async def get_public_key():
    return {"key": public_key}


@app.post("/login/")
async def login(perms: PermsOnly):
    return {"perms": perms}


@app.post("/validate/")
async def validate(validation: ValidateBody):
    return decrypt(validation.password) == decrypt(validation.credentials.password)


# region users
@app.post(
    "/users/get",
    dependencies=[require_permission_only(Permissions.SPONSOR)],
)
async def getUsers():
    return usersdb.get_all()


@app.post(
    "/users/create",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def createUser(
    user: User,
):
    usersdb.create(user)
    return {"message": "created"}


@app.post(
    "/users/update",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def updateUser(
    original: User,
    new: User,
):
    def update_user(_: MaybeUser) -> MaybeUser:
        return new

    usersdb.update(update_user, original=original)
    return {"message": "updated"}


@app.post(
    "/users/delete",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def deleteUser(
    user: User,
):
    usersdb.delete([user["user_id"]])
    return {"message": "deleted"}


@app.post("/users/replace", dependencies=[require_permission(Permissions.ADMIN)])
async def replaceUsers(replacement: list[User]):
    raise HTTPException(status_code=501, detail="Feature not yet implemented")


# endregion


# region events
@app.post(
    "/events/get",
    dependencies=[require_permission_only(Permissions.SPONSOR)],
)
async def getEvents():
    return eventsdb.get_all()


@app.post(
    "/events/create",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def createEvent(
    event: Event,
):
    eventsdb.create(event)
    return {"message": "created"}


@app.post(
    "/events/update",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def updateEvent(
    original: Event,
    new: Event,
):
    def update_event(_: MaybeEvent) -> MaybeEvent:
        return new

    eventsdb.update(update_event, original=original)
    return {"message": "updated"}


@app.post(
    "/events/delete",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def deleteEvent(
    event: Event,
):
    eventsdb.delete([event["code"]])
    return {"message": "deleted"}


@app.post("/events/replace", dependencies=[require_permission(Permissions.ADMIN)])
async def replaceEvents(replacement: list[Event]):
    raise HTTPException(status_code=501, detail="Feature not yet implemented")


# endregion


# region flagged
@app.post(
    "/flagged/get",
    dependencies=[require_permission_only(Permissions.ADMIN)],
)
async def getFlagged():
    return flaggeddb.get_all()


@app.post(
    "/flagged/create",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def createFlagged(
    flagged: Flagged,
):
    flaggeddb.create(flagged)
    return {"message": "created"}


@app.post(
    "/flagged/update",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def updateFlagged(
    original: Flagged,
    new: Flagged,
):
    def update_flagged(_: MaybeFlagged) -> MaybeFlagged:
        return new

    flaggeddb.update(update_flagged, original=original)
    return {"message": "updated"}


@app.post(
    "/flagged/delete",
    dependencies=[require_permission(Permissions.ADMIN)],
)
async def deleteFlagged(
    flagged: Flagged,
):
    flaggeddb.delete([flagged["user_id"]])
    return {"message": "deleted"}


@app.post("/flagged/replace", dependencies=[require_permission(Permissions.ADMIN)])
async def replaceFlagged(replacement: list[Flagged]):
    raise HTTPException(status_code=501, detail="Feature not yet implemented")


# endregion


def run_api():
    uvicorn.run(
        app, host=dashboard_credentials["host"], port=int(dashboard_credentials["port"])
    )
