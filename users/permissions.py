from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from artists.models import ArtistProfile


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsPromoter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'promoter'


class IsArtist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'artist'


class IsArtistOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user and request.user.role == 'artist'


class IsFan(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'fan'


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsArtistManager(permissions.BasePermission):
    """
    Autorise uniquement si le promoteur est manager de l’artiste ciblé.
    Nécessite que la vue ait accès à un `artist_id` dans les kwargs.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.role != 'promoter':
            return False

        artist_id = view.kwargs.get('artist_id')
        if not artist_id:
            return False

        try:
            artist = ArtistProfile.objects.get(id=artist_id)
        except ArtistProfile.DoesNotExist:
            return False

        return artist.is_managed_by(request.user)


class IsEventOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user


class IsAdminOrPromoter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (
            request.user.role in ['admin', 'promoter']
        )
