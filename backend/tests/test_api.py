import pytest

from app import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_health(client):
    assert client.get("/api/health").json == {"status": "ok"}


@pytest.mark.parametrize("path", ["/api/files", "/api/dashboard/stats", "/api/backups/history",
                                  "/api/cloud/b2/status", "/api/simulation"])
def test_protected_routes_require_auth(client, path):
    r = client.get(path)
    assert r.status_code == 401 and "error" in r.json


def test_register_validates_input(client):
    assert client.post("/api/auth/register", json={"email": "bad", "password": "12345678"}).status_code == 400
    assert client.post("/api/auth/register", json={"email": "a@b.co", "password": "short"}).status_code == 400
