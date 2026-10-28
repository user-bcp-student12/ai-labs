import os

import jwt
from jwt.exceptions import InvalidKeyError, InvalidTokenError

JWT_ALGORITHM = "RS256"
PUBLIC_KEY_SETTING = "AUTH_JWT_PUBLIC_KEY"
ISSUER_SETTING = "AUTH_JWT_ISSUER"
AUDIENCE_SETTING = "AUTH_JWT_AUDIENCE"
REQUIRED_CLAIMS = ["sub", "role", "exp", "iss", "aud"]


class AuthenticationConfigurationError(Exception):
    pass


def verify_token(token: str) -> dict[str, str]:
    public_key = os.getenv(PUBLIC_KEY_SETTING)
    issuer = os.getenv(ISSUER_SETTING)
    audience = os.getenv(AUDIENCE_SETTING)
    if not public_key or not issuer or not audience:
        raise AuthenticationConfigurationError("JWT verification settings are required")

    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[JWT_ALGORITHM],
            issuer=issuer,
            audience=audience,
            options={"require": REQUIRED_CLAIMS},
        )
    except InvalidKeyError as error:
        raise AuthenticationConfigurationError("JWT public key configuration is invalid") from error

    username = claims.get("sub")
    role = claims.get("role")
    if not isinstance(username, str) or not username or not isinstance(role, str) or not role:
        raise InvalidTokenError("invalid token")

    return {"username": username, "role": role}
