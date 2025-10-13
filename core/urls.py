from django.urls import path
from core.views import (
    LoginAPIView,
    ActiveServicesListAPIView,
    ServiceDetailAPIView,
    AllReviewsListAPIView,
    ReviewStatisticsAPIView,
    AllUsersListAPIView,
    CreateCollaboratorAPIView,
    DeactivateUserAPIView
)

app_name = 'core'

urlpatterns = [
    # Authentication
    path('login/', LoginAPIView.as_view(), name='login'),
    
    # Services
    path('services/', ActiveServicesListAPIView.as_view(), name='services-list'),
    path('services/<int:pk>/', ServiceDetailAPIView.as_view(), name='service-detail'),
    
    # Reviews
    path('reviews/', AllReviewsListAPIView.as_view(), name='reviews-list'),
    path('reviews/statistics/', ReviewStatisticsAPIView.as_view(), name='reviews-statistics'),
    
    # Admin - User Management (Admin Only)
    path('admin/users/', AllUsersListAPIView.as_view(), name='admin-users-list'),
    path('admin/collaborators/', CreateCollaboratorAPIView.as_view(), name='admin-create-collaborator'),
    path('admin/users/<int:pk>/deactivate/', DeactivateUserAPIView.as_view(), name='admin-deactivate-user'),
]