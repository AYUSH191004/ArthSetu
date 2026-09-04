import time

import jwt
import pytest

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_roundtrip(self):
        hashed = hash_password("correct horse battery staple")
        assert hashed != "correct horse battery staple"
        assert verify_password("correct horse battery staple", hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("s3cret")
        assert verify_password("guess", hashed) is False

    def test_verify_is_robust_to_garbage(self):
        assert verify_password("x", "not-a-hash") is False
        assert verify_password("x", "") is False

    def test_long_password_does_not_raise(self):
        # bcrypt rejects > 72 bytes; security.py clips it.
        long_pw = "a" * 200
        hashed = hash_password(long_pw)
        assert verify_password(long_pw, hashed) is True


class TestAccessToken:
    def test_encodes_subject_and_role(self):
        token = create_access_token("alice", "admin")
        payload = decode_access_token(token)
        assert payload["sub"] == "alice"
        assert payload["role"] == "admin"

    def test_expired_token_raises(self):
        token = create_access_token("bob", "viewer", expires_minutes=-1)
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_tampered_token_raises(self):
        token = create_access_token("bob", "viewer")
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(token + "x")

    def test_wrong_secret_raises(self):
        forged = jwt.encode({"sub": "mallory", "exp": time.time() + 999},
                            "not-the-secret", algorithm="HS256")
        with pytest.raises(jwt.PyJWTError):
            decode_access_token(forged)
