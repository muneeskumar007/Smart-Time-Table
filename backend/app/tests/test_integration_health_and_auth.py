"""
Integration tests - unlike every other file in this directory, these
actually boot the FastAPI app (triggering its lifespan: real MongoDB
connection, index creation, Super Admin bootstrap) and exercise it
end-to-end through Starlette's TestClient. That means they need a real,
reachable MongoDB at MONGODB_URL to pass - they are not meant to run in
an offline sandbox, and are marked `integration` so they can be run or
skipped on purpose:

    pytest -m integration          # only these
    pytest -m "not integration"    # everything except these (fast, no infra)

Run against a disposable/test database - MONGODB_DB_NAME from your .env
determines which database gets a Super Admin bootstrapped into it and
test data written to it.
"""
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.integration
class TestHealthEndpoint:
    def test_health_check_returns_success_envelope(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "healthy"


@pytest.mark.integration
class TestAuthFlow:
    def test_login_with_wrong_password_is_rejected(self, client):
        response = client.post("/api/v1/auth/login", json={"email": "admin@college.edu", "password": "definitely-wrong"})
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False

    def test_login_with_malformed_email_is_a_validation_error(self, client):
        response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "whatever123"})
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert len(body["errors"]) > 0

    def test_protected_endpoint_rejects_missing_token(self, client):
        response = client.get("/api/v1/departments")
        # get_current_user requires a Bearer token even for GET /departments
        # (every role may list departments, but you must be authenticated).
        assert response.status_code == 401

    def test_protected_endpoint_rejects_garbage_token(self, client):
        response = client.get("/api/v1/departments", headers={"Authorization": "Bearer not-a-real-token"})
        assert response.status_code == 401

    def test_unmatched_route_returns_standard_envelope_404(self, client):
        response = client.get("/api/v1/this-route-does-not-exist")
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
