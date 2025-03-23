from cyberham import dashboard_credentials, encryption_keys
from cyberham.apis.types import Body, Permissions
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
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


def authenticate(body: Body) -> Permissions:
    try:
        username = decrypt(body.credentials.username)
        password = decrypt(body.credentials.password)
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
