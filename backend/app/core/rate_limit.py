# ==============================================================================
# CampusGPT Backend — Rate Limiting
# ==============================================================================
import json
import time

from fastapi import HTTPException, Request, status
from limits import RateLimitItem, RateLimitItemPerHour, RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from app.core.config import settings

# In-process storage: fine for a single backend instance. Use Redis storage
# (limits.storage.RedisStorage) if the API is scaled to several workers.
_limiter = MovingWindowRateLimiter(MemoryStorage())


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check(item: RateLimitItem, scope: str, key: str) -> None:
    if not _limiter.hit(item, scope, key):
        reset_at, _ = _limiter.get_window_stats(item, scope, key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please slow down",
            headers={"Retry-After": str(max(1, int(reset_at - time.time())))},
        )


def rate_limit(item: RateLimitItem, scope: str):
    """FastAPI dependency: allow `item` requests per client IP for `scope`, else 429."""

    async def dependency(request: Request) -> None:
        if settings.rate_limit_enabled:
            _check(item, scope, _client_ip(request))

    return dependency


async def auth_rate_limit(request: Request) -> None:
    """Limit sign-in style requests per account, with a looser cap per IP.

    Many students share one campus IP, so a strict per-IP limit would let one
    person lock everyone out. The tight limit is per IP + email (guessing one
    account's password); the per-IP limit only stops spraying many accounts.
    """
    if not settings.rate_limit_enabled:
        return
    ip = _client_ip(request)
    _check(RateLimitItemPerMinute(settings.rate_limit_auth_per_ip_per_minute), "auth-ip", ip)

    try:
        email = str(json.loads(await request.body()).get("email", "")).strip().lower()
    except (ValueError, AttributeError):
        email = ""
    _check(RateLimitItemPerMinute(settings.rate_limit_auth_per_minute), "auth", f"{ip}:{email}")


chat_rate_limit = rate_limit(RateLimitItemPerMinute(settings.rate_limit_chat_per_minute), "chat")
upload_rate_limit = rate_limit(RateLimitItemPerHour(settings.rate_limit_upload_per_hour), "upload")
