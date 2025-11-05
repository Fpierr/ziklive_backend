#!usr/bin/env python3
"""test midleware user"""


import uuid
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from users.authentication import CookieJWTWithRedisSessionAuth
from users.session_manager import create_session

User = get_user_model()


#======== Fixtures =======================

@pytest.fixture
def user(db):
    return User.objects.create_user(
        name="Test User",
        email="test@example.com",
        password="testpass",
        role="fan"
    )

@pytest.fixture
def access_token(user):
    return str(AccessToken.for_user(user))

@pytest.fixture
def csrf_token():
    return str(uuid.uuid4())

@pytest.fixture
def session_id(user, csrf_token):
    jti = str(uuid.uuid4())
    return create_session(user.id, csrf_token, jti)

@pytest.fixture
def auth_class():
    return CookieJWTWithRedisSessionAuth()

#======== Tests =======================

@pytest.mark.django_db
def test_authenticate_web_success(auth_class, access_token, session_id, csrf_token):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CSRF_TOKEN=csrf_token, HTTP_X_CLIENT_TYPE="web")
    request.COOKIES["access_token"] = access_token
    request.COOKIES["session_id"] = session_id

    user_out, _ = auth_class.authenticate(request)
    assert user_out.email == "test@example.com"


@pytest.mark.django_db
def test_authenticate_mobile_success(auth_class, access_token, session_id, csrf_token):
    factory = APIRequestFactory()
    request = factory.get(
        "/some-endpoint",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
        HTTP_X_SESSION_ID=session_id,
        HTTP_X_CSRF_TOKEN=csrf_token,
        HTTP_X_CLIENT_TYPE="mobile",
    )

    user_out, _ = auth_class.authenticate(request)
    assert user_out.email == "test@example.com"


@pytest.mark.django_db
def test_authenticate_web_with_auth_header_rejected(auth_class, access_token, csrf_token):
    factory = APIRequestFactory()
    request = factory.get(
        "/some-endpoint",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
        HTTP_X_CSRF_TOKEN=csrf_token,
        HTTP_X_CLIENT_TYPE="web",
    )

    with pytest.raises(AuthenticationFailed, match="Not allowed for web clients."):
        auth_class.authenticate(request)


@pytest.mark.django_db
def test_authenticate_mobile_with_cookies_rejected(auth_class, access_token, session_id, csrf_token):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CSRF_TOKEN=csrf_token, HTTP_X_CLIENT_TYPE="mobile")
    request.COOKIES["access_token"] = access_token
    request.COOKIES["session_id"] = session_id

    with pytest.raises(AuthenticationFailed, match="Cookies not allowed for mobile clients."):
        auth_class.authenticate(request)


def test_authenticate_missing_tokens(auth_class):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CLIENT_TYPE="web")

    with pytest.raises(AuthenticationFailed, match="Missing authentication elements."):
        auth_class.authenticate(request)


@pytest.mark.django_db
def test_authenticate_invalid_session(auth_class, access_token, csrf_token):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CSRF_TOKEN=csrf_token, HTTP_X_CLIENT_TYPE="web")
    request.COOKIES["access_token"] = access_token
    request.COOKIES["session_id"] = "invalid-session-id"

    with pytest.raises(AuthenticationFailed, match="Invalid or expired session"):
        auth_class.authenticate(request)


@pytest.mark.django_db
def test_authenticate_invalid_jwt(auth_class, csrf_token, session_id):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CSRF_TOKEN=csrf_token, HTTP_X_CLIENT_TYPE="web")
    request.COOKIES["access_token"] = "bad.token.here"
    request.COOKIES["session_id"] = session_id

    with pytest.raises(AuthenticationFailed, match="Invalid or expired JWT"):
        auth_class.authenticate(request)


@pytest.mark.django_db
def test_authenticate_csrf_mismatch(auth_class, access_token, session_id):
    factory = APIRequestFactory()
    request = factory.get("/some-endpoint", HTTP_X_CSRF_TOKEN="wrong-csrf", HTTP_X_CLIENT_TYPE="web")
    request.COOKIES["access_token"] = access_token
    request.COOKIES["session_id"] = session_id

    with pytest.raises(AuthenticationFailed, match="Invalid CSRF token"):
        auth_class.authenticate(request)
