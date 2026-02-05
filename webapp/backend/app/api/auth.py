"""
Authentication endpoints: register, login, logout, me, password reset, email verification, OAuth.
"""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_active_user
from app.core.redis import Cache
from app.config import get_settings
from app.services.email import send_password_reset_email, send_verification_email
from app.services.oauth import GoogleOAuth, is_google_oauth_configured

router = APIRouter()
settings = get_settings()

# OAuth state token expiry
OAUTH_STATE_EXPIRE_SECONDS = 300  # 5 minutes

# Token expiry times
PASSWORD_RESET_EXPIRE_MINUTES = 60  # 1 hour
VERIFICATION_EXPIRE_HOURS = 24


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def store_token(prefix: str, token: str, user_id: str, expire_seconds: int) -> bool:
    """Store a token in Redis or memory."""
    return Cache.set(f"{prefix}:{token}", user_id, ttl=expire_seconds)


def get_token_user_id(prefix: str, token: str) -> str | None:
    """Get user ID from token, returns None if expired/invalid."""
    return Cache.get(f"{prefix}:{token}")


def delete_token(prefix: str, token: str) -> bool:
    """Delete a used token."""
    return Cache.delete(f"{prefix}:{token}")


# Request/Response schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    credits: int
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    Returns access token on successful registration.
    Sends verification email in background.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        name=request.name,
        credits=1  # Give 1 free credit on signup
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send verification email in background
    verification_token = generate_token()
    store_token("verify", verification_token, user.id, VERIFICATION_EXPIRE_HOURS * 3600)
    verify_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
    background_tasks.add_task(send_verification_email, user.email, user.name, verify_url)

    # Generate access token
    token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiry_hours * 3600
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns access token on success.
    """
    # Find user
    user = db.query(User).filter(User.email == request.email.lower()).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if this is an OAuth-only account
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google sign-in. Please use 'Sign in with Google'."
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Generate token
    token = create_access_token(data={"sub": user.id})

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiry_hours * 3600
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user's profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        credits=current_user.credits,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout current user.
    Note: With JWT, logout is client-side (discard token).
    This endpoint exists for API completeness and future token blacklisting.
    """
    return {"message": "Successfully logged out"}


# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=100)


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.
    Always returns success to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == request.email.lower()).first()

    if user and user.is_active:
        # Generate reset token
        token = generate_token()
        store_token("reset", token, user.id, PASSWORD_RESET_EXPIRE_MINUTES * 60)

        # Send email in background
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        background_tasks.add_task(send_password_reset_email, user.email, user.name, reset_url)

    # Always return success to prevent email enumeration
    return {"message": "If an account exists with that email, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using the token from email.
    """
    # Validate token
    user_id = get_token_user_id("reset", request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Update password
    user.password_hash = hash_password(request.password)
    user.updated_at = datetime.utcnow()
    db.commit()

    # Delete used token
    delete_token("reset", request.token)

    return {"message": "Password has been reset successfully. You can now log in."}


@router.post("/send-verification")
async def send_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send email verification link to current user.
    """
    if current_user.is_verified:
        return {"message": "Email is already verified"}

    # Generate verification token
    token = generate_token()
    store_token("verify", token, current_user.id, VERIFICATION_EXPIRE_HOURS * 3600)

    # Send email in background
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    background_tasks.add_task(
        send_verification_email,
        current_user.email,
        current_user.name,
        verify_url
    )

    return {"message": "Verification email sent. Please check your inbox."}


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email using the token from email.
    """
    # Validate token
    user_id = get_token_user_id("verify", request.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Find and verify user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    user.is_verified = True
    user.updated_at = datetime.utcnow()
    db.commit()

    # Delete used token
    delete_token("verify", request.token)

    return {"message": "Email verified successfully!"}


@router.post("/resend-verification")
async def resend_verification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    """
    Resend email verification link.
    Alias for /send-verification for API consistency.
    """
    return await send_verification(background_tasks, current_user)


# ============================================================================
# Google OAuth Endpoints
# ============================================================================

@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth flow.
    Redirects user to Google's consent screen.
    """
    if not is_google_oauth_configured():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured"
        )

    # Generate state token for CSRF protection
    state = generate_token()
    store_token("oauth_state", state, "pending", OAUTH_STATE_EXPIRE_SECONDS)

    # Build callback URL
    redirect_uri = f"{settings.api_url}/api/auth/google/callback"

    # Redirect to Google
    auth_url = GoogleOAuth.get_authorization_url(state, redirect_uri)
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Creates or links user account and redirects to frontend with token.
    """
    # Handle OAuth errors
    if error:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=oauth_denied"
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=oauth_invalid"
        )

    # Verify state token (CSRF protection)
    stored_state = get_token_user_id("oauth_state", state)
    if not stored_state:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=oauth_expired"
        )
    delete_token("oauth_state", state)

    try:
        # Exchange code for tokens
        redirect_uri = f"{settings.api_url}/api/auth/google/callback"
        tokens = await GoogleOAuth.exchange_code(code, redirect_uri)

        # Get user info from Google
        user_info = await GoogleOAuth.get_user_info(tokens["access_token"])

        google_id = user_info.get("id")
        email = user_info.get("email", "").lower()
        name = user_info.get("name")

        if not google_id or not email:
            return RedirectResponse(
                url=f"{settings.frontend_url}/login?error=oauth_no_email"
            )

        # Find or create user
        user = find_or_create_oauth_user(db, google_id, email, name)

        # Generate JWT token
        token = create_access_token(data={"sub": user.id})

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback?token={token}"
        )

    except Exception as e:
        print(f"OAuth error: {e}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=oauth_failed"
        )


def find_or_create_oauth_user(db: Session, google_id: str, email: str, name: str) -> User:
    """
    Find existing user or create new one for OAuth login.
    Handles account linking for existing email accounts.
    """
    # 1. Check if user exists with this google_id
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        return user

    # 2. Check if user exists with this email (account linking)
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link Google account to existing user
        user.google_id = google_id
        user.is_verified = True  # Google verified the email
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    # 3. Create new user
    user = User(
        email=email,
        name=name,
        google_id=google_id,
        password_hash=None,  # No password for OAuth-only users
        is_verified=True,    # Google verified the email
        credits=1            # Free credit for new users
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/oauth/status")
async def oauth_status():
    """Check which OAuth providers are configured."""
    return {
        "google": is_google_oauth_configured()
    }
