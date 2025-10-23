from django.urls import path
from core.views import (
    LoginAPIView,
    ActiveServicesListAPIView,
    ServiceDetailAPIView,
    DemoVideoAPIView,
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
    CollaboratorStatusAPIView,
    ActiveCollaboratorListAPIView,
    CollaboratorOrderListAPIView,
    CollaboratorStatisticsAPIView,
    ClientOrderListAPIView,
    ClientOrderCancelAPIView,
    ClientStatisticsAPIView,
    OrderStatusHistoryAPIView,
    CollaboratorLivrableListCreateAPIView,
    CollaboratorLivrableRetrieveUpdateDestroyAPIView,
    AdminLivrableListAPIView,
    AdminAllLivrableListAPIView,
    AdminLivrableRetrieveAPIView,
    AdminLivrableReviewAPIView,
    ClientLivrableListAPIView,
    ClientLivrableAcceptRejectAPIView,
    ClientReviewListCreateAPIView,
    ClientReviewRetrieveUpdateDestroyAPIView,
    LivrableFileDownloadAPIView,
    ProfileUpdateAPIView,
    AdminStatisticsAPIView,
    TestEmailAPIView,
    GlobalSettingsRetrieveUpdateAPIView
)

app_name = 'core'

urlpatterns = [
    # Authentication
    path('login/', LoginAPIView.as_view(), name='login'),
    
    # Services
    path('services/', ActiveServicesListAPIView.as_view(), name='services-list'),
    path('services/<int:pk>/', ServiceDetailAPIView.as_view(), name='service-detail'),
    path('demo-video/<int:template_id>/', DemoVideoAPIView.as_view(), name='demo-video'),
    
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
    path('admin/orders/<int:order_id>/status-history/', OrderStatusHistoryAPIView.as_view(), name='admin-order-status-history'),
    path('admin/orders/<int:pk>/assign-collaborator/', OrderCollaboratorAssignAPIView.as_view(), name='admin-order-assign-collaborator'),
    path('admin/statuses/', StatusListAPIView.as_view(), name='admin-statuses-list'),
    path('admin/active-collaborators/', ActiveCollaboratorListAPIView.as_view(), name='admin-active-collaborators-list'),
    
    # Admin - Statistics (Admin Only)
    path('admin/statistics/', AdminStatisticsAPIView.as_view(), name='admin-statistics'),
    path('admin/test-email/', TestEmailAPIView.as_view(), name='admin-test-email'),
    
    # Admin - Global Settings (Admin Only)
    path('admin/global-settings/', GlobalSettingsRetrieveUpdateAPIView.as_view(), name='admin-global-settings'),
    
    # Collaborator - Order Management (Collaborator Only)
    path('collaborator/orders/', CollaboratorOrderListAPIView.as_view(), name='collaborator-orders-list'),
    path('collaborator/orders/<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='collaborator-order-status-update'),
    path('collaborator/orders/<int:order_id>/status-history/', OrderStatusHistoryAPIView.as_view(), name='collaborator-order-status-history'),
    path('collaborator/statuses/', StatusListAPIView.as_view(), name='collaborator-statuses-list'),
    path('collaborator/status/', CollaboratorStatusAPIView.as_view(), name='collaborator-status'),
    path('collaborator/statistics/', CollaboratorStatisticsAPIView.as_view(), name='collaborator-statistics'),
    
    # Client - Order Management (Client Only)
    path('client/orders/', ClientOrderListAPIView.as_view(), name='client-orders-list'),
    path('client/orders/<int:pk>/cancel/', ClientOrderCancelAPIView.as_view(), name='client-order-cancel'),
    path('client/orders/<int:order_id>/status-history/', OrderStatusHistoryAPIView.as_view(), name='order-status-history'),
    path('client/statistics/', ClientStatisticsAPIView.as_view(), name='client-statistics'),
    
    # Collaborator - Livrable Management (Collaborator Only)
    path('collaborator/livrables/', CollaboratorLivrableListCreateAPIView.as_view(), name='collaborator-livrables-list-create'),
    path('collaborator/livrables/<int:pk>/', CollaboratorLivrableRetrieveUpdateDestroyAPIView.as_view(), name='collaborator-livrable-detail'),
    
    # Admin - Livrable Review (Admin Only)
    path('admin/livrables/', AdminLivrableListAPIView.as_view(), name='admin-livrables-list'),
    path('admin/livrables/all/', AdminAllLivrableListAPIView.as_view(), name='admin-all-livrables-list'),
    path('admin/livrables/<int:pk>/', AdminLivrableRetrieveAPIView.as_view(), name='admin-livrable-detail'),
    path('admin/livrables/<int:pk>/review/', AdminLivrableReviewAPIView.as_view(), name='admin-livrable-review'),
    
    # Client - Livrable Management (Client Only)
    path('client/livrables/', ClientLivrableListAPIView.as_view(), name='client-livrables-list'),
    path('client/livrables/<int:pk>/accept-reject/', ClientLivrableAcceptRejectAPIView.as_view(), name='client-livrable-accept-reject'),
    
    # Client - Review Management (Client Only)
    path('client/reviews/', ClientReviewListCreateAPIView.as_view(), name='client-reviews-list-create'),
    path('client/reviews/<int:pk>/', ClientReviewRetrieveUpdateDestroyAPIView.as_view(), name='client-review-detail'),
    
    # File Download (Collaborator, Client, Admin)
    path('livrables/<int:pk>/download/', LivrableFileDownloadAPIView.as_view(), name='livrable-file-download'),
    
    # Profile Update (All authenticated users)
    path('profile/update/', ProfileUpdateAPIView.as_view(), name='profile-update'),
]