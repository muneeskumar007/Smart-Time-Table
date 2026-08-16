from app.auth.security import DUMMY_HASH, hash_password, verify_password


def test_hash_password_produces_a_different_string_than_the_input():
    hashed = hash_password("MySecurePass123")
    assert hashed != "MySecurePass123"
    assert len(hashed) > 20


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("MySecurePass123")
    assert verify_password("MySecurePass123", hashed) is True


def test_verify_password_rejects_an_incorrect_password():
    hashed = hash_password("MySecurePass123")
    assert verify_password("WrongPassword", hashed) is False


def test_hashing_the_same_password_twice_gives_different_hashes():
    # Argon2 (like bcrypt) salts automatically, so two hashes of the same
    # password must never be identical.
    first = hash_password("RepeatMe123")
    second = hash_password("RepeatMe123")
    assert first != second
    assert verify_password("RepeatMe123", first) is True
    assert verify_password("RepeatMe123", second) is True


def test_dummy_hash_never_verifies_against_a_real_password():
    assert verify_password("anything at all", DUMMY_HASH) is False
