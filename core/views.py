"""
API Views
Place this file in: core/views.py
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login
from core.models import Service, Review
from core.serializers import (
    LoginSerializer, UserSerializer, ServiceListSerializer,
    ServiceDetailSerializer, AllReviewsSerializer
)


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
            "phone": "+212600000004"
        }
    }
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
    Get all active services with reviews count and average rating
    
    Response:
    [
        {
            "id": 1,
            "name": "Web Development",
            "price": "5000.00",
            "description": "Professional web development services...",
            "is_active": true,
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
    Get service details by ID with related reviews, orders, and deliverables
    
    Response:
    {
        "id": 1,
        "name": "Web Development",
        "price": "5000.00",
        "description": "Professional web development services...",
        "is_active": true,
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
        ],
        "total_orders": 10,
        "completed_orders": 8,
        "sample_deliverables": [
            {
                "id": 1,
                "name": "E-commerce Website Final Delivery",
                "description": "Complete website with all features",
                "is_accepted": true,
                "reviews": [...]
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