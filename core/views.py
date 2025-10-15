"""
API Views
Place this file in: core/views.py
"""

from rest_framework import status, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, get_user_model
from core.models import Service, Review, Template, Order, Status, Collaborator
from core.serializers import (
    LoginSerializer, UserSerializer, ServiceListSerializer,
    ServiceDetailSerializer, AllReviewsSerializer,
    UserListSerializer, CreateCollaboratorSerializer, DeactivateUserSerializer,
    ServiceCreateUpdateSerializer, ServiceAdminListSerializer, ServiceToggleActiveSerializer,
    TemplateSerializer, TemplateCreateUpdateSerializer,
    OrderListSerializer, OrderCreateUpdateSerializer, OrderDetailSerializer,
    OrderStatusUpdateSerializer, OrderCollaboratorAssignSerializer,
    StatusSerializer, ActiveCollaboratorListSerializer
)
from core.permissions import IsAdminUser

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
            'livrable__order__service',
            'livrable__order__client__user'
        ).all()
        
        # Filter by service_id if provided
        service_id = self.request.query_params.get('service_id', None)
        if service_id:
            queryset = queryset.filter(livrable__order__service__id=service_id)
        
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
        reviews = Review.objects.all()
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
            orders__livrables__reviews__isnull=False
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
            "status_name": "In Progress",
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
        "status_name": "In Progress",
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
        "status_name": "Completed",
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
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        collaborator_name = "Unassigned"
        if instance.collaborator:
            collaborator_name = instance.collaborator.user.get_full_name() or instance.collaborator.user.username
        
        return Response({
            'id': instance.id,
            'collaborator': instance.collaborator.user.id if instance.collaborator else None,
            'collaborator_name': collaborator_name,
            'message': 'Collaborator assigned successfully'
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
            "name": "Pending"
        },
        {
            "id": 2,
            "name": "In Progress"
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
            "status_name": "In Progress",
            "date": "2024-01-15T10:30:00Z",
            "deadline_date": "2024-02-15T10:30:00Z",
            "total_price": "1500.00",
            "advance_payment": "500.00",
            "remaining_payment": "1000.00",
            "is_fully_paid": false
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
            ).all()
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
            "status_name": "In Progress",
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