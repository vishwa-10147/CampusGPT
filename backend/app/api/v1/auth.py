# ==============================================================================
# CampusGPT Backend — Auth API Routes
# ==============================================================================
from fastapi import APIRouter, BackgroundTasks, Depends, Response, HTTPException, status, Cookie
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.rate_limit import auth_rate_limit
from app.api.deps import get_auth_service, get_current_user_id, get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
    MessageResponse,
)
from app.services.auth_service import AuthService, EmailNotVerifiedError
from app.services.email_service import send_verification_email
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Cookie settings
COOKIE_SETTINGS = {
    "httponly": True,
    "secure": not settings.is_development,
    "samesite": "lax",
}
REFRESH_COOKIE_PATH = "/api/v1/auth"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set the access cookie (all routes) and the refresh cookie (auth routes only)."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **COOKIE_SETTINGS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        **COOKIE_SETTINGS,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limit)],
)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user; unverified accounts are emailed a confirmation link."""
    try:
        user = await auth_service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not user.email_verified:
        background_tasks.add_task(send_verification_email, user.id, user.email)
    return user


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)])
async def login(
    response: Response,
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login and set auth cookies."""
    try:
        token_response, refresh_token = await auth_service.login(data)
    except EmailNotVerifiedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_auth_cookies(response, token_response.access_token, refresh_token)
    return token_response


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    data: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm an email address using the token from the emailed link."""
    try:
        return await auth_service.verify_email(data.token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    dependencies=[Depends(auth_rate_limit)],
)
async def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Send a new verification link. Always answers the same way, so it can't reveal which emails exist."""
    user = await auth_service.get_unverified_user(data.email)
    if user:
        background_tasks.add_task(send_verification_email, user.id, user.email)
    return MessageResponse(message="If that account needs confirming, a new link is on its way.")


@router.post("/logout")
async def logout(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Logout and clear cookies."""
    response.delete_cookie("access_token", **COOKIE_SETTINGS)
    response.delete_cookie("refresh_token", path=REFRESH_COOKIE_PATH, **COOKIE_SETTINGS)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        token_response, new_refresh_token = await auth_service.refresh_token(refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    set_auth_cookies(response, token_response.access_token, new_refresh_token)
    return token_response
