import os
import secrets as secrets_module
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt


JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
_BCRYPT_MAX_BYTES = 72


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if secret:
        return secret
    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENV") == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY must be set in production. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    return "dev-only-jwt-secret-do-not-use-in-prod"


def _encode_password(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_encode_password(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_encode_password(plain), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (JWTError, ValueError):
        return None


def generate_share_token() -> str:
    return secrets_module.token_urlsafe(16)
