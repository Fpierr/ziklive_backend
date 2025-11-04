#!/usr/bin/env python
"""Authentication midleware for user"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from users.session_manager import get_session


class CookieJWTWithRedisSessionAuth(JWTAuthentication):
    """
    Custom authentication class combining JWT, Redis, and CSRF.

    Supports two client types:
    - Web:
        - Tokens (access_token, session_id) in cookies
        - CSRF token in header: X-CSRF-Token
        - Header: X-Client-Type = "web"
    - Mobile:
        - Tokens in headers (Authorization, X-Session-Id, X-CSRF-Token)
        - Header: X-Client-Type = "mobile"

    Each client must use its designated transport mode.
    """

    def authenticate(self, request):
        """Authenticte user to access to protect routes"""
        client_type = request.headers.get("X-Client-Type")

        # Web client handling
        if client_type == "web":
            if "Authorization" in request.headers:
                raise AuthenticationFailed("Not allowed for web clients.")

            access_token = request.COOKIES.get("access_token")
            session_id = request.COOKIES.get("session_id")
            csrf_token = request.headers.get("X-CSRF-Token")

        # Mobile client handling
        elif client_type == "mobile":
            if request.COOKIES.get("access_token") or request.COOKIES.get("session_id"):
                raise AuthenticationFailed("Cookies not allowed for mobile clients.")

            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split("Bearer ")[1]
            else:
                raise AuthenticationFailed("Missing or invalid Authorization.")

            session_id = request.headers.get("X-Session-Id")
            csrf_token = request.headers.get("X-CSRF-Token")

        else:
            return None

        # Ensure all required tokens are present
        if not all([access_token, session_id, csrf_token]):
            raise AuthenticationFailed("Missing authentication elements.")

        # Validate JWT
        try:
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
        except Exception:
            raise AuthenticationFailed("Invalid or expired JWT.")

        # Validate Redis session
        session = get_session(session_id)
        if not session:
            raise AuthenticationFailed("Invalid or expired session.")

        if str(session.get("user_id")) != str(user.id):
            raise AuthenticationFailed("User mismatch in session data.")

        if session.get("csrf_token") != csrf_token:
            raise AuthenticationFailed("Invalid CSRF token.")

        return (user, validated_token)
