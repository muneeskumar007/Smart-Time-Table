"""
Shared test fixtures.

Note: these tests exercise pure logic (password hashing, JWT
encode/decode, pagination math, response envelope shape) and do not
require a running MongoDB instance. Full integration tests against a
live database (or mongomock) are a good next addition once this Phase 1
foundation is running - see README.md "Testing" section.
"""
import os

# Ensure a JWT secret is present for anything that imports app.config.settings,
# without requiring a real .env file to exist when running tests in CI.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "smart_timetable_test_db")
