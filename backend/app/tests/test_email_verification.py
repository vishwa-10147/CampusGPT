# ==============================================================================
# CampusGPT Backend — Email Verification Tests
# ==============================================================================
from uuid import UUID

import pytest

from app.api.v1 import auth as auth_routes
from app.core.config import settings
from app.core.security import create_access_token, create_email_verification_token

USER = {
    "email": "verify-me@college.edu",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "full_name": "Verify Me",
}
LOGIN = {"email": USER["email"], "password": USER["password"]}


@pytest.fixture
def sent_emails(monkeypatch):
    """Turn verification on and capture verification emails instead of sending them."""
    monkeypatch.setattr(settings, "require_email_verification", True)
    sent = []

    async def capture(user_id, email):
        sent.append((user_id, email))

    monkeypatch.setattr(auth_routes, "send_verification_email", capture)
    return sent


async def test_unverified_user_cannot_log_in_until_link_is_used(client, sent_emails):
    response = await client.post("/api/v1/auth/register", json=USER)
    assert response.status_code == 201
    assert response.json()["email_verified"] is False
    assert sent_emails == [(UUID(response.json()["id"]), USER["email"])]

    assert (await client.post("/api/v1/auth/login", json=LOGIN)).status_code == 403

    token = create_email_verification_token(sent_emails[0][0])
    verified = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 200
    assert verified.json()["email_verified"] is True

    assert (await client.post("/api/v1/auth/login", json=LOGIN)).status_code == 200


async def test_wrong_password_is_401_even_when_unverified(client, sent_emails):
    await client.post("/api/v1/auth/register", json=USER)
    response = await client.post("/api/v1/auth/login", json={**LOGIN, "password": "wrongpassword"})
    assert response.status_code == 401


async def test_other_token_types_are_rejected_as_verification_links(client, sent_emails):
    response = await client.post("/api/v1/auth/register", json=USER)
    access_token = create_access_token(UUID(response.json()["id"]))
    for token in (access_token, "not-a-token"):
        assert (await client.post("/api/v1/auth/verify-email", json={"token": token})).status_code == 400


async def test_resend_answers_the_same_for_unknown_and_unverified_emails(client, sent_emails):
    await client.post("/api/v1/auth/register", json=USER)
    sent_emails.clear()

    known = await client.post("/api/v1/auth/resend-verification", json={"email": USER["email"]})
    unknown = await client.post("/api/v1/auth/resend-verification", json={"email": "nobody@college.edu"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert [email for _, email in sent_emails] == [USER["email"]]
