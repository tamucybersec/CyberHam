from cyberham import dashboard_credentials
from cyberham.apis.crypto import authenticate, public_key
from cyberham.apis.types import Permissions
from fastapi import FastAPI, Depends
import uvicorn


app = FastAPI()


@app.get("/key/")
async def get_public_key():
    return {"key": public_key}


@app.post("/login/")
async def login(perms: Permissions = Depends(authenticate)):
    return {"perms": perms}


def run_api():
    uvicorn.run(
        app, host=dashboard_credentials["host"], port=int(dashboard_credentials["port"])
    )
