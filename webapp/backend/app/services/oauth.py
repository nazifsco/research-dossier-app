"""
OAuth service for Google authentication.
"""

from typing import Optional
from urllib.parse import urlencode
import httpx

from app.config import get_settings

settings = get_settings()


class GoogleOAuth:
    """Google OAuth 2.0 helper."""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    SCOPES = ["openid", "email", "profile"]

    @classmethod
    def get_authorization_url(cls, state: str, redirect_uri: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: CSRF protection token
            redirect_uri: Callback URL after authorization

        Returns:
            Full authorization URL to redirect user to
        """
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(cls.SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",  # Always show account picker
        }
        return f"{cls.AUTH_URL}?{urlencode(params)}"

    @classmethod
    async def exchange_code(cls, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Google callback
            redirect_uri: Must match the one used in authorization

        Returns:
            Token response containing access_token, id_token, etc.

        Raises:
            Exception: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                cls.TOKEN_URL,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )

            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")

            return response.json()

    @classmethod
    async def get_user_info(cls, access_token: str) -> dict:
        """
        Get user profile information from Google.

        Args:
            access_token: Valid Google access token

        Returns:
            User info dict with id, email, name, picture

        Raises:
            Exception: If user info request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                cls.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get user info: {response.text}")

            return response.json()


def is_google_oauth_configured() -> bool:
    """Check if Google OAuth is properly configured."""
    return bool(settings.google_client_id and settings.google_client_secret)
