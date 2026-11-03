import os

import jwt
from fastapi import Header, HTTPException, status
from jwt.exceptions import InvalidTokenError

from app.models import Identity

JWT_SECRET_ENV = "WORKSHOP_JWT_SECRET"
JWT_ISSUER_ENV = "WORKSHOP_JWT_ISSUER"
JWT_AUDIENCE_ENV = "WORKSHOP_JWT_AUDIENCE"
JWT_ALGORITHM_ENV = "WORKSHOP_JWT_ALGORITHM"
DEFAULT_JWT_ALGORITHM = "HS256"
SUPPORTED_JWT_ALGORITHMS = {DEFAULT_JWT_ALGORITHM}
REQUIRED_JWT_CLAIMS = ["sub", "role", "exp", "iss", "aud"]
MINIMUM_HMAC_KEY_LENGTH = 32


def get_identity(authorization: str = Header(default="")) -> Identity:
    scheme, separator, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or " " in token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    secret = os.getenv(JWT_SECRET_ENV, "")
    issuer = os.getenv(JWT_ISSUER_ENV, "")
    audience = os.getenv(JWT_AUDIENCE_ENV, "")
    algorithm = os.getenv(JWT_ALGORITHM_ENV, DEFAULT_JWT_ALGORITHM)
    if (
        len(secret.encode("utf-8")) < MINIMUM_HMAC_KEY_LENGTH
        or not issuer
        or not audience
        or algorithm not in SUPPORTED_JWT_ALGORITHMS
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            issuer=issuer,
            audience=audience,
            options={"require": REQUIRED_JWT_CLAIMS},
        )
    except InvalidTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from error

    username = claims.get("sub")
    role = claims.get("role")
    if not isinstance(username, str) or not isinstance(role, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {"username": username, "role": role}