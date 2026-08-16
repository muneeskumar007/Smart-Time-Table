import pytest

from app.auth.jwt_handler import TokenError, create_access_token, create_refresh_token, decode_token


def test_access_token_round_trips_with_correct_claims():
    token = create_access_token(user_id="abc123", role="hod")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "abc123"
    assert payload["role"] == "hod"
    assert payload["type"] == "access"
    assert "jti" in payload


def test_refresh_token_round_trips_with_correct_claims():
    token = create_refresh_token(user_id="abc123", role="student")
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "abc123"
    assert payload["type"] == "refresh"


def test_remember_me_refresh_token_lasts_longer_than_a_normal_one():
    normal = decode_token(create_refresh_token("u1", "faculty", remember_me=False), expected_type="refresh")
    remembered = decode_token(create_refresh_token("u1", "faculty", remember_me=True), expected_type="refresh")
    assert (remembered["exp"] - remembered["iat"]) > (normal["exp"] - normal["iat"])


def test_an_access_token_is_rejected_when_a_refresh_token_is_expected():
    token = create_access_token(user_id="abc123", role="student")
    with pytest.raises(TokenError):
        decode_token(token, expected_type="refresh")


def test_a_tampered_token_is_rejected():
    token = create_access_token(user_id="abc123", role="student")
    tampered = token[:-3] + ("xyz" if not token.endswith("xyz") else "abc")
    with pytest.raises(TokenError):
        decode_token(tampered, expected_type="access")


def test_every_token_gets_a_unique_jti():
    payload_a = decode_token(create_access_token("u1", "faculty"), expected_type="access")
    payload_b = decode_token(create_access_token("u1", "faculty"), expected_type="access")
    assert payload_a["jti"] != payload_b["jti"]
