from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
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
    ClientOrderCreateAPIView,
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
    GlobalSettingsRetrieveUpdateAPIView,
    ServiceCollaboratorCommissionListCreateAPIView,
    ServiceCollaboratorCommissionRetrieveUpdateDestroyAPIView,
    AdminRevenueSummaryAPIView,
    CollaboratorRevenueSummaryAPIView,
    NotificationListAPIView,
    NotificationRetrieveAPIView,
    NotificationMarkReadAPIView,
    NotificationMarkAllReadAPIView,
    NotificationStatsAPIView,
    NotificationDeleteAPIView,
    # Chatbot Views
    ChatbotLanguageListAPIView,
    ChatbotServiceListAPIView,
    ChatbotServiceDetailAPIView,
    ChatbotTemplateListAPIView,
    CollaboratorTemplateListAPIView,
    CollaboratorTemplateDownloadAPIView,
    ChatbotSessionCreateAPIView,
    ChatbotSessionUpdateAPIView,
    ChatbotClientRegistrationAPIView,
    # Public Order Creation
    OrderCreateAPIView,
    ChatbotOrderReviewAPIView,
    ChatbotOrderConfirmationAPIView
)

app_name = 'core'

urlpatterns = [
    # Authentication
    path('login/', LoginAPIView.as_view(), name='login'),
    
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
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
    path('admin/collaborator-commissions/', ServiceCollaboratorCommissionListCreateAPIView.as_view(), name='admin-collaborator-commissions'),
    path('admin/collaborator-commissions/<int:pk>/', ServiceCollaboratorCommissionRetrieveUpdateDestroyAPIView.as_view(), name='admin-collaborator-commission-detail'),
    path('admin/revenue-summary/', AdminRevenueSummaryAPIView.as_view(), name='admin-revenue-summary'),
    
    # Collaborator - Order Management (Collaborator Only)
    path('collaborator/orders/', CollaboratorOrderListAPIView.as_view(), name='collaborator-orders-list'),
    path('collaborator/orders/<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='collaborator-order-status-update'),
    path('collaborator/orders/<int:order_id>/status-history/', OrderStatusHistoryAPIView.as_view(), name='collaborator-order-status-history'),
    path('collaborator/statuses/', StatusListAPIView.as_view(), name='collaborator-statuses-list'),
    path('collaborator/status/', CollaboratorStatusAPIView.as_view(), name='collaborator-status'),
    path('collaborator/statistics/', CollaboratorStatisticsAPIView.as_view(), name='collaborator-statistics'),
    path('collaborator/revenue/', CollaboratorRevenueSummaryAPIView.as_view(), name='collaborator-revenue'),
    
    # Collaborator - Template Management (Collaborator Only)
    path('collaborator/templates/', CollaboratorTemplateListAPIView.as_view(), name='collaborator-templates-list'),
    path('collaborator/templates/<int:pk>/download/', CollaboratorTemplateDownloadAPIView.as_view(), name='collaborator-template-download'),
    
    # Client - Order Management (Client Only)
    path('client/orders/', ClientOrderListAPIView.as_view(), name='client-orders-list'),
    path('client/orders/create/', ClientOrderCreateAPIView.as_view(), name='client-order-create'),
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
    
    # Notifications (All authenticated users)
    path('notifications/', NotificationListAPIView.as_view(), name='notifications-list'),
    path('notifications/<int:pk>/', NotificationRetrieveAPIView.as_view(), name='notification-detail'),
    path('notifications/<int:pk>/mark-read/', NotificationMarkReadAPIView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read/', NotificationMarkAllReadAPIView.as_view(), name='notifications-mark-all-read'),
    path('notifications/stats/', NotificationStatsAPIView.as_view(), name='notifications-stats'),
    
    # Chatbot Workflow (Public endpoints)
    path('chatbot/language/', ChatbotLanguageListAPIView.as_view(), name='chatbot-language-list'),
    path('chatbot/session/', ChatbotSessionCreateAPIView.as_view(), name='chatbot-session-create'),
    path('chatbot/session/<str:session_id>/', ChatbotSessionUpdateAPIView.as_view(), name='chatbot-session-update'),
    path('chatbot/register/', ChatbotClientRegistrationAPIView.as_view(), name='chatbot-client-registration'),
    path('chatbot/confirm/', ChatbotOrderConfirmationAPIView.as_view(), name='chatbot-order-confirmation'),
    path('orders/review/', ChatbotOrderReviewAPIView.as_view(), name='chatbot-order-review'),
    
    # Public Order Creation (Public endpoint)
    path('orders/create/', OrderCreateAPIView.as_view(), name='order-create'),
    
    # Services and Templates for Chatbot (Public endpoints)
    path('templates/', ChatbotTemplateListAPIView.as_view(), name='chatbot-templates-list'),
]