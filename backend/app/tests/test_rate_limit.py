# ==============================================================================
# CampusGPT Backend — Rate Limit Tests
# ==============================================================================
from app.core.config import settings


async def test_login_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    payload = {"email": "ratelimit@college.edu", "password": "wrongpassword123"}

    statuses = [
        (await client.post("/api/v1/auth/login", json=payload)).status_code
        for _ in range(settings.rate_limit_auth_per_minute)
    ]
    assert 429 not in statuses

    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


async def test_one_locked_account_does_not_block_others_on_the_same_network(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    target = {"email": "someone-else@college.edu", "password": "wrongpassword123"}
    for _ in range(settings.rate_limit_auth_per_minute + 1):
        await client.post("/api/v1/auth/login", json=target)
    assert (await client.post("/api/v1/auth/login", json=target)).status_code == 429

    classmate = {"email": "classmate@college.edu", "password": "wrongpassword123"}
    assert (await client.post("/api/v1/auth/login", json=classmate)).status_code == 401
