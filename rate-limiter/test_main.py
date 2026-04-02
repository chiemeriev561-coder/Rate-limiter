from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_not_rate_limited():
    for _ in range(20):
        response = client.get("/health")
    assert response.status_code == 200

def test_rate_limit_triggers():
    for _ in range(6):
        response = client.get("/")
    assert response.status_code == 429

def test_429_headers_present():
    for _ in range(6):
        response = client.get("/")
    assert "X-RateLimit-Limit" in response.headers
    assert "Retry-After" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "0"