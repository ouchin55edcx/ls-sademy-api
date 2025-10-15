"""
API Serializers
Place this file in: core/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from core.models import Service, Review, Livrable, Order, Client, Template, Collaborator, Admin, Status

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


class TemplateSerializer(serializers.ModelSerializer):
    """
    Template serializer for displaying service templates
    """
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Template
        fields = ['id', 'service', 'service_name', 'title', 'description', 'file', 'demo_video']


class TemplateCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Template serializer for creating and updating templates (admin only)
    """
    class Meta:
        model = Template
        fields = ['service', 'title', 'description', 'file', 'demo_video']
    
    def validate_service(self, value):
        """Validate that the service exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError('Cannot create template for inactive service.')
        return value
    
    def validate_title(self, value):
        """Check if template title already exists for the same service"""
        service = self.initial_data.get('service')
        if service and self.instance is None:  # Creating new template
            if Template.objects.filter(service=service, title=value).exists():
                raise serializers.ValidationError('Template with this title already exists for this service.')
        return value


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
    templates_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'tool_name',
            'is_active',
            'audio_file',
            'templates_count',
            'reviews_count',
            'average_rating'
        ]
    
    def get_templates_count(self, obj):
        return obj.templates.count()
    
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
    Service detail serializer (with related templates and reviews)
    Public endpoint for visitors
    """
    templates = TemplateSerializer(many=True, read_only=True)
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'tool_name',
            'is_active',
            'audio_file',
            'templates',
            'reviews_count',
            'average_rating',
            'recent_reviews'
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


# Admin User Management Serializers

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing all users (admin only)
    """
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_active_collab = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name',
            'full_name',
            'phone', 
            'role',
            'is_active',
            'is_active_collab',
            'date_joined',
            'last_login'
        ]
    
    def get_role(self, obj):
        """Get user role"""
        if hasattr(obj, 'admin_profile'):
            return 'admin'
        elif hasattr(obj, 'collaborator_profile'):
            return 'collaborator'
        elif hasattr(obj, 'client_profile'):
            return 'client'
        else:
            return 'user'
    
    def get_full_name(self, obj):
        """Get full name or username"""
        return obj.get_full_name() or obj.username
    
    def get_is_active_collab(self, obj):
        """Get collaborator active status (only for collaborators)"""
        if hasattr(obj, 'collaborator_profile'):
            return obj.collaborator_profile.is_active
        return None


class CreateCollaboratorSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new collaborators (admin only)
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'password',
            'confirm_password'
        ]
    
    def validate(self, data):
        """Validate password confirmation"""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        return data
    
    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists.')
        return value
    
    def validate_phone(self, value):
        """Check if phone already exists (if provided)"""
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('Phone number already exists.')
        return value
    
    def create(self, validated_data):
        """Create user and collaborator profile"""
        # Remove confirm_password as it's not needed for user creation
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create collaborator profile
        Collaborator.objects.create(user=user, is_active=True)
        
        return user


class DeactivateUserSerializer(serializers.Serializer):
    """
    Serializer for deactivating/activating a user (admin only)
    """
    is_active = serializers.BooleanField()
    
    def create(self, validated_data):
        """Not used for this serializer"""
        pass
    
    def update(self, instance, validated_data):
        """Update user active status"""
        is_active = validated_data.get('is_active')
        
        # Prevent deactivating admin users
        if hasattr(instance, 'admin_profile'):
            raise serializers.ValidationError('Cannot deactivate admin users.')
        
        # Update user.is_active
        instance.is_active = is_active
        instance.save()
        
        # If it's a collaborator, also update collaborator.is_active
        if hasattr(instance, 'collaborator_profile'):
            instance.collaborator_profile.is_active = is_active
            instance.collaborator_profile.save()
        
        return instance


# Service CRUD Serializers for Admin

class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating services (admin only)
    """
    class Meta:
        model = Service
        fields = [
            'name',
            'description',
            'tool_name',
            'is_active',
            'audio_file'
        ]
    
    def validate_name(self, value):
        """Check if service name already exists (for create operations)"""
        if self.instance is None:  # Creating new service
            if Service.objects.filter(name=value).exists():
                raise serializers.ValidationError('Service with this name already exists.')
        return value


class ServiceAdminListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing all services (admin only) - includes active and inactive
    """
    templates_count = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'tool_name',
            'is_active',
            'audio_file',
            'templates_count',
            'orders_count',
            'reviews_count',
            'average_rating'
        ]
    
    def get_templates_count(self, obj):
        return obj.templates.count()
    
    def get_orders_count(self, obj):
        return obj.orders.count()
    
    def get_reviews_count(self, obj):
        return Review.objects.filter(livrable__order__service=obj).count()
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(livrable__order__service=obj)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 2)
        return None


class ServiceToggleActiveSerializer(serializers.ModelSerializer):
    """
    Serializer for toggling service active status (admin only)
    """
    class Meta:
        model = Service
        fields = ['is_active']


# Order CRUD Serializers for Admin

class StatusSerializer(serializers.ModelSerializer):
    """
    Simple status serializer
    """
    class Meta:
        model = Status
        fields = ['id', 'name']


class CollaboratorSerializer(serializers.ModelSerializer):
    """
    Simple collaborator serializer
    """
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Collaborator
        fields = ['id', 'username', 'full_name', 'is_active']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class OrderListSerializer(serializers.ModelSerializer):
    """
    Order list serializer for admin (with all details)
    """
    client_name = serializers.SerializerMethodField()
    client_email = serializers.CharField(source='client.user.email', read_only=True)
    client_phone = serializers.CharField(source='client.user.phone', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    collaborator_name = serializers.SerializerMethodField()
    remaining_payment = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'client_name',
            'client_email', 
            'client_phone',
            'service_name',
            'status_name',
            'collaborator_name',
            'date',
            'deadline_date',
            'total_price',
            'advance_payment',
            'remaining_payment',
            'is_fully_paid',
            'discount',
            'quotation',
            'lecture',
            'comment'
        ]
    
    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.collaborator:
            return obj.collaborator.user.get_full_name() or obj.collaborator.user.username
        return "Unassigned"


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Order create/update serializer for admin
    """
    class Meta:
        model = Order
        fields = [
            'client',
            'service', 
            'status',
            'collaborator',
            'deadline_date',
            'total_price',
            'advance_payment',
            'discount',
            'quotation',
            'lecture',
            'comment'
        ]
    
    def validate_client(self, value):
        """Validate that client exists"""
        if not value:
            raise serializers.ValidationError('Client is required.')
        return value
    
    def validate_service(self, value):
        """Validate that service exists and is active"""
        if not value:
            raise serializers.ValidationError('Service is required.')
        if not value.is_active:
            raise serializers.ValidationError('Cannot create order for inactive service.')
        return value
    
    def validate_status(self, value):
        """Validate that status exists"""
        if not value:
            raise serializers.ValidationError('Status is required.')
        return value
    
    def validate_collaborator(self, value):
        """Validate that collaborator is active (if provided)"""
        if value and not value.is_active:
            raise serializers.ValidationError('Cannot assign order to inactive collaborator.')
        return value
    
    def validate_total_price(self, value):
        """Validate total price"""
        if value <= 0:
            raise serializers.ValidationError('Total price must be greater than 0.')
        return value
    
    def validate_advance_payment(self, value):
        """Validate advance payment"""
        if value < 0:
            raise serializers.ValidationError('Advance payment cannot be negative.')
        return value
    
    def validate_discount(self, value):
        """Validate discount"""
        if value < 0:
            raise serializers.ValidationError('Discount cannot be negative.')
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        advance_payment = data.get('advance_payment', 0)
        total_price = data.get('total_price')
        
        if advance_payment > total_price:
            raise serializers.ValidationError({
                'advance_payment': 'Advance payment cannot be greater than total price.'
            })
        
        return data


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Order detail serializer with related data
    """
    client_name = serializers.SerializerMethodField()
    client_email = serializers.CharField(source='client.user.email', read_only=True)
    client_phone = serializers.CharField(source='client.user.phone', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    collaborator_name = serializers.SerializerMethodField()
    remaining_payment = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()
    livrables = LivrableSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'client',
            'client_name',
            'client_email',
            'client_phone',
            'service',
            'service_name',
            'status',
            'status_name',
            'collaborator',
            'collaborator_name',
            'date',
            'deadline_date',
            'total_price',
            'advance_payment',
            'remaining_payment',
            'is_fully_paid',
            'discount',
            'quotation',
            'lecture',
            'comment',
            'livrables'
        ]
    
    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.collaborator:
            return obj.collaborator.user.get_full_name() or obj.collaborator.user.username
        return "Unassigned"


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order status (admin and collaborator)
    """
    class Meta:
        model = Order
        fields = ['status']
    
    def validate_status(self, value):
        """Validate that status exists"""
        if not value:
            raise serializers.ValidationError('Status is required.')
        return value


class OrderCollaboratorAssignSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning collaborator to order (admin only)
    """
    class Meta:
        model = Order
        fields = ['collaborator']
    
    def validate_collaborator(self, value):
        """Validate that collaborator is active"""
        if value and not value.is_active:
            raise serializers.ValidationError('Cannot assign order to inactive collaborator.')
        return value


class ActiveCollaboratorListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing active collaborators (for assignment dropdown)
    """
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Collaborator
        fields = ['user', 'username', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username