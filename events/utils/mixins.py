from rest_framework.exceptions import PermissionDenied

class OwnerRestrictedMixin:
    owner_field = 'created_by'

    def perform_create(self, serializer):
        serializer.save(**{self.owner_field: self.request.user})

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.owner_field: self.request.user})

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        owner = getattr(obj, self.owner_field)
        if owner != request.user:
            raise PermissionDenied("You are not allowed to edit this object.")
