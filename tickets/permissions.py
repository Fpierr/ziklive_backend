#!/usr/bin/env python
"""tickets permission"""


from rest_framework.permissions import BasePermission

class IsFan(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'fan'

class IsPromoterOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'promoter' or request.user.is_staff
        )
