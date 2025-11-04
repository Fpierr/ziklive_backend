#!/usr/bin/env python
"""Artist views"""

from django.forms import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from artists.models import ArtistProfile

from artists.models import ArtistProfile, ArtistManager
from artists.serializers import (
    ArtistProfileSerializer,
    ArtistManagerSerializer,
    ArtistVerificationSerializer
)
from users.models import User
from users.permissions import IsPromoter
from events.utils.mixins import OwnerRestrictedMixin
from users.services.verification import trigger_verification_flow


class ArtistProfileViewSet(OwnerRestrictedMixin, ModelViewSet):
    """Artist route"""

    queryset = ArtistProfile.objects.all()
    serializer_class = ArtistProfileSerializer
    permission_classes = [IsAuthenticated]
    owner_field = 'user'

    def update(self, request, *args, **kwargs):
        """update method artist"""
        artist = self.get_object()
        if request.user.role != "artist" and not artist.email_verified:
            raise PermissionDenied("Only artist can edit profile.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update artist"""
        artist = self.get_object()
        if request.user.role != "artist" and not artist.email_verified:
            raise PermissionDenied("Only artist can update profile.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """destroy artist profile"""
        artist = self.get_object()
        if request.user.role != "artist":
            raise PermissionDenied("Only artist can delete profile.")
        if not artist.email_verified:
            raise PermissionDenied("Your email is not verified.")
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """search metho activate"""
        queryset = ArtistProfile.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset
    
    def get_permissions(self):
        """Personalised permission to artist view class"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def check_object_permissions(self, request, obj):
        """Permission check to operation important"""
        super().check_object_permissions(request, obj)
        if request.method in ["PUT", "PATCH", "DELETE"]:
            if obj.status == "invited" and obj.created_by == request.user:
                return
            if request.user.role == "artist" and obj.user == request.user:
                return
            raise PermissionDenied("You can't allow to edit this artist.")

    def perform_create(self, serializer):
        """To create artist profile"""
        if self.request.user.role != "promoter":
            raise PermissionDenied('Only promoter can create artist profile.')

        artist = serializer.save(created_by=self.request.user)

        try:
            if not artist.user and artist.email and artist.email.strip():
                user = User.objects.create(
                    email=artist.email,
                    name=artist.name,
                    role='artist',
                    is_active=False
                )
                user.set_unusable_password()
                user.save()

                artist.user = user
                artist.save()

            existing_manager = ArtistManager.objects.filter(
                artist=artist,
                promoter=self.request.user,
                end_date__isnull=True
            ).first()

            if not existing_manager:
                ArtistManager.objects.create(
                    artist=artist,
                    promoter=self.request.user
                )

            if artist.email:
                trigger_verification_flow(artist)

        except ValidationError as e:
            raise e


class ArtistManagerViewSet(OwnerRestrictedMixin, ModelViewSet):
    """Artist manager"""

    queryset = ArtistManager.objects.all()
    serializer_class = ArtistManagerSerializer
    permission_classes = [IsPromoter]
    owner_field = 'promoter'

    def perform_create(self, serializer):
        serializer.save(promoter=self.request.user)


class VerifyArtistEmailView(APIView):
    """Verify artist class"""

    def post(self, request):
        serializer = ArtistVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        artist = serializer.validated_data['artist']

        artist.email_verified = True
        artist.verification_code = None
        artist.verification_code_expiry = None
        artist.status = "active"

        if artist.user:
            artist.user.is_active = True
            artist.user.save()

        artist.save()
        return Response({"detail": "Profile activated success."}, status=200)


class SetPasswordView(APIView):
    """Set password for artist profile"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logic set pasword method to activate artist profile"""
        user = request.user
        password = request.data.get("password")
        if not password:
            return Response({"detail": "Required password."}, status=400)
        user.set_password(password)
        user.save()
        return Response({"detail": "Password defined success."}, status=200)
