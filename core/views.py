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
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
import os
from core.models import Service, Review, Template, Order, Status, Collaborator, Livrable, OrderStatusHistory
from core.serializers import (
    LoginSerializer, UserSerializer, ServiceListSerializer,
    ServiceDetailSerializer, AllReviewsSerializer, ReviewSerializer, ReviewCreateUpdateSerializer,
    UserListSerializer, CreateCollaboratorSerializer, DeactivateUserSerializer,
    ServiceCreateUpdateSerializer, ServiceAdminListSerializer, ServiceToggleActiveSerializer,
    TemplateSerializer, TemplateCreateUpdateSerializer,
    OrderListSerializer, OrderCreateUpdateSerializer, OrderDetailSerializer,
    OrderStatusUpdateSerializer, OrderCancelSerializer, OrderCollaboratorAssignSerializer,
    StatusSerializer, ActiveCollaboratorListSerializer, OrderStatusHistorySerializer,
    LivrableCreateUpdateSerializer, LivrableListSerializer, LivrableDetailSerializer,
    LivrableAcceptRejectSerializer, LivrableAdminReviewSerializer, ProfileUpdateSerializer
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
    
    Examples:
    - GET /api/admin/users/ - Get all users
    - GET /api/admin/users/?role=collaborator - Get all collaborators
    - GET /api/admin/users/?role=client - Get all clients
    
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
        
        return queryset


class CreateCollaboratorAPIView(generics.CreateAPIView):
    """
    POST /api/admin/collaborators/
    Create a new collaborator (admin only)
    
    Request body:
    {
        "username": "new_collab",
        "email": "newcollab@sademiy.com",
        "first_name": "Hassan",
        "last_name": "Alami",
        "phone": "+212600000010",
        "password": "securePassword123",
        "confirm_password": "securePassword123"
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
        "role_id": 5
    }
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = CreateCollaboratorSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return user data with role information
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


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
            "client_name": "Youssef Tazi",
            "client_email": "client1@example.com",
            "client_phone": "+212600000004",
            "service_name": "Web Development",
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
        
        # Send email notification if collaborator is assigned
        email_sent = False
        if order.collaborator and order.collaborator.user.email:
            try:
                email_sent = EmailService.send_order_assignment_email(order, order.collaborator)
            except Exception as e:
                logging.error(f"Failed to send assignment email: {str(e)}")
        
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
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'id': instance.id,
            'status': instance.status.id,
            'status_name': instance.status.name,
            'message': 'Order status updated successfully'
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
        
        return Response({
            'id': instance.id,
            'status': instance.status.id,
            'status_name': instance.status.name,
            'message': 'Order cancelled successfully',
            'cancellation_reason': cancellation_reason
        })


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
    
    List and create livrables for the authenticated collaborator
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
    
    def perform_create(self, serializer):
        """Set the order and validate collaborator assignment"""
        order = serializer.validated_data['order']
        
        # Double-check that the order is assigned to this collaborator
        if order.collaborator != self.request.user.collaborator_profile:
            raise serializers.ValidationError('You can only create livrables for orders assigned to you.')
        
        serializer.save()


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
    
    def perform_update(self, serializer):
        """Update the livrable review status"""
        is_reviewed = serializer.validated_data['is_reviewed_by_admin']
        
        if is_reviewed:
            # If marking as reviewed, we could trigger additional actions here
            # like sending notifications to the client, etc.
            pass
        
        serializer.save()


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