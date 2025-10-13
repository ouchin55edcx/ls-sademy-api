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
from core.models import Service, Review
from core.serializers import (
    LoginSerializer, UserSerializer, ServiceListSerializer,
    ServiceDetailSerializer, AllReviewsSerializer,
    UserListSerializer, CreateCollaboratorSerializer, DeactivateUserSerializer
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