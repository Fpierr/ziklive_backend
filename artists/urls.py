#!/usr/bin/env python
"""Artist urls"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from artists.views import ArtistProfileViewSet, ArtistManagerViewSet, VerifyArtistEmailView

router = DefaultRouter()
router.register(r'', ArtistProfileViewSet, basename='artist')
router.register(r'managers', ArtistManagerViewSet, basename='artistmanager')

urlpatterns = [
    path('', include(router.urls)),
    path('verify-email/', VerifyArtistEmailView.as_view(), name='verify-artist-email'),
]
