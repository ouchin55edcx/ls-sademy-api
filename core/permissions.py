"""
Custom Permissions
Place this file in: core/permissions.py
"""

from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to allow only admin users.
    Checks if the user has an admin_profile.
    """
    message = 'You do not have permission to perform this action. Admin access required.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin profile
        return hasattr(request.user, 'admin_profile')

