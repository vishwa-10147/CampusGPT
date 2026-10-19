# ==============================================================================
# CampusGPT Backend — Rate Limiting
# ==============================================================================
import time

from fastapi import HTTPException, Request, status
from limits import RateLimitItemPerHour, RateLimitItemPerMinute, RateLimitItem
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from app.core.config import settings

# In-process storage: fine for a single backend instance. Use Redis storage
# (limits.storage.RedisStorage) if the API is scaled to several workers.
_limiter = MovingWindowRateLimiter(MemoryStorage())


def rate_limit(item: RateLimitItem, scope: str):
    """FastAPI dependency: allow `item` requests per client IP for `scope`, else 429."""

    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        client_ip = request.client.host if request.client else "unknown"
        if not _limiter.hit(item, scope, client_ip):
            reset_at, _ = _limiter.get_window_stats(item, scope, client_ip)
            retry_after = max(1, int(reset_at - time.time()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please slow down",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency


auth_rate_limit = rate_limit(RateLimitItemPerMinute(settings.rate_limit_auth_per_minute), "auth")
chat_rate_limit = rate_limit(RateLimitItemPerMinute(settings.rate_limit_chat_per_minute), "chat")
upload_rate_limit = rate_limit(RateLimitItemPerHour(settings.rate_limit_upload_per_hour), "upload")
