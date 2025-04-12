from cyberham import dashboard_credentials, encryption_keys
from cyberham.apis.types import Credentials, Permissions, AuthenticationRequest
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from fastapi import HTTPException, Depends
import base64


_private_key = serialization.load_pem_private_key(
    encryption_keys["private"].encode("utf-8"),
    password=None,
    backend=default_backend(),
)

public_key = encryption_keys["public"]


def decrypt(s: str) -> str:
    decrypted_message = _private_key.decrypt(  # type: ignore
        base64.b64decode(s),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return decrypted_message.decode("utf-8")  # type: ignore


def authenticate(credentials: Credentials) -> Permissions:
    try:
        username = decrypt(credentials.username)
        password = decrypt(credentials.password)
    except:
        return Permissions.DENIED

    if (
        username == dashboard_credentials["admin_username"]
        and password == dashboard_credentials["admin_password"]
    ):
        return Permissions.ADMIN
    elif (
        username == dashboard_credentials["sponsor_username"]
        and password == dashboard_credentials["sponsor_password"]
    ):
        return Permissions.SPONSOR

    return Permissions.DENIED


def authenticate_only(req: AuthenticationRequest):
    return authenticate(req.credentials)


def req_perm(level: Permissions, perms: Permissions):
    if perms != Permissions.NONE and perms < level:
        raise HTTPException(status_code=403, detail="Insufficient Permissions")


def require_permission(level: Permissions):
    async def dependency(perms: Permissions = Depends(authenticate)):
        req_perm(level, perms)

    return Depends(dependency)


def require_permission_only(level: Permissions):
    async def dependency(perms: Permissions = Depends(authenticate_only)):
        req_perm(level, perms)

    return Depends(dependency)
