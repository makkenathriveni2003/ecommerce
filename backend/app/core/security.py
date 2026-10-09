import hashlib
import hmac
import json
import logging
import secrets
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

logger = logging.getLogger("shopzone_security")
bearer_scheme = HTTPBearer(auto_error=False)

_TOKEN_LIFETIME_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _encode(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    encoded = value.encode("ascii")
    return urlsafe_b64decode(encoded + b"=" * (-len(encoded) % 4))


def _secret_key() -> bytes:
    secret = settings.JWT_SECRET_KEY
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 bytes")
    return secret.encode("utf-8")


def validate_token_configuration() -> None:
    _secret_key()


def hash_password(password: str) -> str:
    """Secure PBKDF2-HMAC-SHA256 password hashing with 310,000 iterations."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time password hash verification against timing attacks."""
    try:
        salt_hex, expected_hash = stored_hash.split(":", maxsplit=1)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            310_000,
        ).hex()
    except (AttributeError, TypeError, ValueError):
        return False
    return hmac.compare_digest(actual_hash, expected_hash)


def create_access_token(email: str, role: str = "shopper") -> str:
    """Generate signed JWT token containing email subject and expiration."""
    header = _encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _encode(
        json.dumps(
            {
                "sub": email,
                "role": role,
                "exp": int(time.time()) + _TOKEN_LIFETIME_SECONDS,
            },
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signing_input = f"{header}.{payload}"
    signature = hmac.new(_secret_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_encode(signature)}"


def read_access_token(token: str) -> str:
    """Parse and verify JWT token returning the user email or raising ValueError."""
    try:
        header, payload, provided_signature = token.split(".")
        claims_header = json.loads(_decode(header))
        if claims_header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("Invalid access token header")

        signing_input = f"{header}.{payload}"
        expected_signature = _encode(
            hmac.new(_secret_key(), signing_input.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise ValueError("Invalid access token signature")

        claims = json.loads(_decode(payload))
        email = claims["sub"]
        expiration = claims["exp"]
        if not isinstance(email, str) or isinstance(expiration, bool) or not isinstance(expiration, int):
            raise ValueError("Invalid access token claims")
        if expiration <= int(time.time()):
            raise ValueError("Expired access token")
        return email
    except (AttributeError, KeyError, TypeError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Invalid access token") from error


def require_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Dependency verifying valid JWT and active user account."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    try:
        email = read_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(
            status_code=401, detail="Invalid or expired access token"
        ) from error

    from ..db.database import database_connection

    with database_connection() as connection:
        user = connection.execute(
            "SELECT id, name, email, role FROM users WHERE email = %s",
            (email,),
        ).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    return dict(user)


def require_admin(
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, Any]:
    """Dependency verifying administrator privileges."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def verify_object_ownership(resource_user_id: int, current_user: dict[str, Any], resource_name: str = "Resource") -> None:
    """OWASP BOLA / IDOR protection helper: Ensure user owns resource or is admin."""
    if current_user.get("role") == "admin":
        return
    if resource_user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail=f"Access denied: You do not own this {resource_name.lower()}")
