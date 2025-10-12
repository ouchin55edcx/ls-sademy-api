"""
API Serializers
Place this file in: core/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from core.models import Service, Review, Livrable, Order, Client

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """
    Login with username/phone and password
    """
    username_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        username_or_phone = data.get('username_or_phone')
        password = data.get('password')

        if username_or_phone and password:
            # Try to authenticate with username first
            user = authenticate(username=username_or_phone, password=password)
            
            # If username authentication fails, try with phone
            if not user:
                try:
                    user_obj = User.objects.get(phone=username_or_phone)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if not user:
                raise serializers.ValidationError('Invalid credentials. Please check your username/phone and password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError('Must include "username_or_phone" and "password".')


class UserSerializer(serializers.ModelSerializer):
    """User serializer for login response with role information"""
    role = serializers.SerializerMethodField()
    role_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'role_id']
    
    def get_role(self, obj):
        """Get user role based on related models"""
        if hasattr(obj, 'admin_profile'):
            return 'admin'
        elif hasattr(obj, 'collaborator_profile'):
            return 'collaborator'
        elif hasattr(obj, 'client_profile'):
            return 'client'
        else:
            return 'user'
    
    def get_role_id(self, obj):
        """Get the ID of the role-specific profile"""
        if hasattr(obj, 'admin_profile'):
            return obj.admin_profile.pk
        elif hasattr(obj, 'collaborator_profile'):
            return obj.collaborator_profile.pk
        elif hasattr(obj, 'client_profile'):
            return obj.client_profile.pk
        else:
            return None


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer
    """
    livrable_name = serializers.CharField(source='livrable.name', read_only=True)
    order_id = serializers.IntegerField(source='livrable.order.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='livrable.order.service.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 
            'livrable', 
            'livrable_name',
            'order_id',
            'client_name',
            'service_name',
            'rating', 
            'comment', 
            'date'
        ]
        read_only_fields = ['date']
    
    def get_client_name(self, obj):
        return obj.livrable.order.client.user.get_full_name() or obj.livrable.order.client.user.username


class ServiceListSerializer(serializers.ModelSerializer):
    """
    Service list serializer (for listing all active services)
    """
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'price',
            'description',
            'is_active',
            'reviews_count',
            'average_rating'
        ]
    
    def get_reviews_count(self, obj):
        # Count reviews for all orders with this service
        return Review.objects.filter(
            livrable__order__service=obj
        ).count()
    
    def get_average_rating(self, obj):
        # Calculate average rating for this service
        reviews = Review.objects.filter(livrable__order__service=obj)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 2)
        return None


class LivrableSerializer(serializers.ModelSerializer):
    """Livrable serializer for service details"""
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta:
        model = Livrable
        fields = ['id', 'name', 'description', 'is_accepted', 'reviews']


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer for service details"""
    client_name = serializers.SerializerMethodField()
    livrables = LivrableSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'client_name',
            'date',
            'deadline_date',
            'status',
            'livrables'
        ]
    
    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.username


class ServiceDetailSerializer(serializers.ModelSerializer):
    """
    Service detail serializer (with related orders, livrables, and reviews)
    """
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    completed_orders = serializers.SerializerMethodField()
    sample_deliverables = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'price',
            'description',
            'is_active',
            'reviews_count',
            'average_rating',
            'recent_reviews',
            'total_orders',
            'completed_orders',
            'sample_deliverables'
        ]
    
    def get_reviews_count(self, obj):
        return Review.objects.filter(livrable__order__service=obj).count()
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(livrable__order__service=obj)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 2)
        return None
    
    def get_recent_reviews(self, obj):
        # Get last 5 reviews for this service
        reviews = Review.objects.filter(
            livrable__order__service=obj
        ).order_by('-date')[:5]
        return ReviewSerializer(reviews, many=True).data
    
    def get_total_orders(self, obj):
        return obj.orders.count()
    
    def get_completed_orders(self, obj):
        return obj.orders.filter(status__name='Completed').count()
    
    def get_sample_deliverables(self, obj):
        # Get sample livrables from completed orders
        livrables = Livrable.objects.filter(
            order__service=obj,
            order__status__name='Completed',
            is_accepted=True
        )[:3]
        return LivrableSerializer(livrables, many=True).data


class AllReviewsSerializer(serializers.ModelSerializer):
    """
    Serializer for all reviews listing
    """
    service_name = serializers.CharField(source='livrable.order.service.name', read_only=True)
    service_id = serializers.IntegerField(source='livrable.order.service.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    livrable_name = serializers.CharField(source='livrable.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'service_id',
            'service_name',
            'livrable_name',
            'client_name',
            'rating',
            'comment',
            'date'
        ]
    
    def get_client_name(self, obj):
        return obj.livrable.order.client.user.get_full_name() or obj.livrable.order.client.user.username