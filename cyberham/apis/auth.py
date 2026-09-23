from datetime import datetime

from fastapi import Depends, HTTPException
from fastapi.requests import Request  # getting IP address
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cyberham.database.typeddb import tokensdb
from cyberham.types import MaybeTokens, Permissions
from cyberham.utils.audit import log_access
from cyberham.utils.date import compare_datestrs, datetime_to_datestr

security = HTTPBearer()


def token_status(token: str) -> tuple[Permissions, bool]:
    tokens = tokensdb.get((token,))
    if tokens is None:
        return Permissions.NONE, False

    now = datetime_to_datestr(datetime.now())

    def update_token(tok: MaybeTokens) -> MaybeTokens:
        if tok is not None:
            tok["last_accessed"] = now
        return tok

    tokensdb.update(update_token, original=tokens)

    if compare_datestrs(tokens["expires_after"], now) < 0 or tokens["revoked"]:
        return Permissions.NONE, False

    return tokens["permission"], tokens["permission"] != Permissions.NONE


async def get_permission_level(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Permissions:
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=403, detail="Invalid auth scheme")

    token = credentials.credentials
    permission, valid = token_status(token)
    if not valid:
        log_access("INVALID_KEY", token, request, success=False)
        raise HTTPException(status_code=403, detail="Invalid or revoked token")

    return permission


def require_permission(min_permission: Permissions):
    async def guard(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        permission: Permissions = Depends(get_permission_level),
    ) -> None:
        if permission < min_permission:
            log_access(
                "INSUFFICIENT_PERMISSION",
                credentials.credentials,
                request,
                success=False,
            )
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    return guard
