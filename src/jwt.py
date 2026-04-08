from datetime import datetime, timedelta, UTC

import jwt


def encode_token(
    user_id: str,
    github_login: str,
    secret: str,
    ttl_minutes: int,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "github_login": github_login,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])
