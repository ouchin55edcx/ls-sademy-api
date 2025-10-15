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


class IsCollaboratorUser(permissions.BasePermission):
    """
    Permission class to allow only collaborator users.
    Checks if the user has a collaborator_profile and is active.
    """
    message = 'You do not have permission to perform this action. Collaborator access required.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has collaborator profile and is active
        return (hasattr(request.user, 'collaborator_profile') and 
                request.user.collaborator_profile.is_active)


class IsClientUser(permissions.BasePermission):
    """
    Permission class to allow only client users.
    Checks if the user has a client_profile.
    """
    message = 'You do not have permission to perform this action. Client access required.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has client profile
        return hasattr(request.user, 'client_profile')


class IsAdminOrCollaboratorUser(permissions.BasePermission):
    """
    Permission class to allow admin or collaborator users.
    """
    message = 'You do not have permission to perform this action. Admin or Collaborator access required.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has admin or collaborator profile
        return (hasattr(request.user, 'admin_profile') or 
                (hasattr(request.user, 'collaborator_profile') and 
                 request.user.collaborator_profile.is_active))

