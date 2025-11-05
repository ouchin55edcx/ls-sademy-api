"""
API Views
Place this file in: core/views.py
"""

from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import login, get_user_model
from django.db import models
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
from core.models import Service, Review, Template, Order, Status, Collaborator, Livrable, OrderStatusHistory, GlobalSettings, Language, ChatbotSession, Client
from core.serializers import (
    LoginSerializer, UserSerializer, ServiceListSerializer,
    ServiceDetailSerializer, AllReviewsSerializer, ReviewSerializer, ReviewCreateUpdateSerializer,
    UserListSerializer, CreateCollaboratorSerializer, CreateCollaboratorAdminSerializer, DeactivateUserSerializer,
    ServiceCreateUpdateSerializer, ServiceAdminListSerializer, ServiceToggleActiveSerializer,
    TemplateSerializer, TemplateCreateUpdateSerializer, CollaboratorTemplateSerializer,
    OrderListSerializer, OrderCreateUpdateSerializer, OrderDetailSerializer,
    OrderStatusUpdateSerializer, OrderCancelSerializer, OrderCollaboratorAssignSerializer,
    ClientOrderCreateSerializer,
    StatusSerializer, ActiveCollaboratorListSerializer, OrderStatusHistorySerializer,
    LivrableCreateUpdateSerializer, LivrableListSerializer, LivrableDetailSerializer,
    LivrableAcceptRejectSerializer, LivrableAdminReviewSerializer, ProfileUpdateSerializer,
    GlobalSettingsSerializer, NotificationSerializer, NotificationListSerializer, NotificationStatsSerializer,
    LanguageSerializer, ChatbotSessionSerializer, ChatbotSessionCreateSerializer,
    ChatbotSessionUpdateSerializer, ChatbotClientRegistrationSerializer,
    ChatbotOrderReviewSerializer, ChatbotOrderConfirmationSerializer, ChatbotOrderResponseSerializer
)
from core.permissions import IsAdminUser, IsCollaboratorUser, IsClientUser, IsAdminOrCollaboratorUser
from core.email_service import EmailService
import logging

User = get_user_model()


class LoginAPIView(APIView):
    """
    POST /api/login/
    Login with username/phone and password
    
    Request body:
    {
        "username_or_phone": "client1" or "+212600000004",
        "password": "client123"
    }
    
    Response:
    {
        "token": "your-auth-token",
        "user": {
            "id": 1,
            "username": "client1",
            "email": "client1@example.com",
            "first_name": "Youssef",
            "last_name": "Tazi",
            "phone": "+212600000004",
            "role": "client",
            "role_id": 1
        },
        "message": "Login successful"
    }
    
    Role types:
    - admin: Superuser with admin privileges
    - collaborator: Team member with collaboration access
    - client: Customer with client access
    - user: Basic user without specific role
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActiveServicesListAPIView(generics.ListAPIView):
    """
    GET /api/services/
    Get all active services with templates count, reviews count and average rating
    
    Response:
    [
        {
            "id": 1,
            "name": "Web Development",
            "price": "5000.00",
            "description": "Professional web development services...",
            "tool_name": "React, Django",
            "is_active": true,
            "templates_count": 3,
            "reviews_count": 5,
            "average_rating": 4.8
        }
    ]
    """
    permission_classes = [AllowAny]
    serializer_class = ServiceListSerializer
    queryset = Service.objects.filter(is_active=True).order_by('name')


class ServiceDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/services/{id}/
    Get service details by ID with related templates and reviews
    Public endpoint for visitors
    
    Response:
    {
        "id": 1,
        "name": "Web Development",
        "price": "5000.00",
        "description": "Professional web development services...",
        "tool_name": "React, Django, PostgreSQL",
        "is_active": true,
        "templates": [
            {
                "id": 1,
                "title": "E-commerce Website Template",
                "description": "Modern e-commerce template with shopping cart",
                "file": "/templates/ecommerce-template.zip",
                "demo": "https://demo.example.com/ecommerce"
            },
            {
                "id": 2,
                "title": "Portfolio Website Template",
                "description": "Clean portfolio template for professionals",
                "file": "/templates/portfolio-template.zip",
                "demo": "https://demo.example.com/portfolio"
            }
        ],
        "reviews_count": 5,
        "average_rating": 4.8,
        "recent_reviews": [
            {
                "id": 1,
                "livrable_name": "E-commerce Website Final Delivery",
                "order_id": 1,
                "client_name": "Youssef Tazi",
                "service_name": "Web Development",
                "rating": 5,
                "comment": "Outstanding work!",
                "date": "2024-10-10T10:00:00Z"
            }
        ]
    }
    """
    permission_classes = [AllowAny]
    serializer_class = ServiceDetailSerializer
    queryset = Service.objects.all()


class DemoVideoAPIView(APIView):
    """
    GET /api/demo-video/{template_id}/
    Stream demo video for a specific template
    Public endpoint for visitors
    
    Example:
    GET /api/demo-video/1/
    
    Response: Video file stream with appropriate headers
    """
    permission_classes = [AllowAny]
    
    def get(self, request, template_id):
        """Stream demo video file"""
        try:
            # Get the template
            template = get_object_or_404(Template, id=template_id)
            
            # Check if template has a demo video
            if not template.demo_video:
                return Response(
                    {'error': 'No demo video available for this template'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get the file path
            file_path = template.demo_video.path
            
            # Check if file exists
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'Demo video file not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get file extension for content type
            file_extension = os.path.splitext(file_path)[1].lower()
            content_types = {
                '.mp4': 'video/mp4',
                '.avi': 'video/avi',
                '.mov': 'video/quicktime',
                '.webm': 'video/webm',
                '.mkv': 'video/x-matroska'
            }
            
            content_type = content_types.get(file_extension, 'video/mp4')
            
            # Create file response with appropriate headers
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type,
                as_attachment=False  # Stream the video instead of downloading
            )
            
            # Add headers for video streaming
            response['Accept-Ranges'] = 'bytes'
            response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error streaming demo video: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AllReviewsListAPIView(generics.ListAPIView):
    """
    GET /api/reviews/
    Get all reviews with optional filtering
    
    Query parameters:
    - service_id: Filter by service ID
    - rating: Filter by rating (1-5)
    - ordering: Order by 'date' or '-date' (default: -date)
    
    Examples:
    - GET /api/reviews/ - Get all reviews
    - GET /api/reviews/?service_id=1 - Get reviews for service ID 1
    - GET /api/reviews/?rating=5 - Get 5-star reviews
    - GET /api/reviews/?ordering=date - Order by oldest first
    
    Response:
    [
        {
            "id": 1,
            "service_id": 1,
            "service_name": "Web Development",
            "livrable_name": "E-commerce Website Final Delivery",
            "client_name": "Youssef Tazi",
            "rating": 5,
            "comment": "Outstanding work!",
            "date": "2024-10-10T10:00:00Z"
        }
    ]
    """
    permission_classes = [AllowAny]
    serializer_class = AllReviewsSerializer
    
    def get_queryset(self):
        queryset = Review.objects.select_related(
            'order__service',
            'order__client__user',
            'client__user'
        ).filter(client__isnull=False)
        
        # Filter by service_id if provided
        service_id = self.request.query_params.get('service_id', None)
        if service_id:
            queryset = queryset.filter(order__service__id=service_id)
        
        # Filter by rating if provided
        rating = self.request.query_params.get('rating', None)
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Order by date (default: newest first)
        ordering = self.request.query_params.get('ordering', '-date')
        queryset = queryset.order_by(ordering)
        
        return queryset


class ReviewStatisticsAPIView(APIView):
    """
    GET /api/reviews/statistics/
    Get overall review statistics
    
    Response:
    {
        "total_reviews": 25,
        "average_rating": 4.6,
        "rating_distribution": {
            "5": 15,
            "4": 7,
            "3": 2,
            "2": 1,
            "1": 0
        },
        "services_with_reviews": 5
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        reviews = Review.objects.filter(client__isnull=False)
        total_reviews = reviews.count()
        
        if total_reviews == 0:
            return Response({
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {
                    '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
                },
                'services_with_reviews': 0
            })
        
        # Calculate average rating
        total_rating = sum([review.rating for review in reviews])
        average_rating = round(total_rating / total_reviews, 2)
        
        # Rating distribution
        rating_distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
        
        # Services with reviews
        services_with_reviews = Service.objects.filter(
            orders__reviews__isnull=False
        ).distinct().count()
        
        return Response({
            'total_reviews': total_reviews,
            'average_rating': average_rating,
            'rating_distribution': rating_distribution,
            'services_with_reviews': services_with_reviews
        })


# Admin-Only Views for User Management

class AllUsersListAPIView(generics.ListAPIView):
    """
    GET /api/admin/users/
    Get all users (admin only)
    
    Query parameters:
    - role: Filter by role (admin, collaborator, client)
    - status: Filter by status (active, inactive, blacklisted)
    
    Examples:
    - GET /api/admin/users/ - Get all users
    - GET /api/admin/users/?role=collaborator - Get all collaborators
    - GET /api/admin/users/?role=client - Get all clients
    - GET /api/admin/users/?status=active - Get all active users
    - GET /api/admin/users/?status=inactive - Get all inactive users
    - GET /api/admin/users/?status=blacklisted - Get all blacklisted clients
    - GET /api/admin/users/?role=collaborator&status=active - Get active collaborators
    
    Response:
    [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@sademiy.com",
            "first_name": "Super",
            "last_name": "Admin",
            "full_name": "Super Admin",
            "phone": "+212600000001",
            "role": "admin",
            "is_active": true,
            "is_active_collab": null,
            "date_joined": "2024-10-10T10:00:00Z",
            "last_login": "2024-10-13T09:00:00Z"
        }
    ]
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserListSerializer
    
    def get_queryset(self):
        queryset = User.objects.select_related(
            'admin_profile',
            'collaborator_profile', 
            'client_profile'
        ).all().order_by('username')
        
        # Filter by role if provided
        role = self.request.query_params.get('role', None)
        if role:
            if role == 'admin':
                queryset = queryset.filter(admin_profile__isnull=False)
            elif role == 'collaborator':
                queryset = queryset.filter(collaborator_profile__isnull=False)
            elif role == 'client':
                queryset = queryset.filter(client_profile__isnull=False)
        
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status:
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
            elif status == 'blacklisted':
                queryset = queryset.filter(client_profile__is_blacklisted=True)
        
        return queryset


