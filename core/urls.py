from django.urls import path
from core.views import (
    LoginAPIView,
    ActiveServicesListAPIView,
    ServiceDetailAPIView,
    AllReviewsListAPIView,
    ReviewStatisticsAPIView,
    AllUsersListAPIView,
    CreateCollaboratorAPIView,
    DeactivateUserAPIView,
    ServiceAdminListAPIView,
    ServiceCreateAPIView,
    ServiceRetrieveUpdateDestroyAPIView,
    ServiceToggleActiveAPIView,
    TemplateAdminListAPIView,
    TemplateCreateAPIView,
    TemplateRetrieveUpdateDestroyAPIView,
    OrderListCreateAPIView,
    OrderRetrieveUpdateDestroyAPIView,
    OrderStatusUpdateAPIView,
    OrderCollaboratorAssignAPIView,
    StatusListAPIView,
    ActiveCollaboratorListAPIView,
    CollaboratorOrderListAPIView,
    ClientOrderListAPIView
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
    
    # Admin - Service Management (Admin Only)
    path('admin/services/', ServiceAdminListAPIView.as_view(), name='admin-services-list'),
    path('admin/services/create/', ServiceCreateAPIView.as_view(), name='admin-service-create'),
    path('admin/services/<int:pk>/', ServiceRetrieveUpdateDestroyAPIView.as_view(), name='admin-service-detail'),
    path('admin/services/<int:pk>/toggle-active/', ServiceToggleActiveAPIView.as_view(), name='admin-service-toggle-active'),
    
    # Admin - Template Management (Admin Only)
    path('admin/templates/', TemplateAdminListAPIView.as_view(), name='admin-templates-list'),
    path('admin/templates/create/', TemplateCreateAPIView.as_view(), name='admin-template-create'),
    path('admin/templates/<int:pk>/', TemplateRetrieveUpdateDestroyAPIView.as_view(), name='admin-template-detail'),
    
    # Admin - Order Management (Admin Only)
    path('admin/orders/', OrderListCreateAPIView.as_view(), name='admin-orders-list'),
    path('admin/orders/<int:pk>/', OrderRetrieveUpdateDestroyAPIView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='admin-order-status-update'),
    path('admin/orders/<int:pk>/assign-collaborator/', OrderCollaboratorAssignAPIView.as_view(), name='admin-order-assign-collaborator'),
    path('admin/statuses/', StatusListAPIView.as_view(), name='admin-statuses-list'),
    path('admin/active-collaborators/', ActiveCollaboratorListAPIView.as_view(), name='admin-active-collaborators-list'),
    
    # Collaborator - Order Management (Collaborator Only)
    path('collaborator/orders/', CollaboratorOrderListAPIView.as_view(), name='collaborator-orders-list'),
    path('collaborator/orders/<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='collaborator-order-status-update'),
    path('collaborator/statuses/', StatusListAPIView.as_view(), name='collaborator-statuses-list'),
    
    # Client - Order Management (Client Only)
    path('client/orders/', ClientOrderListAPIView.as_view(), name='client-orders-list'),
]