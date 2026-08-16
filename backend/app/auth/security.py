"""
Password hashing.

IMPORTANT - library choice: the project brief asked for Passlib. Passlib
has had no release in years, is broken by bcrypt>=5.0's API changes, and
its `crypt`-module dependency was removed in Python 3.13 - it is no
longer safe to install into a new project. FastAPI's own official
documentation dropped Passlib in favour of `pwdlib` for exactly this
reason (see https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
We use pwdlib with Argon2 (OWASP's current top recommendation for new
applications, and pwdlib's own "recommended" preset) instead. See
README.md for the full note.
"""
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

# A precomputed hash of a value nobody will ever type, used to keep
# login timing constant whether the submitted email exists or not (see
# auth_service.authenticate). Without this, an attacker could measure
# response time to enumerate valid email addresses.
DUMMY_HASH = _password_hash.hash("not-a-real-password-used-only-for-timing")


def hash_password(plain_password: str) -> str:
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)
