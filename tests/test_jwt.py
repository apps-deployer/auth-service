import time

import jwt as pyjwt
import pytest

from src.jwt import decode_token, encode_token


SECRET = "test-secret-key"


def test_encode_decode_roundtrip():
    token = encode_token(
        user_id="user-123",
        github_login="testuser",
        secret=SECRET,
        ttl_minutes=60,
    )
    claims = decode_token(token, SECRET)
    assert claims["sub"] == "user-123"
    assert claims["github_login"] == "testuser"


def test_token_contains_exp():
    token = encode_token(
        user_id="user-123",
        github_login="testuser",
        secret=SECRET,
        ttl_minutes=30,
    )
    claims = decode_token(token, SECRET)
    assert "exp" in claims
    assert "iat" in claims
    # exp should be ~30 min after iat
    assert claims["exp"] - claims["iat"] == pytest.approx(30 * 60, abs=5)


def test_decode_with_wrong_secret():
    token = encode_token(
        user_id="user-123",
        github_login="testuser",
        secret=SECRET,
        ttl_minutes=60,
    )
    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_token(token, "wrong-secret")


def test_expired_token():
    token = encode_token(
        user_id="user-123",
        github_login="testuser",
        secret=SECRET,
        ttl_minutes=-1,  # already expired
    )
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(token, SECRET)