class CreateCollaboratorAPIView(generics.CreateAPIView):
    """
    POST /api/admin/collaborators/
    Create a new collaborator with auto-generated password (admin only)
    
    Request body:
    {
        "username": "new_collab",
        "email": "newcollab@sademiy.com",
        "first_name": "Hassan",
        "last_name": "Alami",
        "phone": "+212600000010"
    }
    
    Response:
    {
        "id": 5,
        "username": "new_collab",
        "email": "newcollab@sademiy.com",
        "first_name": "Hassan",
        "last_name": "Alami",
        "phone": "+212600000010",
        "role": "collaborator",
        "role_id": 5,
        "email_sent": true
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = CreateCollaboratorAdminSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send email with login credentials
        email_sent = False
        if hasattr(user, '_generated_password'):
            try:
                email_sent = EmailService.send_collaborator_account_created_email(
                    user, user._generated_password
                )
            except Exception as e:
                logging.error(f"Failed to send collaborator account creation email: {str(e)}")
        
        # Return user data with role information and email status
        response_data = UserSerializer(user).data
        response_data['email_sent'] = email_sent
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class DeactivateUserAPIView(APIView):
    """
    PATCH /api/admin/users/{id}/deactivate/
    Deactivate or activate a user (admin only)
    
    Request body:
    {
        "is_active": false
    }
    
    Response:
    {
        "message": "User deactivated successfully",
        "user": {
            "id": 3,
            "username": "client1",
            "email": "client1@example.com",
            "first_name": "Youssef",
            "last_name": "Tazi",
            "full_name": "Youssef Tazi",
            "phone": "+212600000004",
            "role": "client",
            "is_active": false,
            "is_active_collab": null,
            "date_joined": "2024-10-10T10:00:00Z",
            "last_login": "2024-10-13T09:00:00Z"
        }
    }
    
    Note: 
    - When a user is deactivated (is_active=false), they cannot login
    - Admin users cannot be deactivated
    - For collaborators, both user.is_active and collaborator.is_active are updated
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def patch(self, request, pk):
        try:
            user = User.objects.select_related(
                'admin_profile',
                'collaborator_profile',
                'client_profile'
            ).get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DeactivateUserSerializer(
            user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            try:
                updated_user = serializer.save()
                is_active = request.data.get('is_active')
                message = 'User activated successfully' if is_active else 'User deactivated successfully'
                
                return Response({
                    'message': message,
                    'user': UserListSerializer(updated_user).data
                }, status=status.HTTP_200_OK)
            except serializers.ValidationError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Service CRUD Views for Admin

class ServiceAdminListAPIView(generics.ListAPIView):
    """
    GET /api/admin/services/
    Get all services (admin only) - includes active and inactive with filtering
    
    Query parameters:
    - is_active: Filter by active status (true/false)
    - search: Search by name or description
    
    Examples:
    - GET /api/admin/services/ - Get all services
    - GET /api/admin/services/?is_active=true - Get only active services
    - GET /api/admin/services/?is_active=false - Get only inactive services
    - GET /api/admin/services/?search=web - Search services by name/description
    
    Response:
    [
        {
            "id": 1,
            "name": "Web Development",
            "description": "Professional web development services...",
            "tool_name": "React, Django",
            "is_active": true,
            "audio_file": "/media/services/audio/web-dev-intro.mp3",
            "templates_count": 3,
            "orders_count": 5,
            "reviews_count": 5,
            "average_rating": 4.8
        }
    ]
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ServiceAdminListSerializer
    
    def get_queryset(self):
        from django.db import models
        queryset = Service.objects.all().order_by('name')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Search by name or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | 
                models.Q(description__icontains=search)
            )
        
        return queryset


class ServiceCreateAPIView(generics.CreateAPIView):
    """
    POST /api/admin/services/
    Create a new service (admin only)
    
    Request body (multipart/form-data for file upload):
    {
        "name": "Mobile App Development",
        "description": "Professional mobile app development services...",
        "tool_name": "React Native, Flutter",
        "is_active": true,
        "audio_file": <audio_file>
    }
    
    Response:
    {
        "id": 3,
        "name": "Mobile App Development",
        "description": "Professional mobile app development services...",
        "tool_name": "React Native, Flutter",
        "is_active": true,
        "audio_file": "/media/services/audio/mobile-dev-intro.mp3"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ServiceCreateUpdateSerializer


class ServiceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/admin/services/{id}/
    PUT /api/admin/services/{id}/
    PATCH /api/admin/services/{id}/
    DELETE /api/admin/services/{id}/
    
    Retrieve, update, or delete a service (admin only)
    
    GET Response:
    {
        "id": 1,
        "name": "Web Development",
        "description": "Professional web development services...",
        "tool_name": "React, Django",
        "is_active": true,
        "audio_file": "/media/services/audio/web-dev-intro.mp3"
    }
    
    PUT/PATCH Request body (multipart/form-data for file upload):
    {
        "name": "Web Development Updated",
        "description": "Updated description...",
        "tool_name": "React, Django, PostgreSQL",
        "is_active": true,
        "audio_file": <new_audio_file>
    }
    
    DELETE Response:
    Success (200):
    {
        "message": "Service deleted successfully"
    }
    
    Error (400) - Service has associated orders:
    {
        "error": "Cannot delete service",
        "message": "This service cannot be deleted because it has 1 associated order(s). Please deactivate the service instead or delete the associated orders first.",
        "orders_count": 1
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ServiceCreateUpdateSerializer
    queryset = Service.objects.all()
    
    def destroy(self, request, *args, **kwargs):
        from django.db.models.deletion import ProtectedError
        
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {'message': 'Service deleted successfully'},
                status=status.HTTP_200_OK
            )
        except ProtectedError as e:
            # Get the count of related orders
            orders_count = instance.orders.count()
            return Response(
                {
                    'error': 'Cannot delete service',
                    'message': f'This service cannot be deleted because it has {orders_count} associated order(s). Please deactivate the service instead or delete the associated orders first.',
                    'orders_count': orders_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ServiceToggleActiveAPIView(APIView):
    """
    PATCH /api/admin/services/{id}/toggle-active/
    Toggle service active status (admin only)
    
    Request body:
    {
        "is_active": false
    }
    
    Response:
    {
        "message": "Service deactivated successfully",
        "service": {
            "id": 1,
            "name": "Web Development",
            "description": "Professional web development services...",
            "tool_name": "React, Django",
            "is_active": false,
            "audio_file": "/media/services/audio/web-dev-intro.mp3"
        }
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def patch(self, request, pk):
        try:
            service = Service.objects.get(pk=pk)
        except Service.DoesNotExist:
            return Response(
                {'error': 'Service not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ServiceToggleActiveSerializer(
            service, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            updated_service = serializer.save()
            is_active = request.data.get('is_active')
            message = 'Service activated successfully' if is_active else 'Service deactivated successfully'
            
            return Response({
                'message': message,
                'service': ServiceCreateUpdateSerializer(updated_service).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Template CRUD Views for Admin

class TemplateAdminListAPIView(generics.ListAPIView):
    """
    GET /api/admin/templates/
    Get all templates (admin only) with filtering
    
    Query parameters:
    - service_id: Filter by service ID
    - search: Search by title or description
    
    Examples:
    - GET /api/admin/templates/ - Get all templates
    - GET /api/admin/templates/?service_id=1 - Get templates for service ID 1
    - GET /api/admin/templates/?search=portfolio - Search templates by title/description
    
    Response:
    [
        {
            "id": 1,
            "service": 1,
            "service_name": "Web Development",
            "title": "E-commerce Website Template",
            "description": "Modern e-commerce template with shopping cart",
            "file": "/media/templates/files/ecommerce-template.zip",
            "demo_video": "/media/templates/demos/ecommerce-demo.mp4"
        }
    ]
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TemplateSerializer
    
    def get_queryset(self):
        from django.db import models
        queryset = Template.objects.select_related('service').all().order_by('service__name', 'title')
        
        # Filter by service_id
        service_id = self.request.query_params.get('service_id', None)
        if service_id:
            queryset = queryset.filter(service__id=service_id)
        
        # Search by title or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) | 
                models.Q(description__icontains=search)
            )
        
        return queryset


class TemplateCreateAPIView(generics.CreateAPIView):
    """
    POST /api/admin/templates/
    Create a new template (admin only)
    
    Request body (multipart/form-data for file upload):
    {
        "service": 1,
        "title": "Portfolio Website Template",
        "description": "Clean portfolio template for professionals",
        "file": <template_file>,
        "demo_video": <demo_video_file>
    }
    
    Response:
    {
        "id": 2,
        "service": 1,
        "service_name": "Web Development",
        "title": "Portfolio Website Template",
        "description": "Clean portfolio template for professionals",
        "file": "/media/templates/files/portfolio-template.zip",
        "demo_video": "/media/templates/demos/portfolio-demo.mp4"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TemplateCreateUpdateSerializer


class TemplateRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/admin/templates/{id}/
    PUT /api/admin/templates/{id}/
    PATCH /api/admin/templates/{id}/
    DELETE /api/admin/templates/{id}/
    
    Retrieve, update, or delete a template (admin only)
    
    GET Response:
    {
        "id": 1,
        "service": 1,
        "service_name": "Web Development",
        "title": "E-commerce Website Template",
        "description": "Modern e-commerce template with shopping cart",
        "file": "/media/templates/files/ecommerce-template.zip",
        "demo_video": "/media/templates/demos/ecommerce-demo.mp4"
    }
    
    PUT/PATCH Request body (multipart/form-data for file upload):
    {
        "service": 1,
        "title": "E-commerce Website Template Updated",
        "description": "Updated description...",
        "file": <new_template_file>,
        "demo_video": <new_demo_video_file>
    }
    
    DELETE Response:
    Success (200):
    {
        "message": "Template deleted successfully"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TemplateCreateUpdateSerializer
    queryset = Template.objects.select_related('service').all()
    
    def get_serializer_class(self):
        """Return different serializer for GET vs POST/PUT/PATCH"""
        if self.request.method == 'GET':
            return TemplateSerializer
        return TemplateCreateUpdateSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Template deleted successfully'},
            status=status.HTTP_200_OK
        )


# Order Management Views

class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/admin/orders/
    POST /api/admin/orders/
    
    List all orders or create a new order (admin only)
    
    GET Response:
    [
        {
            "id": 1,
            "client_id": 1,
            "client_name": "Youssef Tazi",
            "client_email": "client1@example.com",
            "client_phone": "+212600000004",
            "service_id": 1,
            "service_name": "Web Development",
            "status_id": 2,
            "status_name": "in_progress",
            "collaborator_name": "Ahmed Benali",
            "date": "2024-01-15T10:30:00Z",
            "deadline_date": "2024-02-15T10:30:00Z",
            "total_price": "1500.00",
            "advance_payment": "500.00",
            "remaining_payment": "1000.00",
            "is_fully_paid": false,
            "discount": "0.00",
            "quotation": "Custom website development...",
            "lecture": "Focus on responsive design...",
            "comment": "Client prefers modern design"
        }
    ]
    
    POST Request body:
    {
        "client": 1,
        "service": 1,
        "status": 2,
        "collaborator": 1,
        "deadline_date": "2024-02-15T10:30:00Z",
        "total_price": "1500.00",
        "advance_payment": "500.00",
        "discount": "0.00",
        "quotation": "Custom website development...",
        "lecture": "Focus on responsive design...",
        "comment": "Client prefers modern design"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.select_related(
        'client__user', 'service', 'status', 'collaborator__user'
    ).all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderListSerializer
        return OrderCreateUpdateSerializer
    
    def create(self, request, *args, **kwargs):
        """Create order and send email if collaborator is assigned"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Apply global commission settings if not explicitly set
        if not order.commission_type or not order.commission_value:
            order.apply_global_commission_settings()
            order.save()
        
        # Send email notification if collaborator is assigned
        email_sent = False
        if order.collaborator and order.collaborator.user.email:
            try:
                email_sent = EmailService.send_order_assignment_email(order, order.collaborator)
            except Exception as e:
                logging.error(f"Failed to send assignment email: {str(e)}")
        
        # Create notification for admin about new order
        from core.notification_service import NotificationService
        try:
            # Get all admin users
            from core.models import Admin
            admin_users = Admin.objects.select_related('user').all()
            for admin in admin_users:
                NotificationService.create_notification(
                    user=admin.user,
                    notification_type='order_assigned',
                    title=f'New Order Created - Order #{order.id}',
                    message=f'A new order has been created by {order.client.user.get_full_name() or order.client.user.username} for {order.service.name}',
                    priority='medium',
                    order=order
                )
        except Exception as e:
            logging.error(f"Failed to create admin notification for new order: {str(e)}")
        
        # Return order data with email status
        response_data = OrderListSerializer(order).data
        response_data['email_sent'] = email_sent
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class OrderRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/admin/orders/{id}/
    PUT /api/admin/orders/{id}/
    PATCH /api/admin/orders/{id}/
    DELETE /api/admin/orders/{id}/
    
    Retrieve, update, or delete an order (admin only)
    
    GET Response:
    {
        "id": 1,
        "client": 1,
        "client_name": "Youssef Tazi",
        "client_email": "client1@example.com",
        "client_phone": "+212600000004",
        "service": 1,
        "service_name": "Web Development",
        "status": 2,
        "status_name": "in_progress",
        "collaborator": 1,
        "collaborator_name": "Ahmed Benali",
        "date": "2024-01-15T10:30:00Z",
        "deadline_date": "2024-02-15T10:30:00Z",
        "total_price": "1500.00",
        "advance_payment": "500.00",
        "remaining_payment": "1000.00",
        "is_fully_paid": false,
        "discount": "0.00",
        "quotation": "Custom website development...",
        "lecture": "Focus on responsive design...",
        "comment": "Client prefers modern design",
        "livrables": []
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Order.objects.select_related(
        'client__user', 'service', 'status', 'collaborator__user'
    ).prefetch_related('livrables').all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return OrderDetailSerializer
        return OrderCreateUpdateSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Order deleted successfully'},
            status=status.HTTP_200_OK
        )


class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    """
    PATCH /api/admin/orders/{id}/status/
    PATCH /api/collaborator/orders/{id}/status/
    
    Update order status (admin and collaborator)
    
    Request body:
    {
        "status": 3
    }
    
    Response:
    {
        "id": 1,
        "status": 3,
        "status_name": "completed",
        "message": "Order status updated successfully"
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusUpdateSerializer
    queryset = Order.objects.select_related('status').all()
    
    def get_permissions(self):
        """
        Allow both admin and collaborator to update status
        """
        if hasattr(self.request.user, 'admin_profile'):
            return [IsAuthenticated()]
        elif hasattr(self.request.user, 'collaborator_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if collaborator can update this order
        if hasattr(request.user, 'collaborator_profile'):
            if not instance.collaborator or instance.collaborator.user != request.user:
                return Response(
                    {'error': 'You can only update status of orders assigned to you.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Store the old status to check if it's being changed to cancelled
        old_status = instance.status
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Check if status was changed to cancelled and send email notification
        email_sent = False
        if (old_status.name != instance.status.name and 
            instance.status.name.lower() == 'cancelled' and 
            instance.collaborator and 
            instance.collaborator.user.email):
            try:
                # Get cancellation reason from notes if available
                notes = request.data.get('notes', '')
                cancellation_reason = notes if notes else 'Order cancelled by admin/collaborator'
                
                email_sent = EmailService.send_order_cancellation_email(
                    instance, 
                    instance.collaborator, 
                    cancellation_reason
                )
            except Exception as e:
                logging.error(f"Failed to send cancellation email: {str(e)}")
        
        # Create notifications for status changes
        from core.notification_service import NotificationService
        try:
            # Notify admin if status changed to under_review
            if (old_status.name != instance.status.name and 
                instance.status.name.lower() == 'under_review'):
                from core.models import Admin
                admin_users = Admin.objects.select_related('user').all()
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin.user,
                        notification_type='order_status_changed',
                        title=f'Order Under Review - Order #{instance.id}',
                        message=f'Order #{instance.id} has been submitted for review by {instance.collaborator.user.get_full_name() or instance.collaborator.user.username if instance.collaborator else "Unknown"}',
                        priority='medium',
                        order=instance
                    )
            
            # Handle order cancellation notifications
            if (old_status.name != instance.status.name and 
                instance.status.name.lower() == 'cancelled'):
                
                # Get cancellation reason from notes if available
                notes = request.data.get('notes', '')
                cancellation_reason = notes if notes else 'Order cancelled'
                
                # Determine who cancelled the order
                cancelled_by = "Unknown"
                if hasattr(request.user, 'client_profile'):
                    cancelled_by = f"Client {instance.client.user.get_full_name() or instance.client.user.username}"
                elif hasattr(request.user, 'admin_profile'):
                    cancelled_by = f"Admin {request.user.get_full_name() or request.user.username}"
                elif hasattr(request.user, 'collaborator_profile'):
                    cancelled_by = f"Collaborator {request.user.get_full_name() or request.user.username}"
                
                # Notify all admins about cancellation
                from core.models import Admin
                admin_users = Admin.objects.select_related('user').all()
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin.user,
                        notification_type='order_cancelled',
                        title=f'Order Cancelled - Order #{instance.id}',
                        message=f'Order #{instance.id} has been cancelled by {cancelled_by}. Reason: {cancellation_reason}',
                        priority='high',
                        order=instance
                    )
                
                # Notify collaborator if assigned (and not the one who cancelled)
                if (instance.collaborator and 
                    not hasattr(request.user, 'collaborator_profile') or 
                    instance.collaborator.user != request.user):
                    NotificationService.create_notification(
                        user=instance.collaborator.user,
                        notification_type='order_cancelled',
                        title=f'Order Cancelled - Order #{instance.id}',
                        message=f'Order #{instance.id} has been cancelled by {cancelled_by}. Reason: {cancellation_reason}',
                        priority='high',
                        order=instance
                    )
                
                # Notify client if cancelled by admin or collaborator
                if (not hasattr(request.user, 'client_profile') and 
                    instance.client and instance.client.user):
                    NotificationService.create_notification(
                        user=instance.client.user,
                        notification_type='order_cancelled',
                        title=f'Order Cancelled - Order #{instance.id}',
                        message=f'Order #{instance.id} has been cancelled by {cancelled_by}. Reason: {cancellation_reason}',
                        priority='high',
                        order=instance
                    )
        except Exception as e:
            logging.error(f"Failed to create status change notifications: {str(e)}")
        
        return Response({
            'id': instance.id,
            'status': instance.status.id,
            'status_name': instance.status.name,
            'message': 'Order status updated successfully',
            'email_sent': email_sent
        })


class OrderCollaboratorAssignAPIView(generics.UpdateAPIView):
    """
    PATCH /api/admin/orders/{id}/assign-collaborator/
    
    Assign collaborator to order (admin only)
    
    Request body:
    {
        "collaborator": 1
    }
    
    Response:
    {
        "id": 1,
        "collaborator": 1,
        "collaborator_name": "Ahmed Benali",
        "message": "Collaborator assigned successfully"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = OrderCollaboratorAssignSerializer
    queryset = Order.objects.select_related('collaborator__user').all()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_collaborator = instance.collaborator
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Refresh instance to get updated collaborator
        instance.refresh_from_db()
        
        collaborator_name = "Unassigned"
        email_sent = False
        
        if instance.collaborator:
            collaborator_name = instance.collaborator.user.get_full_name() or instance.collaborator.user.username
            
            # Send email notification if collaborator was assigned and is different from before
            if instance.collaborator != old_collaborator and instance.collaborator.user.email:
                try:
                    email_sent = EmailService.send_order_assignment_email(instance, instance.collaborator)
                except Exception as e:
                    logging.error(f"Failed to send assignment email: {str(e)}")
            
            # Create notification for collaborator when order is assigned
            from core.notification_service import NotificationService
            try:
                if instance.collaborator != old_collaborator:
                    NotificationService.create_notification(
                        user=instance.collaborator.user,
                        notification_type='order_assigned',
                        title=f'New Order Assigned - Order #{instance.id}',
                        message=f'You have been assigned a new order #{instance.id} for {instance.service.name} by {instance.client.user.get_full_name() or instance.client.user.username}',
                        priority='medium',
                        order=instance
                    )
            except Exception as e:
                logging.error(f"Failed to create collaborator assignment notification: {str(e)}")
        
        return Response({
            'id': instance.id,
            'collaborator': instance.collaborator.user.id if instance.collaborator else None,
            'collaborator_name': collaborator_name,
            'message': 'Collaborator assigned successfully',
            'email_sent': email_sent
        })


class StatusListAPIView(generics.ListAPIView):
    """
    GET /api/admin/statuses/
    GET /api/collaborator/statuses/
    
    List all available statuses (admin and collaborator)
    
    Response:
    [
        {
            "id": 1,
            "name": "pending"
        },
        {
            "id": 2,
            "name": "in_progress"
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StatusSerializer
    queryset = Status.objects.all()
    
    def get_permissions(self):
        """
        Allow both admin and collaborator to access statuses
        """
        if hasattr(self.request.user, 'admin_profile'):
            return [IsAuthenticated()]
        elif hasattr(self.request.user, 'collaborator_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]


class CollaboratorStatusAPIView(generics.ListAPIView):
    """
    GET /api/collaborator/status/
    
    List only In Progress and Under Review statuses for collaborators
    
    Response:
    [
        {
            "id": 51,
            "name": "in_progress"
        },
        {
            "id": 52,
            "name": "under_review"
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StatusSerializer
    
    def get_queryset(self):
        """Return only In Progress and Under Review statuses"""
        return Status.objects.filter(
            name__in=['in_progress', 'under_review']
        )
    
    def get_permissions(self):
        """
        Allow only collaborators to access these specific statuses
        """
        if hasattr(self.request.user, 'collaborator_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]


class ActiveCollaboratorListAPIView(generics.ListAPIView):
    """
    GET /api/admin/active-collaborators/
    
    List all active collaborators for assignment (admin only)
    
    Response:
    [
        {
            "id": 1,
            "username": "collab1",
            "full_name": "Ahmed Benali",
            "email": "ahmed@example.com"
        }
    ]
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ActiveCollaboratorListSerializer
    queryset = Collaborator.objects.filter(is_active=True).select_related('user')


class CollaboratorOrderListAPIView(generics.ListAPIView):
    """
    GET /api/collaborator/orders/
    
    List orders assigned to the authenticated collaborator
    
    Response:
    [
        {
            "id": 1,
            "client_name": "Youssef Tazi",
            "service_name": "Web Development",
            "status_name": "in_progress",
            "date": "2024-01-15T10:30:00Z",
            "deadline_date": "2024-02-15T10:30:00Z",
            "total_price": "1500.00",
            "advance_payment": "500.00",
            "remaining_payment": "1000.00",
            "is_fully_paid": false,
            "has_livrable": true
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer
    
    def get_queryset(self):
        """Return orders assigned to the authenticated collaborator"""
        if hasattr(self.request.user, 'collaborator_profile'):
            return Order.objects.filter(
                collaborator__user=self.request.user
            ).select_related(
                'client__user', 'service', 'status', 'collaborator__user'
            ).prefetch_related('livrables').all()
        return Order.objects.none()
    
    def get_permissions(self):
        """
        Allow only collaborators to access their orders
        """
        if hasattr(self.request.user, 'collaborator_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]


class ClientOrderListAPIView(generics.ListAPIView):
    """
    GET /api/client/orders/
    
    List orders for the authenticated client
    
    Response:
    [
        {
            "id": 1,
            "client_name": "Youssef Tazi",
            "service_name": "Web Development",
            "status_name": "in_progress",
            "collaborator_name": "Ahmed Bennani",
            "date": "2024-01-15T10:30:00Z",
            "deadline_date": "2024-02-15T10:30:00Z",
            "total_price": "1500.00",
            "advance_payment": "500.00",
            "remaining_payment": "1000.00",
            "is_fully_paid": false,
            "discount": "0.00",
            "quotation": "Custom website development...",
            "lecture": "Focus on responsive design...",
            "comment": "Client prefers modern design",
            "livrables": [
                {
                    "id": 1,
                    "name": "Website Mockup",
                    "description": "Initial design mockup",
                    "is_accepted": false,
                    "reviews": []
                }
            ]
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    
    def get_queryset(self):
        """Return orders for the authenticated client"""
        if hasattr(self.request.user, 'client_profile'):
            return Order.objects.filter(
                client__user=self.request.user
            ).select_related(
                'client__user', 'service', 'status', 'collaborator__user'
            ).prefetch_related('livrables').all()
        return Order.objects.none()
    
    def get_permissions(self):
        """
        Allow only clients to access their orders
        """
        if hasattr(self.request.user, 'client_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]


class ClientOrderCancelAPIView(generics.UpdateAPIView):
    """
    PATCH /api/client/orders/{id}/cancel/
    
    Cancel an order (client only)
    
    Request body:
    {
        "cancellation_reason": "Changed requirements"
    }
    
    Response:
    {
        "id": 1,
        "status": 4,
        "status_name": "cancelled",
        "message": "Order cancelled successfully",
        "cancellation_reason": "Changed requirements"
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCancelSerializer
    queryset = Order.objects.select_related('status').all()
    
    def get_permissions(self):
        """
        Allow only clients to cancel their own orders
        """
        if hasattr(self.request.user, 'client_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]
    
    def get_queryset(self):
        """Return only orders belonging to the authenticated client"""
        if hasattr(self.request.user, 'client_profile'):
            return Order.objects.filter(
                client__user=self.request.user
            ).select_related('status')
        return Order.objects.none()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Get the cancellation reason
        cancellation_reason = request.data.get('cancellation_reason', '')
        
        # Get the "cancelled" status
        try:
            cancelled_status = Status.objects.get(name='cancelled')
        except Status.DoesNotExist:
            return Response(
                {'error': 'Cancelled status not found in system.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update the order status to cancelled
        instance.status = cancelled_status
        instance.save()
        
        # Create status history entry
        OrderStatusHistory.objects.create(
            order=instance,
            status=cancelled_status,
            changed_by=request.user,
            notes=f"Order cancelled by client. Reason: {cancellation_reason}" if cancellation_reason else "Order cancelled by client"
        )
        
        # Send email notification to collaborator if assigned
        email_sent = False
        if instance.collaborator and instance.collaborator.user.email:
            try:
                email_sent = EmailService.send_order_cancellation_email(
                    instance, 
                    instance.collaborator, 
                    cancellation_reason
                )
            except Exception as e:
                logging.error(f"Failed to send cancellation email: {str(e)}")
        
        # Create notifications for admin and collaborator
        from core.notification_service import NotificationService
        try:
            # Notify all admins about order cancellation
            from core.models import Admin
            admin_users = Admin.objects.select_related('user').all()
            for admin in admin_users:
                NotificationService.create_notification(
                    user=admin.user,
                    notification_type='order_cancelled',
                    title=f'Order Cancelled - Order #{instance.id}',
                    message=f'Order #{instance.id} has been cancelled by client {instance.client.user.get_full_name() or instance.client.user.username}. Reason: {cancellation_reason}' if cancellation_reason else f'Order #{instance.id} has been cancelled by client {instance.client.user.get_full_name() or instance.client.user.username}.',
                    priority='high',
                    order=instance
                )
            
            # Notify collaborator if assigned
            if instance.collaborator:
                NotificationService.create_notification(
                    user=instance.collaborator.user,
                    notification_type='order_cancelled',
                    title=f'Order Cancelled - Order #{instance.id}',
                    message=f'Order #{instance.id} has been cancelled by client {instance.client.user.get_full_name() or instance.client.user.username}. Reason: {cancellation_reason}' if cancellation_reason else f'Order #{instance.id} has been cancelled by client {instance.client.user.get_full_name() or instance.client.user.username}.',
                    priority='high',
                    order=instance
                )
        except Exception as e:
            logging.error(f"Failed to create cancellation notifications: {str(e)}")
        
        return Response({
            'id': instance.id,
            'status': instance.status.id,
            'status_name': instance.status.name,
            'message': 'Order cancelled successfully',
            'cancellation_reason': cancellation_reason,
            'email_sent': email_sent
        })


class ClientOrderCreateAPIView(generics.CreateAPIView):
    """
    POST /api/client/orders/create/
    
    Create a new order (client only)
    
    Request body:
    {
        "service": 1,
        "deadline_date": "2024-02-15T10:30:00Z",
        "budget": "1500.00",
        "project_description": "I need a modern website for my business with e-commerce functionality",
        "special_instructions": "Please use React and Node.js, and ensure mobile responsiveness"
    }
    
    Response:
    {
        "id": 1,
        "service": 1,
        "deadline_date": "2024-02-15T10:30:00Z",
        "total_price": "1500.00",
        "quotation": "I need a modern website for my business with e-commerce functionality",
        "lecture": "Please use React and Node.js, and ensure mobile responsiveness",
        "status": 1,
        "status_name": "pending",
        "message": "Order created successfully"
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ClientOrderCreateSerializer
    
    def get_permissions(self):
        """
        Allow only clients to create orders
        """
        if hasattr(self.request.user, 'client_profile'):
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        """Create order and send email notification to admin"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Send email notification to admin about new order
        email_sent = False
        try:
            # Get admin users to notify
            from core.models import Admin
            admin_users = Admin.objects.filter(user__is_active=True)
            
            for admin in admin_users:
                if admin.user.email:
                    email_sent = EmailService.send_new_order_notification_email(order, admin.user)
                    if email_sent:
                        break  # Send to first available admin
        except Exception as e:
            logging.error(f"Failed to send new order notification email: {str(e)}")
        
        return Response({
            'id': order.id,
            'service': order.service.id,
            'deadline_date': order.deadline_date,
            'total_price': str(order.total_price),
            'quotation': order.quotation,
            'lecture': order.lecture,
            'status': order.status.id,
            'status_name': order.status.name,
            'message': 'Order created successfully',
            'email_sent': email_sent
        }, status=status.HTTP_201_CREATED)


class OrderStatusHistoryAPIView(generics.ListAPIView):
    """
    GET /api/client/orders/{order_id}/status-history/
    
    Get status history for a specific order (client can only access their own orders)
    
    Response:
    [
        {
            "id": 1,
            "status_name": "pending",
            "changed_by_username": "admin",
            "changed_by_full_name": "Admin User",
            "changed_at": "2024-01-15T10:30:00Z",
            "notes": "Order created"
        },
        {
            "id": 2,
            "status_name": "in_progress",
            "changed_by_username": "collaborator1",
            "changed_by_full_name": "Ahmed Bennani",
            "changed_at": "2024-01-16T14:20:00Z",
            "notes": "Started working on the project"
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusHistorySerializer
    
    def get_queryset(self):
        """Return status history for the specified order if user has access"""
        order_id = self.kwargs.get('order_id')
        
        # Check if user is client and owns the order
        if hasattr(self.request.user, 'client_profile'):
            try:
                order = Order.objects.get(
                    id=order_id,
                    client__user=self.request.user
                )
                return OrderStatusHistory.objects.filter(order=order).select_related(
                    'status', 'changed_by'
                ).order_by('-changed_at')
            except Order.DoesNotExist:
                return OrderStatusHistory.objects.none()
        
        # Check if user is admin or collaborator assigned to the order
        elif (hasattr(self.request.user, 'admin_profile') or 
              hasattr(self.request.user, 'collaborator_profile')):
            try:
                if hasattr(self.request.user, 'admin_profile'):
                    # Admin can see any order
                    order = Order.objects.get(id=order_id)
                else:
                    # Collaborator can only see orders assigned to them
                    order = Order.objects.get(
                        id=order_id,
                        collaborator__user=self.request.user
                    )
                return OrderStatusHistory.objects.filter(order=order).select_related(
                    'status', 'changed_by'
                ).order_by('-changed_at')
            except Order.DoesNotExist:
                return OrderStatusHistory.objects.none()
        
        return OrderStatusHistory.objects.none()


class ClientStatisticsAPIView(APIView):
    """
    GET /api/client/statistics/
    
    Get global statistics for the authenticated client
    
    Response:
    {
        "total_orders": 5,
        "completed_orders": 3,
        "in_progress_orders": 1,
        "pending_orders": 1,
        "total_spent": "7500.00",
        "average_order_value": "1500.00",
        "total_livrables": 8,
        "accepted_livrables": 6,
        "pending_livrables": 2,
        "total_reviews_given": 3,
        "average_rating_given": 4.7,
        "services_used": [
            {
                "service_name": "Web Development",
                "orders_count": 2,
                "total_spent": "3000.00"
            }
        ],
        "recent_activity": [
            {
                "type": "order_created",
                "description": "New order for Web Development",
                "date": "2024-01-15T10:30:00Z"
            }
        ]
    }
    """
    permission_classes = [IsClientUser]
    
    def get(self, request):
        """Get statistics for the authenticated client"""
        if not hasattr(request.user, 'client_profile'):
            return Response({'error': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        client = request.user.client_profile
        
        # Get all orders for this client
        orders = Order.objects.filter(client=client)
        total_orders = orders.count()
        
        # Order status statistics
        completed_orders = orders.filter(status__name__icontains='completed').count()
        in_progress_orders = orders.filter(status__name__icontains='progress').count()
        pending_orders = orders.filter(status__name__icontains='pending').count()
        
        # Financial statistics
        total_spent = orders.aggregate(total=models.Sum('total_price'))['total'] or 0
        average_order_value = round(float(total_spent / total_orders), 2) if total_orders > 0 else 0
        
        # Livrables statistics
        livrables = Livrable.objects.filter(order__client=client)
        total_livrables = livrables.count()
        accepted_livrables = livrables.filter(is_accepted=True).count()
        pending_livrables = total_livrables - accepted_livrables
        
        # Reviews statistics
        reviews = Review.objects.filter(client=client)
        total_reviews_given = reviews.count()
        if total_reviews_given > 0:
            total_rating = sum([review.rating for review in reviews])
            average_rating_given = round(total_rating / total_reviews_given, 2)
        else:
            average_rating_given = 0
        
        # Services used statistics
        services_used = []
        for service in Service.objects.filter(orders__client=client).distinct():
            service_orders = orders.filter(service=service)
            service_spent = service_orders.aggregate(total=models.Sum('total_price'))['total'] or 0
            services_used.append({
                'service_name': service.name,
                'orders_count': service_orders.count(),
                'total_spent': str(service_spent)
            })
        
        # Recent activity (last 5 orders)
        recent_orders = orders.order_by('-date')[:5]
        recent_activity = []
        for order in recent_orders:
            recent_activity.append({
                'type': 'order_created',
                'description': f"New order for {order.service.name}",
                'date': order.date.isoformat()
            })
        
        return Response({
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'in_progress_orders': in_progress_orders,
            'pending_orders': pending_orders,
            'total_spent': str(total_spent),
            'average_order_value': str(average_order_value),
            'total_livrables': total_livrables,
            'accepted_livrables': accepted_livrables,
            'pending_livrables': pending_livrables,
            'total_reviews_given': total_reviews_given,
            'average_rating_given': average_rating_given,
            'services_used': services_used,
            'recent_activity': recent_activity
        })


class CollaboratorStatisticsAPIView(APIView):
    """
    GET /api/collaborator/statistics/
    
    Get global statistics for the authenticated collaborator
    
    Response:
    {
        "total_orders": 8,
        "completed_orders": 5,
        "in_progress_orders": 2,
        "under_review_orders": 1,
        "total_earnings": "12000.00",
        "average_order_value": "1500.00",
        "total_livrables": 12,
        "accepted_livrables": 10,
        "pending_livrables": 2,
        "total_reviews_received": 5,
        "average_rating_received": 4.8,
        "services_worked_on": [
            {
                "service_name": "Web Development",
                "orders_count": 3,
                "total_earnings": "4500.00"
            }
        ],
        "recent_activity": [
            {
                "type": "order_assigned",
                "description": "New order assigned for Web Development",
                "date": "2024-01-15T10:30:00Z"
            }
        ]
    }
    """
    permission_classes = [IsCollaboratorUser]
    
    def get(self, request):
        """Get statistics for the authenticated collaborator"""
        if not hasattr(request.user, 'collaborator_profile'):
            return Response({'error': 'Collaborator profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        collaborator = request.user.collaborator_profile
        
        # Get all orders assigned to this collaborator
        orders = Order.objects.filter(collaborator=collaborator)
        total_orders = orders.count()
        
        # Order status statistics
        completed_orders = orders.filter(status__name__icontains='completed').count()
        in_progress_orders = orders.filter(status__name__icontains='progress').count()
        under_review_orders = orders.filter(status__name__icontains='review').count()
        
        # Financial statistics (earnings from completed orders)
        completed_orders_queryset = orders.filter(status__name__icontains='completed')
        total_earnings = completed_orders_queryset.aggregate(total=models.Sum('total_price'))['total'] or 0
        average_order_value = round(float(total_earnings / completed_orders), 2) if completed_orders > 0 else 0
        
        # Livrables statistics
        livrables = Livrable.objects.filter(order__collaborator=collaborator)
        total_livrables = livrables.count()
        accepted_livrables = livrables.filter(is_accepted=True).count()
        pending_livrables = total_livrables - accepted_livrables
        
        # Reviews statistics (reviews received from clients)
        reviews = Review.objects.filter(order__collaborator=collaborator)
        total_reviews_received = reviews.count()
        if total_reviews_received > 0:
            total_rating = sum([review.rating for review in reviews])
            average_rating_received = round(total_rating / total_reviews_received, 2)
        else:
            average_rating_received = 0
        
        # Services worked on statistics
        services_worked_on = []
        for service in Service.objects.filter(orders__collaborator=collaborator).distinct():
            service_orders = orders.filter(service=service)
            service_earnings = service_orders.filter(status__name__icontains='completed').aggregate(
                total=models.Sum('total_price')
            )['total'] or 0
            services_worked_on.append({
                'service_name': service.name,
                'orders_count': service_orders.count(),
                'total_earnings': str(service_earnings)
            })
        
        # Recent activity (last 5 orders assigned)
        recent_orders = orders.order_by('-date')[:5]
        recent_activity = []
        for order in recent_orders:
            recent_activity.append({
                'type': 'order_assigned',
                'description': f"New order assigned for {order.service.name}",
                'date': order.date.isoformat()
            })
        
        return Response({
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'in_progress_orders': in_progress_orders,
            'under_review_orders': under_review_orders,
            'total_earnings': str(total_earnings),
            'average_order_value': str(average_order_value),
            'total_livrables': total_livrables,
            'accepted_livrables': accepted_livrables,
            'pending_livrables': pending_livrables,
            'total_reviews_received': total_reviews_received,
            'average_rating_received': average_rating_received,
            'services_worked_on': services_worked_on,
            'recent_activity': recent_activity
        })


# ==================== LIVRABLE ENDPOINTS ====================

class CollaboratorLivrableListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/collaborator/livrables/
    POST /api/collaborator/livrables/
    
    List and create livrables for the authenticated collaborator.
    When a collaborator submits a deliverable (POST), the order status is automatically changed to "under_review".
    """
    permission_classes = [IsCollaboratorUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LivrableListSerializer
        return LivrableCreateUpdateSerializer
    
    def get_queryset(self):
        """Return livrables for orders assigned to the authenticated collaborator"""
        return Livrable.objects.filter(
            order__collaborator__user=self.request.user
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()
    
    def create(self, request, *args, **kwargs):
        """Override create method to return proper 201 status and handle notifications"""
        try:
            # Validate the serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Get the order and validate collaborator assignment
            order = serializer.validated_data['order']
            
            # Double-check that the order is assigned to this collaborator
            if order.collaborator != self.request.user.collaborator_profile:
                return Response(
                    {'error': 'You can only create livrables for orders assigned to you.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Save the livrable first
            livrable = serializer.save()
            
            # Automatically change order status to "under_review" when collaborator submits a deliverable
            try:
                under_review_status = Status.objects.get(name='under_review')
                if order.status != under_review_status:
                    # Set attributes for signal handlers to track who made the change
                    order._changed_by_user = self.request.user
                    order._status_change_notes = f'Status changed automatically when collaborator submitted deliverable: {livrable.name}'
                    order.status = under_review_status
                    order.save()
            except Status.DoesNotExist:
                # If "under_review" status doesn't exist, create it
                under_review_status = Status.objects.create(name='under_review')
                order._changed_by_user = self.request.user
                order._status_change_notes = f'Status changed automatically when collaborator submitted deliverable: {livrable.name}'
                order.status = under_review_status
                order.save()
            
            # Send notifications to admin and client about new livrable
            from core.notification_service import NotificationService
            try:
                # Notify all admins about new livrable
                from core.models import Admin
                admin_users = Admin.objects.select_related('user').all()
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin.user,
                        notification_type='livrable_submitted',
                        title=f'New Deliverable Submitted - Order #{order.id}',
                        message=f'Collaborator {self.request.user.get_full_name() or self.request.user.username} has submitted a new deliverable "{livrable.name}" for Order #{order.id}',
                        priority='medium',
                        order=order,
                        livrable=livrable
                    )
                
                # Notify client about new livrable
                if order.client and order.client.user:
                    NotificationService.create_notification(
                        user=order.client.user,
                        notification_type='livrable_uploaded',
                        title=f'New Deliverable Available - Order #{order.id}',
                        message=f'A new deliverable "{livrable.name}" has been submitted for your Order #{order.id} and is ready for review',
                        priority='medium',
                        order=order,
                        livrable=livrable,
                        send_email=True  # ADD: Explicitly enable email sending
                    )
            except Exception as e:
                logging.error(f"Failed to create livrable notifications: {str(e)}")
            
            # Return success response with 201 status
            return Response({
                'message': 'Livrable created successfully',
                'livrable': serializer.data,
                'order_status': order.status.name,
                'notifications_sent': True
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logging.error(f"Error creating livrable: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Failed to create livrable: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CollaboratorLivrableRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/collaborator/livrables/{id}/
    PUT /api/collaborator/livrables/{id}/
    PATCH /api/collaborator/livrables/{id}/
    DELETE /api/collaborator/livrables/{id}/
    
    Retrieve, update, or delete a specific livrable (collaborator only)
    """
    permission_classes = [IsCollaboratorUser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LivrableDetailSerializer
        return LivrableCreateUpdateSerializer
    
    def get_queryset(self):
        """Return livrables for orders assigned to the authenticated collaborator"""
        return Livrable.objects.filter(
            order__collaborator__user=self.request.user
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()
    
    def perform_update(self, serializer):
        """Validate that the collaborator can update this livrable"""
        order = serializer.validated_data.get('order', self.get_object().order)
        
        # Check if order is assigned to this collaborator
        if order.collaborator != self.request.user.collaborator_profile:
            raise serializers.ValidationError('You can only update livrables for orders assigned to you.')
        
        serializer.save()


class AdminLivrableListAPIView(generics.ListAPIView):
    """
    GET /api/admin/livrables/
    
    List all livrables for admin review (admin only)
    """
    permission_classes = [IsAdminUser]
    serializer_class = LivrableListSerializer
    
    def get_queryset(self):
        """Return all livrables with under_review orders for admin review"""
        return Livrable.objects.filter(
            order__status__name='under_review'
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()


class AdminLivrableRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/admin/livrables/{id}/
    
    Retrieve a specific livrable for admin review (admin only)
    """
    permission_classes = [IsAdminUser]
    serializer_class = LivrableDetailSerializer
    
    def get_queryset(self):
        """Return livrables with under_review orders for admin review"""
        return Livrable.objects.filter(
            order__status__name='under_review'
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()


class AdminLivrableReviewAPIView(generics.UpdateAPIView):
    """
    PATCH /api/admin/livrables/{id}/review/
    
    Mark a livrable as reviewed by admin (admin only)
    """
    permission_classes = [IsAdminUser]
    serializer_class = LivrableAdminReviewSerializer
    
    def get_queryset(self):
        """Return livrables with under_review orders for admin review"""
        return Livrable.objects.filter(
            order__status__name='under_review'
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()
    
    def update(self, request, *args, **kwargs):
        """Update livrable review status and send email notification"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        is_reviewed = serializer.validated_data['is_reviewed_by_admin']
        
        # Save the livrable first
        livrable = serializer.save()
        
        email_sent = False
        if is_reviewed:
            # Send email notification to client when livrable is reviewed
            if livrable.order.client and livrable.order.client.user.email:
                try:
                    email_sent = EmailService.send_livrable_reviewed_email(
                        livrable, 
                        livrable.order.client
                    )
                except Exception as e:
                    logging.error(f"Failed to send livrable reviewed email: {str(e)}")
            
            # Create notification for client when livrable is reviewed by admin
            from core.notification_service import NotificationService
            try:
                NotificationService.create_notification(
                    user=livrable.order.client.user,
                    notification_type='livrable_reviewed',
                    title=f'Deliverable Reviewed - Order #{livrable.order.id}',
                    message=f'Your deliverable "{livrable.name}" has been reviewed by admin and is ready for your approval.',
                    priority='medium',
                    order=livrable.order,
                    livrable=livrable
                )
            except Exception as e:
                logging.error(f"Failed to create client notification for livrable review: {str(e)}")
        
        # Return response with email status
        response_data = serializer.data
        response_data['email_sent'] = email_sent
        response_data['message'] = 'Livrable review status updated successfully'
        
        return Response(response_data)


class AdminAllLivrableListAPIView(generics.ListAPIView):
    """
    GET /api/admin/livrables/all/
    
    List ALL livrables for admin (admin only)
    This endpoint returns all livrables regardless of order status
    """
    permission_classes = [IsAdminUser]
    serializer_class = LivrableListSerializer
    
    def get_queryset(self):
        """Return all livrables for admin review"""
        return Livrable.objects.select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all().order_by('-id')


class ClientLivrableListAPIView(generics.ListAPIView):
    """
    GET /api/client/livrables/
    
    List all livrables for the authenticated client's orders
    """
    permission_classes = [IsClientUser]
    serializer_class = LivrableDetailSerializer
    
    def get_queryset(self):
        """Return all livrables for the client's orders"""
        return Livrable.objects.filter(
            order__client__user=self.request.user
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()


class ClientLivrableAcceptRejectAPIView(generics.UpdateAPIView):
    """
    PATCH /api/client/livrables/{id}/accept-reject/
    
    Accept or reject a livrable (client only) - only works with reviewed livrables
    """
    permission_classes = [IsClientUser]
    serializer_class = LivrableAcceptRejectSerializer
    
    def get_queryset(self):
        """Return livrables for the client's completed orders that have been reviewed by admin"""
        return Livrable.objects.filter(
            order__client__user=self.request.user,
            order__status__name='under_review',
            is_reviewed_by_admin=True
        ).select_related(
            'order__client__user', 'order__service', 'order__status', 'order__collaborator__user'
        ).all()
    
    def perform_update(self, serializer):
        """Update the livrable acceptance status"""
        is_accepted = serializer.validated_data['is_accepted']
        
        # Save the livrable first
        livrable = serializer.save()
        
        # Create notifications for livrable acceptance/rejection
        from core.notification_service import NotificationService
        try:
            if is_accepted:
                # Notify collaborator when livrable is accepted
                if livrable.order.collaborator:
                    NotificationService.create_notification(
                        user=livrable.order.collaborator.user,
                        notification_type='livrable_accepted',
                        title=f'Deliverable Accepted - Order #{livrable.order.id}',
                        message=f'Your deliverable "{livrable.name}" has been accepted by {livrable.order.client.user.get_full_name() or livrable.order.client.user.username}',
                        priority='medium',
                        order=livrable.order,
                        livrable=livrable
                    )
            else:
                # Notify collaborator when livrable is rejected
                if livrable.order.collaborator:
                    NotificationService.create_notification(
                        user=livrable.order.collaborator.user,
                        notification_type='livrable_rejected',
                        title=f'Deliverable Rejected - Order #{livrable.order.id}',
                        message=f'Your deliverable "{livrable.name}" has been rejected by {livrable.order.client.user.get_full_name() or livrable.order.client.user.username}. Please review and resubmit.',
                        priority='high',
                        order=livrable.order,
                        livrable=livrable
                    )
        except Exception as e:
            logging.error(f"Failed to create livrable acceptance/rejection notifications: {str(e)}")
        
        if is_accepted:
            # Check if all livrables for this order are accepted
            order = livrable.order
            all_livrables = Livrable.objects.filter(order=order)
            all_accepted = all_livrables.filter(is_accepted=True).count() == all_livrables.count()
            
            # If all livrables are accepted, change order status to "completed"
            if all_accepted and all_livrables.count() > 0:
                try:
                    completed_status = Status.objects.get(name='completed')
                    order.status = completed_status
                    order.save()
                except Status.DoesNotExist:
                    # If "completed" status doesn't exist, create it
                    completed_status = Status.objects.create(name='completed')
                    order.status = completed_status
                    order.save()


# ==================== CLIENT REVIEW ENDPOINTS ====================

class ClientReviewListCreateAPIView(generics.ListCreateAPIView):
    """
    GET /api/client/reviews/
    POST /api/client/reviews/
    
    List and create reviews for the authenticated client
    """
    permission_classes = [IsClientUser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReviewSerializer
        return ReviewCreateUpdateSerializer
    
    def get_queryset(self):
        """Return reviews for the authenticated client"""
        return Review.objects.filter(
            client__user=self.request.user
        ).select_related(
            'order__service', 'order__client__user', 'order__status'
        ).all()
    
    def perform_create(self, serializer):
        """Set the client from the request"""
        serializer.save(client=self.request.user.client_profile)


class ClientReviewRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/client/reviews/{id}/
    PUT /api/client/reviews/{id}/
    PATCH /api/client/reviews/{id}/
    DELETE /api/client/reviews/{id}/
    
    Retrieve, update, or delete a specific review (client only)
    """
    permission_classes = [IsClientUser]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReviewSerializer
        return ReviewCreateUpdateSerializer
    
    def get_queryset(self):
        """Return reviews for the authenticated client"""
        return Review.objects.filter(
            client__user=self.request.user
        ).select_related(
            'order__service', 'order__client__user', 'order__status'
        ).all()
    
    def perform_update(self, serializer):
        """Validate that the review can be updated"""
        review = self.get_object()
        
        # Check if review can be updated (within 24 hours)
        if not review.can_be_updated():
            raise serializers.ValidationError(
                'You can only update your review within 24 hours of creating it.'
            )
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Validate that the review can be deleted"""
        # Check if review can be updated (within 24 hours)
        if not instance.can_be_updated():
            raise serializers.ValidationError(
                'You can only delete your review within 24 hours of creating it.'
            )
        
        instance.delete()


class LivrableFileDownloadAPIView(APIView):
    """
    GET /api/livrables/{id}/download/
    
    Download livrable file (accessible by collaborator, client, and admin)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Download the livrable file"""
        livrable = get_object_or_404(Livrable, pk=pk)
        
        # Check permissions
        user = request.user
        has_access = False
        
        if hasattr(user, 'collaborator_profile'):
            # Collaborator can access their own livrables
            has_access = livrable.order.collaborator == user.collaborator_profile
        elif hasattr(user, 'client_profile'):
            # Client can access livrables for their orders
            has_access = livrable.order.client == user.client_profile
        elif user.is_staff:
            # Admin can access all livrables
            has_access = True
        
        if not has_access:
            return Response(
                {'error': 'You do not have permission to access this file.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not livrable.file_path:
            return Response(
                {'error': 'No file attached to this livrable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            file_path = livrable.file_path.path
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'File not found on server.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{livrable.file_path.name}"'
                return response
                
        except Exception as e:
            return Response(
                {'error': 'Error reading file.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== PROFILE UPDATE ENDPOINT ====================

class ProfileUpdateAPIView(generics.UpdateAPIView):
    """
    PATCH /api/profile/update/
    
    Update user profile information (first_name, last_name, email, phone)
    
    Request body:
    {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john.doe@example.com",
        "phone": "+1234567890"
    }
    
    Response:
    {
        "message": "Profile updated successfully",
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "role": "client",
            "role_id": 1
        }
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileUpdateSerializer
    
    def get_object(self):
        """Return the authenticated user"""
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(updated_user).data
        }, status=status.HTTP_200_OK)


class AdminStatisticsAPIView(APIView):
    """
    GET /api/admin/statistics/
    
    Get comprehensive statistics for admin dashboard (admin only)
    
    Response:
    {
        "overview": {
            "total_users": 150,
            "total_clients": 120,
            "total_collaborators": 25,
            "total_orders": 300,
            "total_services": 15,
            "total_reviews": 85,
            "total_revenue": "125000.00"
        },
        "orders": {
            "total_orders": 300,
            "completed_orders": 180,
            "in_progress_orders": 45,
            "pending_orders": 30,
            "cancelled_orders": 15,
            "under_review_orders": 30,
            "average_order_value": "1250.00",
            "total_revenue": "125000.00",
            "pending_payments": "15000.00"
        },
        "users": {
            "new_users_this_month": 25,
            "active_clients": 95,
            "active_collaborators": 20,
            "inactive_collaborators": 5
        },
        "services": {
            "active_services": 12,
            "inactive_services": 3,
            "most_popular_service": {
                "name": "Web Development",
                "orders_count": 45,
                "revenue": "45000.00"
            },
            "services_performance": [
                {
                    "service_name": "Web Development",
                    "orders_count": 45,
                    "revenue": "45000.00",
                    "average_rating": 4.8
                }
            ]
        },
        "reviews": {
            "total_reviews": 85,
            "average_rating": 4.6,
            "rating_distribution": {
                "5": 50,
                "4": 25,
                "3": 7,
                "2": 2,
                "1": 1
            },
            "recent_reviews": 15
        },
        "collaborators": {
            "total_collaborators": 25,
            "active_collaborators": 20,
            "top_performers": [
                {
                    "collaborator_name": "John Doe",
                    "completed_orders": 15,
                    "total_earnings": "18000.00",
                    "average_rating": 4.9
                }
            ],
            "collaborator_earnings": "75000.00"
        },
        "recent_activity": [
            {
                "type": "order_created",
                "description": "New order for Web Development",
                "date": "2024-01-15T10:30:00Z",
                "user": "client1"
            }
        ],
        "financial": {
            "total_revenue": "125000.00",
            "completed_orders_revenue": "100000.00",
            "pending_payments": "15000.00",
            "average_order_value": "1250.00",
            "monthly_revenue": "25000.00"
        }
    }
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get comprehensive admin statistics"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        from django.db.models import Count, Sum, Avg, Q
        
        # Overview statistics
        total_users = User.objects.count()
        total_clients = User.objects.filter(client_profile__isnull=False).count()
        total_collaborators = User.objects.filter(collaborator_profile__isnull=False).count()
        total_orders = Order.objects.count()
        total_services = Service.objects.count()
        total_reviews = Review.objects.count()
        
        # Financial overview
        total_revenue = Order.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Order statistics
        orders = Order.objects.all()
        completed_orders = orders.filter(status__name__icontains='completed').count()
        in_progress_orders = orders.filter(status__name__icontains='progress').count()
        pending_orders = orders.filter(status__name__icontains='pending').count()
        cancelled_orders = orders.filter(status__name__icontains='cancelled').count()
        under_review_orders = orders.filter(status__name__icontains='review').count()
        
        # Financial calculations
        completed_orders_revenue = orders.filter(status__name__icontains='completed').aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        pending_payments = orders.exclude(status__name__icontains='completed').aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        average_order_value = round(float(total_revenue / total_orders), 2) if total_orders > 0 else 0
        
        # User statistics
        this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = User.objects.filter(date_joined__gte=this_month).count()
        active_clients = User.objects.filter(
            client_profile__isnull=False,
            client_profile__orders__isnull=False
        ).distinct().count()
        active_collaborators = User.objects.filter(
            collaborator_profile__isnull=False,
            collaborator_profile__is_active=True,
            collaborator_profile__orders__isnull=False
        ).distinct().count()
        inactive_collaborators = User.objects.filter(
            collaborator_profile__isnull=False,
            collaborator_profile__is_active=False
        ).count()
        
        # Service statistics
        active_services = Service.objects.filter(is_active=True).count()
        inactive_services = Service.objects.filter(is_active=False).count()
        
        # Most popular service
        popular_service = Service.objects.annotate(
            orders_count=Count('orders')
        ).order_by('-orders_count').first()
        
        most_popular_service = None
        if popular_service:
            service_revenue = Order.objects.filter(service=popular_service).aggregate(
                total=Sum('total_price')
            )['total'] or 0
            most_popular_service = {
                'name': popular_service.name,
                'orders_count': popular_service.orders_count,
                'revenue': str(service_revenue)
            }
        
        # Services performance
        services_performance = []
        for service in Service.objects.annotate(
            orders_count=Count('orders')
        ).filter(orders_count__gt=0).order_by('-orders_count')[:10]:
            service_revenue = Order.objects.filter(service=service).aggregate(
                total=Sum('total_price')
            )['total'] or 0
            
            # Calculate average rating for this service
            service_orders = Order.objects.filter(service=service)
            service_reviews = Review.objects.filter(order__in=service_orders)
            avg_rating = service_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            
            services_performance.append({
                'service_name': service.name,
                'orders_count': service.orders_count,
                'revenue': str(service_revenue),
                'average_rating': round(float(avg_rating), 2) if avg_rating else 0
            })
        
        # Review statistics
        reviews = Review.objects.all()
        if reviews.exists():
            average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
            rating_distribution = {
                '5': reviews.filter(rating=5).count(),
                '4': reviews.filter(rating=4).count(),
                '3': reviews.filter(rating=3).count(),
                '2': reviews.filter(rating=2).count(),
                '1': reviews.filter(rating=1).count(),
            }
        else:
            average_rating = 0
            rating_distribution = {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
        
        # Recent reviews (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews = Review.objects.filter(date__gte=thirty_days_ago).count()
        
        # Collaborator statistics
        collaborators = User.objects.filter(collaborator_profile__isnull=False)
        active_collaborators_count = collaborators.filter(collaborator_profile__is_active=True).count()
        
        # Top performers
        top_performers = []
        for collaborator in collaborators.filter(collaborator_profile__is_active=True):
            collaborator_orders = Order.objects.filter(collaborator=collaborator.collaborator_profile)
            completed_collaborator_orders = collaborator_orders.filter(status__name__icontains='completed')
            completed_count = completed_collaborator_orders.count()
            
            if completed_count > 0:
                total_earnings = completed_collaborator_orders.aggregate(
                    total=Sum('total_price')
                )['total'] or 0
                
                # Get average rating for this collaborator
                collaborator_reviews = Review.objects.filter(order__collaborator=collaborator.collaborator_profile)
                avg_rating = collaborator_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
                
                top_performers.append({
                    'collaborator_name': collaborator.get_full_name() or collaborator.username,
                    'completed_orders': completed_count,
                    'total_earnings': str(total_earnings),
                    'average_rating': round(float(avg_rating), 2) if avg_rating else 0
                })
        
        # Sort by completed orders and take top 5
        top_performers = sorted(top_performers, key=lambda x: x['completed_orders'], reverse=True)[:5]
        
        # Total collaborator earnings
        collaborator_earnings = Order.objects.filter(
            collaborator__isnull=False,
            status__name__icontains='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Recent activity (last 10 orders)
        recent_orders = Order.objects.select_related(
            'client__user', 'service', 'status'
        ).order_by('-date')[:10]
        
        recent_activity = []
        for order in recent_orders:
            recent_activity.append({
                'type': 'order_created',
                'description': f"New order for {order.service.name}",
                'date': order.date.isoformat(),
                'user': order.client.user.username
            })
        
        # Monthly revenue (current month)
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = Order.objects.filter(
            date__gte=current_month_start,
            status__name__icontains='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        return Response({
            'overview': {
                'total_users': total_users,
                'total_clients': total_clients,
                'total_collaborators': total_collaborators,
                'total_orders': total_orders,
                'total_services': total_services,
                'total_reviews': total_reviews,
                'total_revenue': str(total_revenue)
            },
            'orders': {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'in_progress_orders': in_progress_orders,
                'pending_orders': pending_orders,
                'cancelled_orders': cancelled_orders,
                'under_review_orders': under_review_orders,
                'average_order_value': str(average_order_value),
                'total_revenue': str(total_revenue),
                'pending_payments': str(pending_payments)
            },
            'users': {
                'new_users_this_month': new_users_this_month,
                'active_clients': active_clients,
                'active_collaborators': active_collaborators,
                'inactive_collaborators': inactive_collaborators
            },
            'services': {
                'active_services': active_services,
                'inactive_services': inactive_services,
                'most_popular_service': most_popular_service,
                'services_performance': services_performance
            },
            'reviews': {
                'total_reviews': total_reviews,
                'average_rating': round(float(average_rating), 2) if average_rating else 0,
                'rating_distribution': rating_distribution,
                'recent_reviews': recent_reviews
            },
            'collaborators': {
                'total_collaborators': total_collaborators,
                'active_collaborators': active_collaborators_count,
                'top_performers': top_performers,
                'collaborator_earnings': str(collaborator_earnings)
            },
            'recent_activity': recent_activity,
            'financial': {
                'total_revenue': str(total_revenue),
                'completed_orders_revenue': str(completed_orders_revenue),
                'pending_payments': str(pending_payments),
                'average_order_value': str(average_order_value),
                'monthly_revenue': str(monthly_revenue)
            }
        })


class TestEmailAPIView(APIView):
    """
    POST /api/admin/test-email/
    
    Send a test email to verify email configuration (admin only)
    
    Request body:
    {
        "email": "test@example.com",
        "subject": "Test Email",
        "message": "This is a test email"
    }
    
    Response:
    {
        "success": true,
        "message": "Test email sent successfully"
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        email = request.data.get('email')
        subject = request.data.get('subject', 'Test Email')
        message = request.data.get('message', 'This is a test email from Sademiy Order Management System')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            success = EmailService.send_test_email(email, subject, message)
            
            if success:
                return Response({
                    'success': True,
                    'message': 'Test email sent successfully'
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to send test email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error sending test email: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Global Settings Management Views

class GlobalSettingsRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
    GET /api/admin/global-settings/
    PUT /api/admin/global-settings/
    PATCH /api/admin/global-settings/
    
    Retrieve or update global settings (admin only)
    
    GET Response:
    {
        "id": 1,
        "commission_type": "percentage",
        "commission_value": "20.00",
        "is_commission_enabled": true,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "updated_by": null
    }
    
    PUT/PATCH Request body:
    {
        "commission_type": "percentage",
        "commission_value": "25.00",
        "is_commission_enabled": true
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = GlobalSettingsSerializer
    
    def get_object(self):
        """Get or create the global settings instance"""
        return GlobalSettings.get_settings()
    
    def update(self, request, *args, **kwargs):
        """Update global settings and track who made the change"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        
        # Set the user who updated the settings
        serializer.validated_data['updated_by'] = request.user
        
        self.perform_update(serializer)
        
        return Response(serializer.data)


# ==================== NOTIFICATION ENDPOINTS ====================

class NotificationListAPIView(generics.ListAPIView):
    """
    GET /api/notifications/
    
    List notifications for the authenticated user
    
    Query parameters:
    - unread_only: Filter only unread notifications (true/false)
    - notification_type: Filter by notification type
    - priority: Filter by priority level
    - limit: Limit number of results
    
    Response:
    [
        {
            "id": 1,
            "notification_type": "order_assigned",
            "title": "New Order Assignment - Order #123",
            "message": "You have been assigned to a new order...",
            "priority": "medium",
            "is_read": false,
            "is_email_sent": true,
            "created_at": "2024-01-15T10:30:00Z",
            "read_at": null,
            "order_id": 123,
            "order_title": "Web Development",
            "livrable_id": null,
            "livrable_name": null,
            "time_ago": "2 hours ago"
        }
    ]
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filter by unread only
        unread_only = self.request.query_params.get('unread_only', None)
        if unread_only is not None:
            unread_bool = unread_only.lower() == 'true'
            queryset = queryset.filter(is_read=not unread_bool)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('notification_type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Limit results
        limit = self.request.query_params.get('limit', None)
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        
        return queryset


class NotificationRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/notifications/{id}/
    
    Retrieve a specific notification
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadAPIView(generics.UpdateAPIView):
    """
    PATCH /api/notifications/{id}/mark-read/
    
    Mark a notification as read or unread
    
    Request body:
    {
        "is_read": true
    }
    
    Response:
    {
        "message": "Notification marked as read",
        "notification": {
            "id": 1,
            "is_read": true,
            "read_at": "2024-01-15T10:30:00Z"
        }
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Mark notification as read/unread"""
        notification = self.get_object()
        serializer = self.get_serializer(notification, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_notification = serializer.save()
        
        status = "read" if updated_notification.is_read else "unread"
        
        return Response({
            'message': f'Notification marked as {status}',
            'notification': {
                'id': updated_notification.id,
                'is_read': updated_notification.is_read,
                'read_at': updated_notification.read_at
            }
        })


class NotificationMarkAllReadAPIView(APIView):
    """
    POST /api/notifications/mark-all-read/
    
    Mark all notifications as read for the authenticated user
    
    Response:
    {
        "message": "All notifications marked as read",
        "updated_count": 5
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark all notifications as read"""
        from core.notification_service import NotificationService
        
        updated_count = NotificationService.mark_all_notifications_as_read(request.user)
        
        return Response({
            'message': 'All notifications marked as read',
            'updated_count': updated_count
        })


class NotificationStatsAPIView(APIView):
    """
    GET /api/notifications/stats/
    
    Get notification statistics for the authenticated user
    
    Response:
    {
        "total": 25,
        "unread": 5,
        "read": 20,
        "unread_by_type": {
            "order_assigned": 2,
            "order_status_changed": 1,
            "livrable_uploaded": 2
        },
        "recent_notifications": [
            {
                "id": 1,
                "notification_type": "order_assigned",
                "title": "New Order Assignment",
                "priority": "medium",
                "is_read": false,
                "created_at": "2024-01-15T10:30:00Z",
                "time_ago": "2 hours ago"
            }
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationStatsSerializer
    
    def get(self, request):
        """Get notification statistics"""
        from core.models import Notification
        from core.notification_service import NotificationService
        from django.db.models import Count
        
        # Get basic stats
        stats = NotificationService.get_notification_stats(request.user)
        
        # Get unread notifications by type
        unread_by_type = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).values('notification_type').annotate(
            count=Count('id')
        ).order_by('notification_type')
        
        unread_by_type_dict = {item['notification_type']: item['count'] for item in unread_by_type}
        
        # Get recent notifications (last 5)
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        recent_serializer = NotificationListSerializer(recent_notifications, many=True)
        
        return Response({
            'total': stats['total'],
            'unread': stats['unread'],
            'read': stats['read'],
            'unread_by_type': unread_by_type_dict,
            'recent_notifications': recent_serializer.data
        })


class NotificationDeleteAPIView(generics.DestroyAPIView):
    """
    DELETE /api/notifications/{id}/
    
    Delete a specific notification
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Delete notification"""
        notification = self.get_object()
        notification.delete()
        
        return Response({
            'message': 'Notification deleted successfully'
        }, status=status.HTTP_200_OK)


# Chatbot Workflow Views

class ChatbotLanguageListAPIView(generics.ListAPIView):
    """
    GET /api/chatbot/language/
    
    Get available languages for chatbot
    """
    permission_classes = [AllowAny]
    serializer_class = LanguageSerializer
    
    def get_queryset(self):
        """Return active languages"""
        return Language.objects.filter(is_active=True)


class ChatbotServiceListAPIView(generics.ListAPIView):
    """
    GET /api/services/
    
    Get all available services for chatbot
    """
    permission_classes = [AllowAny]
    serializer_class = ServiceListSerializer
    
    def get_queryset(self):
        """Return active services"""
        return Service.objects.filter(is_active=True)


class ChatbotServiceDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/services/{id}/
    
    Get service details with templates
    """
    permission_classes = [AllowAny]
    serializer_class = ServiceDetailSerializer
    queryset = Service.objects.filter(is_active=True)


class ChatbotTemplateListAPIView(generics.ListAPIView):
    """
    GET /api/templates/
    
    Get templates for a specific service
    """
    permission_classes = [AllowAny]
    serializer_class = TemplateSerializer
    
    def get_queryset(self):
        """Return templates for the specified service"""
        service_id = self.request.query_params.get('service_id')
        if service_id:
            return Template.objects.filter(service_id=service_id)
        return Template.objects.none()


class CollaboratorTemplateListAPIView(generics.ListAPIView):
    """
    GET /api/collaborator/templates/
    
    Get templates with files only (no videos) for collaborators
    Returns only templates that have files (not demo videos)
    
    Query parameters:
    - service_id: Filter by service ID (optional)
    
    Examples:
    - GET /api/collaborator/templates/ - Get all templates with files
    - GET /api/collaborator/templates/?service_id=1 - Get templates for service ID 1
    """
    permission_classes = [IsAuthenticated, IsCollaboratorUser]
    serializer_class = CollaboratorTemplateSerializer
    
    def get_queryset(self):
        """Return templates that have files (not null) and exclude demo_video"""
        queryset = Template.objects.filter(
            file__isnull=False
        ).exclude(
            file=''
        ).select_related('service').order_by('title')
        
        # Filter by service_id if provided
        service_id = self.request.query_params.get('service_id')
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        
        return queryset


class CollaboratorTemplateDownloadAPIView(APIView):
    """
    GET /api/collaborator/templates/{id}/download/
    
    Download template file (collaborator only)
    """
    permission_classes = [IsAuthenticated, IsCollaboratorUser]
    
    def get(self, request, pk):
        """Download the template file"""
        template = get_object_or_404(Template, pk=pk)
        
        # Check if template has a file
        if not template.file:
            return Response(
                {'error': 'No file available for this template.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            file_path = template.file.path
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'File not found on server.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{template.file.name}"'
                return response
                
        except Exception as e:
            logging.error(f"Error downloading template file: {str(e)}")
            return Response(
                {'error': 'Error reading file.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatbotSessionCreateAPIView(APIView):
    """
    POST /api/chatbot/session/

    Create a new chatbot session
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Create chatbot session"""
        try:
            import uuid
            
            # Get language ID from request
            language_id = request.data.get('language')
            if not language_id:
                return Response({
                    'error': 'Language ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate language exists
            try:
                language = Language.objects.get(id=language_id)
            except Language.DoesNotExist:
                return Response({
                    'error': 'Invalid language ID'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create session
            session_id = str(uuid.uuid4())
            session = ChatbotSession.objects.create(
                session_id=session_id,
                language=language  # This should work with the ForeignKey
            )
            
            return Response({
                'session_id': session.session_id,
                'message': 'Chatbot session created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create session: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatbotSessionUpdateAPIView(generics.UpdateAPIView):
    """
    PUT /api/chatbot/session/{session_id}/
    
    Update chatbot session
    """
    permission_classes = [AllowAny]
    serializer_class = ChatbotSessionUpdateSerializer
    lookup_field = 'session_id'
    
    def get_queryset(self):
        """Return session by session_id"""
        return ChatbotSession.objects.all()


class ChatbotClientRegistrationAPIView(APIView):
    """
    POST /api/chatbot/register/
    
    Register client through chatbot
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register client and update session"""
        serializer = ChatbotClientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data['session_id']
            name = serializer.validated_data['name']
            email = serializer.validated_data['email']
            phone = serializer.validated_data.get('phone', '')
            
            # Update session with client information
            session = ChatbotSession.objects.get(session_id=session_id)
            session.client_name = name
            session.client_email = email
            session.client_phone = phone
            session.save()
            
            return Response({
                'message': 'Client information saved successfully',
                'session_id': session_id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatbotOrderReviewAPIView(APIView):
    """
    GET /api/orders/review/
    
    Get order review for chatbot session
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get order review"""
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({
                'error': 'session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ChatbotOrderReviewSerializer(data={'session_id': session_id})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = ChatbotSession.objects.get(session_id=session_id)
            
            # Prepare order summary
            order_summary = {
                'session_id': session.session_id,
                'client_name': session.client_name,
                'client_email': session.client_email,
                'client_phone': session.client_phone,
                'service': {
                    'id': session.selected_service.id,
                    'name': session.selected_service.name,
                    'description': session.selected_service.description
                },
                'template': None,
                'custom_description': session.custom_description,
                'language': session.language.name if session.language else None
            }
            
            if session.selected_template:
                order_summary['template'] = {
                    'id': session.selected_template.id,
                    'title': session.selected_template.title,
                    'description': session.selected_template.description
                }
            
            return Response(order_summary, status=status.HTTP_200_OK)
            
        except ChatbotSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ChatbotOrderConfirmationAPIView(APIView):
    """
    POST /api/chatbot/confirm/
    
    Confirm and create order from chatbot session
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Confirm order and create client account"""
        serializer = ChatbotOrderConfirmationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        session_id = serializer.validated_data['session_id']
        confirm = serializer.validated_data['confirm']
        
        if not confirm:
            return Response({
                'message': 'Order confirmation cancelled'
            }, status=status.HTTP_200_OK)
        
        try:
            session = ChatbotSession.objects.get(session_id=session_id)
            
            # Create client user account
            import secrets
            import string
            
            # Generate username and password
            username = f"client_{session.client_email.split('@')[0]}_{secrets.token_hex(4)}"
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=session.client_email,
                password=password,
                first_name=session.client_name.split()[0] if session.client_name else '',
                last_name=' '.join(session.client_name.split()[1:]) if len(session.client_name.split()) > 1 else '',
                phone=session.client_phone
            )
            
            # Create client profile
            client = Client.objects.create(user=user)
            
            # Get pending status
            pending_status = Status.objects.get(name='Pending')
            
            # Create order
            from datetime import datetime, timedelta
            from decimal import Decimal
            deadline_date = datetime.now() + timedelta(days=7)
            
            order = Order.objects.create(
                client=client,
                service=session.selected_service,
                status=pending_status,
                deadline_date=deadline_date,
                total_price=Decimal('100.00'),  # Default price, should be calculated based on service
                advance_payment=Decimal('0.00'),
                description=session.custom_description or (session.selected_template.description if session.selected_template else ''),
                quotation='',
                discount=Decimal('0.00'),
                lecture='',
                comment='',
                sademy_commission_amount=Decimal('0.00'),
                commission_type='percentage',
                commission_value=Decimal('0.00'),
                is_blacklisted=False,
                blacklist_reason='',
                chatbot_session=session
            )
            
            # Create notification for admin about new chatbot order
            from core.notification_service import NotificationService
            try:
                # Get all admin users
                from core.models import Admin
                admin_users = Admin.objects.select_related('user').all()
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin.user,
                        notification_type='chatbot_order_created',
                        title=f'New Chatbot Order Created - Order #{order.id}',
                        message=f'A new order has been created via chatbot by {client.user.get_full_name() or client.user.username} for {order.service.name}',
                        priority='medium',
                        order=order
                    )
            except Exception as e:
                logging.error(f"Failed to create admin notification for chatbot order: {str(e)}")
            
            # Mark session as completed
            session.is_completed = True
            session.save()
            
            # Send credentials email
            try:
                from core.email_service import EmailService
                EmailService.send_client_credentials(user, password)
            except Exception as e:
                logging.error(f"Failed to send credentials email: {str(e)}")
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Order created successfully and client account registered',
                'order_id': order.id,
                'client_username': username,
                'client_password': password,
                'redirect_url': f'/client/dashboard/'  # Adjust based on your frontend routing
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ChatbotSession.DoesNotExist:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Status.DoesNotExist:
            return Response({
                'error': 'Pending status not found. Please contact administrator.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.error(f"Error creating order: {str(e)}")
            logging.error(f"Traceback: {error_details}")
            return Response({
                'error': f'Failed to create order: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== NOTIFICATION ENDPOINTS ====================

class NotificationListAPIView(generics.ListAPIView):
    """
    GET /api/notifications/
    
    List notifications for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationListSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class NotificationRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/notifications/{id}/
    
    Retrieve a specific notification
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkAsReadAPIView(generics.UpdateAPIView):
    """
    PATCH /api/notifications/{id}/mark-read/
    
    Mark a notification as read
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from core.models import Notification
        return Notification.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Mark notification as read"""
        from core.notification_service import NotificationService
        
        notification = self.get_object()
        updated_notification = NotificationService.mark_notification_as_read(notification.id, request.user)
        
        if updated_notification:
            serializer = self.get_serializer(updated_notification)
            return Response(serializer.data)
        else:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


class NotificationMarkAllAsReadAPIView(APIView):
    """
    POST /api/notifications/mark-all-read/
    
    Mark all notifications as read for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark all notifications as read"""
        from core.notification_service import NotificationService
        
        try:
            updated_count = NotificationService.mark_all_notifications_as_read(request.user)
            return Response({
                'message': f'{updated_count} notifications marked as read',
                'updated_count': updated_count
            })
        except Exception as e:
            return Response({
                'error': f'Failed to mark notifications as read: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationStatsAPIView(APIView):
    """
    GET /api/notifications/stats/
    
    Get notification statistics for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get notification statistics"""
        from core.notification_service import NotificationService
        from core.serializers import NotificationStatsSerializer
        
        try:
            stats = NotificationService.get_notification_stats(request.user)
            serializer = NotificationStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'error': f'Failed to get notification stats: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderCreateAPIView(APIView):
    """
    POST /api/orders/create/
    
    Public endpoint for creating orders with WhatsApp notifications
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Create order and send notifications"""
        from core.serializers import OrderCreateSerializer, OrderCreateResponseSerializer
        from core.whatsapp_service import WhatsAppService
        from core.sms_service import SMSService
        from core.email_service import EmailService
        from core.notification_service import NotificationService
        from core.models import Admin
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Validate input data
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create order
            order = serializer.save()
            
            # Initialize notification results
            notifications = {
                'email_sent': False,
                'sms_sent': False,
                'sms_message_id': None,
                'sms_error': None,
                'whatsapp_sent': False,
                'whatsapp_message_id': None,
                'whatsapp_error': None
            }
            
            # Send WhatsApp notification to client (disabled)
            # try:
            #     whatsapp_result = WhatsAppService.send_order_confirmation(order)
            #     notifications['whatsapp_sent'] = whatsapp_result.get('success', False)
            #     notifications['whatsapp_message_id'] = whatsapp_result.get('message_id')
            #     if not whatsapp_result.get('success'):
            #         notifications['whatsapp_error'] = whatsapp_result.get('error')
            # except Exception as e:
            #     logger.error(f"Failed to send WhatsApp notification: {str(e)}")
            #     notifications['whatsapp_error'] = str(e)
            
            # Send admin notifications
            try:
                # Create in-app notification for admins (without email)
                admin_users = Admin.objects.select_related('user').all()
                for admin in admin_users:
                    NotificationService.create_notification(
                        user=admin.user,
                        notification_type='order_assigned',
                        title=f'New Order Created - {order.order_number}',
                        message=f'A new order has been created by {order.client.user.get_full_name() or order.client.user.username} for {order.service.name}',
                        priority='medium',
                        order=order,
                        send_email=False  # Disable email for now
                    )
                
                # Send SMS to admin (disabled)
                # admin_sms_result = SMSService.send_admin_notification(order)
                # if admin_sms_result.get('success'):
                #     logger.info(f"Admin SMS notification sent for order {order.order_number}")
                #     notifications['sms_sent'] = True
                #     notifications['sms_message_id'] = admin_sms_result.get('message_id')
                # else:
                #     notifications['sms_error'] = admin_sms_result.get('error')
                
                # Send WhatsApp to admin (disabled)
                # if not admin_sms_result.get('success'):
                #     admin_whatsapp_result = WhatsAppService.send_admin_notification(order)
                #     if admin_whatsapp_result.get('success'):
                #         logger.info(f"Admin WhatsApp notification sent for order {order.order_number}")
                #         notifications['whatsapp_sent'] = True
                #         notifications['whatsapp_message_id'] = admin_whatsapp_result.get('message_id')
                #     else:
                #         notifications['whatsapp_error'] = admin_whatsapp_result.get('error')
                
            except Exception as e:
                logger.error(f"Failed to send admin notification: {str(e)}")
            
            # Prepare response data
            response_serializer = OrderCreateResponseSerializer(order)
            response_data = {
                'success': True,
                'message': 'Order created successfully',
                'data': response_serializer.data,
                'notifications': notifications
            }
            
            # System notifications are always created, so order is successful
            response_data['message'] = 'Order created successfully with system notifications'
            
            # Check if serializer created a new user (add this tracking in serializer)
            # For now, we'll check if user was created recently (within last minute)
            from django.utils import timezone
            from datetime import timedelta
            
            client_user = order.client.user
            recently_created = client_user.date_joined > timezone.now() - timedelta(minutes=1)
            
            # Send login credentials email if user was just created
            credentials_email_sent = False
            if recently_created:
                # Generate password for new user
                import secrets
                import string
                password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                
                # Set password
                client_user.set_password(password)
                client_user.save()
                
                # Send credentials email
                try:
                    from core.email_service import EmailService
                    credentials_email_sent = EmailService.send_client_credentials(client_user, password)
                    logger.info(f"Credentials email sent to {client_user.email}: {credentials_email_sent}")
                except Exception as e:
                    logger.error(f"Failed to send credentials email: {str(e)}")
            
            # Update response to include credentials email status
            response_data = {
                'success': True,
                'message': 'Order created successfully',
                'data': response_serializer.data,
                'notifications': notifications,
                'credentials_email_sent': credentials_email_sent  # Add this
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            return Response({
                'success': False,
                'message': 'Failed to create order',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)