"""
API Serializers
Place this file in: core/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from core.models import (
    Service,
    Review,
    Livrable,
    Order,
    Client,
    Template,
    Collaborator,
    Admin,
    Status,
    OrderStatusHistory,
    GlobalSettings,
    Notification,
    Language,
    ChatbotSession,
    ServiceCollaboratorCommission,
)

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
            
            # Check if client is blacklisted
            if hasattr(user, 'client_profile') and user.client_profile.is_blacklisted:
                # Find the blacklist reason from any blacklisted order
                blacklisted_order = Order.objects.filter(
                    client=user.client_profile,
                    is_blacklisted=True
                ).first()
                
                reason = blacklisted_order.blacklist_reason if blacklisted_order else "No reason provided"
                raise serializers.ValidationError(f'Your account has been blacklisted. Reason: {reason}')
            
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


class CollaboratorTemplateSerializer(serializers.ModelSerializer):
    """
    Template serializer for collaborators - only title, file, and service_id
    """
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    
    class Meta:
        model = Template
        fields = ['id', 'title', 'file', 'service_id']


class ReviewSerializer(serializers.ModelSerializer):
    """
    Review serializer for displaying reviews
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='order.service.name', read_only=True)
    can_be_updated = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 
            'order', 
            'order_id',
            'client_name',
            'service_name',
            'rating', 
            'comment', 
            'date',
            'updated_at',
            'can_be_updated'
        ]
        read_only_fields = ['date', 'updated_at', 'can_be_updated']
    
    def get_client_name(self, obj):
        if obj.client and obj.client.user:
            return obj.client.user.get_full_name() or obj.client.user.username
        return "Unknown Client"
    
    def get_can_be_updated(self, obj):
        return obj.can_be_updated()


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating reviews (client only)
    """
    class Meta:
        model = Review
        fields = ['order', 'rating', 'comment']
    
    def validate_order(self, value):
        """Validate that the order exists and belongs to the client"""
        if not value:
            raise serializers.ValidationError('Order is required.')
        
        # Check if order belongs to the current client
        request = self.context.get('request')
        if request and hasattr(request.user, 'client_profile'):
            if value.client != request.user.client_profile:
                raise serializers.ValidationError('You can only review your own orders.')
        
        # Check if order is completed and accepted
        if value.status.name != 'Completed':
            raise serializers.ValidationError('You can only review completed orders.')
        
        # Check if order has been reviewed by admin and accepted by client
        livrables = value.livrables.all()
        if not livrables.exists():
            raise serializers.ValidationError('Order has no livrables to review.')
        
        # Check if at least one livrable is reviewed by admin and accepted by client
        has_reviewed_and_accepted = any(
            livrable.is_reviewed_by_admin and livrable.is_accepted 
            for livrable in livrables
        )
        
        if not has_reviewed_and_accepted:
            raise serializers.ValidationError(
                'You can only review orders that have been reviewed by admin and accepted by you.'
            )
        
        return value
    
    def validate_rating(self, value):
        """Validate rating"""
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        order = data.get('order')
        request = self.context.get('request')
        
        if order and request and hasattr(request.user, 'client_profile'):
            # Check if review already exists for this order
            existing_review = Review.objects.filter(
                order=order,
                client=request.user.client_profile
            ).first()
            
            if existing_review and not self.instance:
                raise serializers.ValidationError(
                    'You have already reviewed this order. You can only update your review within 24 hours.'
                )
            
            # If updating, check if it's within 24 hours
            if self.instance and not self.instance.can_be_updated():
                raise serializers.ValidationError(
                    'You can only update your review within 24 hours of creating it.'
                )
        
        return data
    
    def create(self, validated_data):
        """Create review with client from request"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'client_profile'):
            validated_data['client'] = request.user.client_profile
        return super().create(validated_data)


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
            'file_audio',
            'created_date',
            'templates_count',
            'reviews_count',
            'average_rating'
        ]
    
    def get_templates_count(self, obj):
        return obj.templates.count()
    
    def get_reviews_count(self, obj):
        # Count reviews for all orders with this service
        return Review.objects.filter(
            order__service=obj,
            client__isnull=False
        ).count()
    
    def get_average_rating(self, obj):
        # Calculate average rating for this service
        reviews = Review.objects.filter(order__service=obj, client__isnull=False)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 2)
        return None


class LivrableSerializer(serializers.ModelSerializer):
    """Livrable serializer for service details"""
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Livrable
        fields = ['id', 'name', 'description', 'is_accepted', 'is_reviewed_by_admin', 'reviews']
    
    def get_reviews(self, obj):
        """Get reviews for the order this livrable belongs to"""
        order_reviews = Review.objects.filter(order=obj.order, client__isnull=False)
        return ReviewSerializer(order_reviews, many=True).data


class LivrableCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating livrables (collaborator only)
    """
    file_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Livrable
        fields = ['order', 'name', 'description', 'file_path', 'file_url']
        extra_kwargs = {
            'file_path': {'write_only': True}
        }
    
    def validate_order(self, value):
        """Validate that the order exists and is assigned to the collaborator"""
        if not value:
            raise serializers.ValidationError('Order is required.')
        
        # Check if order is assigned to the current collaborator
        request = self.context.get('request')
        if request and hasattr(request.user, 'collaborator_profile'):
            if value.collaborator != request.user.collaborator_profile:
                raise serializers.ValidationError('You can only create livrables for orders assigned to you.')
        
        return value
    
    def validate_name(self, value):
        """Validate livrable name"""
        if not value or not value.strip():
            raise serializers.ValidationError('Livrable name is required.')
        return value.strip()
    
    def validate_file_path(self, value):
        """Validate uploaded file"""
        if value:
            # Check file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if value.size > max_size:
                raise serializers.ValidationError('File size cannot exceed 50MB.')
            
            # Check file extension - ADD .ppt and .pptx here
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.ppt', '.pptx']
            file_extension = value.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise serializers.ValidationError(
                    f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                )
        
        return value
    
    def get_file_url(self, obj):
        """Return the URL to access the uploaded file"""
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None


class LivrableListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing livrables with order and client information
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='order.service.name', read_only=True)
    status_name = serializers.CharField(source='order.status.name', read_only=True)
    collaborator_name = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Livrable
        fields = [
            'id', 'name', 'description', 'is_accepted', 'is_reviewed_by_admin', 'file_path',
            'order_id', 'client_name', 'service_name', 'status_name',
            'collaborator_name', 'reviews_count'
        ]
    
    def get_client_name(self, obj):
        return obj.order.client.user.get_full_name() or obj.order.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.order.collaborator:
            return obj.order.collaborator.user.get_full_name() or obj.order.collaborator.user.username
        return "Unassigned"
    
    def get_reviews_count(self, obj):
        return Review.objects.filter(order=obj.order, client__isnull=False).count()


class LivrableDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed livrable view with all related information
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_email = serializers.CharField(source='order.client.user.email', read_only=True)
    service_name = serializers.CharField(source='order.service.name', read_only=True)
    status_name = serializers.CharField(source='order.status.name', read_only=True)
    collaborator_name = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Livrable
        fields = [
            'id', 'name', 'description', 'is_accepted', 'is_reviewed_by_admin', 'file_path',
            'order_id', 'client_name', 'client_email', 'service_name',
            'status_name', 'collaborator_name', 'reviews'
        ]
    
    def get_client_name(self, obj):
        return obj.order.client.user.get_full_name() or obj.order.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.order.collaborator:
            return obj.order.collaborator.user.get_full_name() or obj.order.collaborator.user.username
        return "Unassigned"
    
    def get_reviews(self, obj):
        """Get reviews for the order this livrable belongs to"""
        order_reviews = Review.objects.filter(order=obj.order, client__isnull=False)
        return ReviewSerializer(order_reviews, many=True).data


class LivrableAcceptRejectSerializer(serializers.ModelSerializer):
    """
    Serializer for client to accept or reject livrables
    """
    class Meta:
        model = Livrable
        fields = ['is_accepted']
    
    def validate_is_accepted(self, value):
        """Validate acceptance status"""
        if value is None:
            raise serializers.ValidationError('is_accepted field is required.')
        return value


class LivrableAdminReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for admin to mark livrables as reviewed
    """
    class Meta:
        model = Livrable
        fields = ['is_reviewed_by_admin']
    
    def validate_is_reviewed_by_admin(self, value):
        """Validate review status"""
        if value is None:
            raise serializers.ValidationError('is_reviewed_by_admin field is required.')
        return value


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
            'file_audio',
            'created_date',
            'templates',
            'reviews_count',
            'average_rating',
            'recent_reviews'
        ]
    
    def get_reviews_count(self, obj):
        return Review.objects.filter(order__service=obj, client__isnull=False).count()
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(order__service=obj, client__isnull=False)
        if reviews.exists():
            total = sum([review.rating for review in reviews])
            return round(total / reviews.count(), 2)
        return None
    
    def get_recent_reviews(self, obj):
        # Get last 5 reviews for this service
        reviews = Review.objects.filter(
            order__service=obj,
            client__isnull=False
        ).order_by('-date')[:5]
        return ReviewSerializer(reviews, many=True).data


class AllReviewsSerializer(serializers.ModelSerializer):
    """
    Serializer for all reviews listing
    """
    service_name = serializers.CharField(source='order.service.name', read_only=True)
    service_id = serializers.IntegerField(source='order.service.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id',
            'order_id',
            'service_id',
            'service_name',
            'client_name',
            'rating',
            'comment',
            'date'
        ]
    
    def get_client_name(self, obj):
        if obj.client and obj.client.user:
            return obj.client.user.get_full_name() or obj.client.user.username
        return "Unknown Client"


# Admin User Management Serializers

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing all users (admin only)
    """
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_active_collab = serializers.SerializerMethodField()
    is_blacklisted = serializers.SerializerMethodField()
    
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
            'is_blacklisted',
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
    
    def get_is_blacklisted(self, obj):
        """Get client blacklist status (only for clients)"""
        if hasattr(obj, 'client_profile'):
            return obj.client_profile.is_blacklisted
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


class CreateCollaboratorAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new collaborators by admin with auto-generated password
    """
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone'
        ]
    
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
        """Create user and collaborator profile with auto-generated password"""
        import secrets
        import string
        
        # Generate a secure random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create collaborator profile
        collaborator = Collaborator.objects.create(user=user, is_active=True)
        
        # Store the generated password in the user instance for email sending
        user._generated_password = password
        
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
            'audio_file',
            'file_audio'
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
            'file_audio',
            'created_date',
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
        return Review.objects.filter(order__service=obj, client__isnull=False).count()
    
    def get_average_rating(self, obj):
        reviews = Review.objects.filter(order__service=obj, client__isnull=False)
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


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Order Status History serializer for displaying status tracking
    """
    status_name = serializers.CharField(source='status.name', read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    changed_by_full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status_name', 'changed_by_username', 'changed_by_full_name', 'changed_at', 'notes']
        
    def get_changed_by_full_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.username
        return "System"


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
    client_id = serializers.IntegerField(source='client.id', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_email = serializers.CharField(source='client.user.email', read_only=True)
    client_phone = serializers.CharField(source='client.user.phone', read_only=True)
    service_id = serializers.IntegerField(source='service.id', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_id = serializers.IntegerField(source='status.id', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    collaborator_name = serializers.SerializerMethodField()
    remaining_payment = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()
    has_livrable = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'client_id',
            'client_name',
            'client_email', 
            'client_phone',
            'service_id',
            'service_name',
            'status_id',
            'status_name',
            'collaborator_name',
            'date',
            'deadline_date',
            'total_price',
            'advance_payment',
            'remaining_payment',
            'is_fully_paid',
            'has_livrable',
            'discount',
            'quotation',
            'lecture',
            'comment',
            'sademy_commission_amount',
            'commission_type',
            'commission_value',
            'collaborator_commission_amount',
            'collaborator_commission_type',
            'collaborator_commission_value',
            'is_blacklisted',
            'blacklist_reason'
        ]
    
    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.collaborator:
            return obj.collaborator.user.get_full_name() or obj.collaborator.user.username
        return "Unassigned"
    
    def get_has_livrable(self, obj):
        """Check if the order has any livrables"""
        return obj.livrables.exists()


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
            'comment',
            'commission_type',
            'commission_value',
            'collaborator_commission_type',
            'collaborator_commission_value',
            'is_blacklisted',
            'blacklist_reason'
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
    
    def validate_commission_value(self, value):
        """Validate commission value"""
        if value < 0:
            raise serializers.ValidationError('Commission value cannot be negative.')
        return value

    def validate_collaborator_commission_value(self, value):
        """Validate collaborator commission value"""
        if value < 0:
            raise serializers.ValidationError('Collaborator commission value cannot be negative.')
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        advance_payment = data.get('advance_payment', 0)
        total_price = data.get('total_price')
        is_blacklisted = data.get('is_blacklisted', False)
        blacklist_reason = data.get('blacklist_reason', '')
        commission_type = data.get('commission_type', 'percentage')
        commission_value = data.get('commission_value', 0)
        collaborator_commission_type = data.get('collaborator_commission_type', 'percentage')
        collaborator_commission_value = data.get('collaborator_commission_value', 0)
        
        # Only validate advance_payment vs total_price if both are provided
        if total_price is not None and advance_payment > total_price:
            raise serializers.ValidationError({
                'advance_payment': 'Advance payment cannot be greater than total price.'
            })
        
        # Validate blacklist reason is provided when order is blacklisted
        if is_blacklisted and not blacklist_reason.strip():
            raise serializers.ValidationError({
                'blacklist_reason': 'Blacklist reason is required when order is blacklisted.'
            })
        
        # Validate commission value based on type
        if commission_type == 'percentage' and commission_value > 100:
            raise serializers.ValidationError({
                'commission_value': 'Percentage commission cannot exceed 100%.'
            })

        if collaborator_commission_type == 'percentage' and collaborator_commission_value > 100:
            raise serializers.ValidationError({
                'collaborator_commission_value': 'Collaborator percentage cannot exceed 100%.'
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
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
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
            'sademy_commission_amount',
            'commission_type',
            'commission_value',
            'collaborator_commission_amount',
            'collaborator_commission_type',
            'collaborator_commission_value',
            'is_blacklisted',
            'blacklist_reason',
            'livrables',
            'status_history'
        ]
    
    def get_client_name(self, obj):
        return obj.client.user.get_full_name() or obj.client.user.username
    
    def get_collaborator_name(self, obj):
        if obj.collaborator:
            return obj.collaborator.user.get_full_name() or obj.collaborator.user.username
        return "Unassigned"


class GlobalSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for GlobalSettings model
    """
    class Meta:
        model = GlobalSettings
        fields = [
            'id',
            'commission_type',
            'commission_value',
            'is_commission_enabled',
            'collaborator_commission_type',
            'collaborator_commission_value',
            'is_collaborator_commission_enabled',
            'created_at',
            'updated_at',
            'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def validate_commission_value(self, value):
        """Validate commission value"""
        if value < 0:
            raise serializers.ValidationError('Commission value cannot be negative.')
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        commission_type = data.get('commission_type', 'percentage')
        commission_value = data.get('commission_value', 0)
        collaborator_commission_type = data.get('collaborator_commission_type', 'percentage')
        collaborator_commission_value = data.get('collaborator_commission_value', 0)
        
        # Validate commission value based on type
        if commission_type == 'percentage' and commission_value > 100:
            raise serializers.ValidationError({
                'commission_value': 'Percentage commission cannot exceed 100%.'
            })

        if collaborator_commission_type == 'percentage' and collaborator_commission_value > 100:
            raise serializers.ValidationError({
                'collaborator_commission_value': 'Collaborator percentage cannot exceed 100%.'
            })
        
        return data


class ServiceCollaboratorCommissionSerializer(serializers.ModelSerializer):
    """
    Serializer for service-level collaborator commission overrides
    """
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = ServiceCollaboratorCommission
        fields = [
            'id',
            'service',
            'service_name',
            'commission_type',
            'commission_value',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'service_name', 'created_at', 'updated_at']

    def validate_commission_value(self, value):
        if value < 0:
            raise serializers.ValidationError('Commission value cannot be negative.')
        return value

    def validate_service(self, value):
        """
        Ensure each service has at most one collaborator commission configuration
        """
        existing = ServiceCollaboratorCommission.objects.filter(service=value)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError('A collaborator commission configuration already exists for this service.')
        return value

    def validate(self, data):
        commission_type = data.get('commission_type', 'percentage')
        commission_value = data.get('commission_value', 0)

        if commission_type == 'percentage' and commission_value > 100:
            raise serializers.ValidationError({
                'commission_value': 'Percentage commission cannot exceed 100%.'
            })

        return data


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order status (admin and collaborator)
    """
    notes = serializers.CharField(required=False, allow_blank=True, write_only=True, 
                                  help_text="Optional notes about the status change")
    
    class Meta:
        model = Order
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        """Validate that status exists"""
        if not value:
            raise serializers.ValidationError('Status is required.')
        return value
    
    def update(self, instance, validated_data):
        """Update order status and set tracking attributes for signal handlers"""
        notes = validated_data.pop('notes', '')
        
        # Set attributes for signal handlers to track who made the change
        instance._changed_by_user = self.context.get('request').user if self.context.get('request') else None
        instance._status_change_notes = notes
        
        return super().update(instance, validated_data)


class OrderCancelSerializer(serializers.ModelSerializer):
    """
    Serializer for clients to cancel their orders
    """
    cancellation_reason = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Optional reason for cancellation"
    )
    
    class Meta:
        model = Order
        fields = ['cancellation_reason']
    
    def validate(self, data):
        """Validate that the order can be cancelled"""
        order = self.instance
        
        # Check if order is already cancelled
        if order.status.name == 'Cancelled':
            raise serializers.ValidationError('Order is already cancelled.')
        
        # Check if order is completed
        if order.status.name == 'Completed':
            raise serializers.ValidationError('Cannot cancel a completed order.')
        
        return data


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


class ClientOrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for clients to create orders with simplified fields
    """
    project_description = serializers.CharField(
        source='quotation',
        required=True,
        help_text="Detailed description of the project"
    )
    special_instructions = serializers.CharField(
        source='lecture',
        required=False,
        allow_blank=True,
        help_text="Optional special instructions or requirements"
    )
    budget = serializers.DecimalField(
        source='total_price',
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Optional budget suggestion (leave empty for quote)"
    )
    
    class Meta:
        model = Order
        fields = [
            'service',
            'deadline_date',
            'budget',
            'project_description',
            'special_instructions'
        ]
    
    def validate_service(self, value):
        """Validate that service exists and is active"""
        if not value:
            raise serializers.ValidationError('Service is required.')
        if not value.is_active:
            raise serializers.ValidationError('Cannot create order for inactive service.')
        return value
    
    def validate_deadline_date(self, value):
        """Validate deadline date is in the future"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError('Deadline date must be in the future.')
        return value
    
    def validate_budget(self, value):
        """Validate budget if provided"""
        if value is not None and value <= 0:
            raise serializers.ValidationError('Budget must be greater than 0 if provided.')
        return value
    
    def create(self, validated_data):
        """Create order with pending status and current client"""
        from core.models import Status
        
        # Get the pending status
        try:
            pending_status = Status.objects.get(name='pending')
        except Status.DoesNotExist:
            raise serializers.ValidationError('Pending status not found. Please contact administrator.')
        
        # Set the client from the authenticated user
        validated_data['client'] = self.context['request'].user.client_profile
        validated_data['status'] = pending_status
        
        # Set default values for required fields
        if not validated_data.get('total_price'):
            validated_data['total_price'] = 0.01  # Minimum required value
        
        return super().create(validated_data)


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for public order creation API with WhatsApp notifications
    """
    # Required fields
    service = serializers.CharField(
        help_text="Service type identifier (e.g., 'full-website', 'logo-design') or service ID (e.g., '1', '2', '3')"
    )
    projectDescription = serializers.CharField(
        source='quotation',
        min_length=50,
        help_text="Detailed project description (minimum 50 characters)"
    )
    deadline = serializers.DateField(
        source='deadline_date',
        help_text="Project deadline in YYYY-MM-DD format"
    )
    fullName = serializers.CharField(
        max_length=150,
        help_text="Client's full name"
    )
    email = serializers.EmailField(
        help_text="Client's email address"
    )
    phone = serializers.CharField(
        max_length=20,
        help_text="Client's phone number in E.164 format (e.g., +212XXXXXXXXX)"
    )
    acceptTerms = serializers.BooleanField(
        write_only=True,
        help_text="Must be true to accept terms of service"
    )
    
    # Optional fields
    technicalRequirements = serializers.CharField(
        source='lecture',
        required=False,
        allow_blank=True,
        help_text="Technical requirements and specifications"
    )
    budget = serializers.DecimalField(
        source='total_price',
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Optional budget suggestion (leave empty for quote)"
    )
    companyName = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Client's company name"
    )
    receiveUpdates = serializers.BooleanField(
        default=True,
        help_text="Whether to receive updates about the order"
    )
    
    # Service mapping
    SERVICE_MAPPING = {
        'logo-design': 1,
        'brand-identity': 2,
        'full-website': 3,
        'pitch-deck': 4,
        'social-media-assets': 5,
        'other': 6
    }
    
    def validate_service(self, value):
        """Validate service string key or service ID"""
        from core.models import Service
        
        # Check if it's a valid string key
        if value in self.SERVICE_MAPPING:
            return value
        
        # Check if it's a valid service ID (as string or try to convert to int)
        try:
            service_id = int(value)
            # Check if service exists and is active
            if Service.objects.filter(id=service_id, is_active=True).exists():
                return str(service_id)  # Return as string for consistency
        except (ValueError, TypeError):
            pass
        
        # If neither valid, raise error
        valid_keys = ', '.join(self.SERVICE_MAPPING.keys())
        raise serializers.ValidationError(
            f"Invalid service. Must be one of: {valid_keys}, or a valid active service ID"
        )
    
    def validate_acceptTerms(self, value):
        """Validate that terms are accepted"""
        if not value:
            raise serializers.ValidationError("You must accept the terms of service.")
        return value
    
    def validate_deadline(self, value):
        """Validate deadline is in the future"""
        from django.utils import timezone
        # Convert to date for comparison
        if hasattr(value, 'date'):
            value_date = value.date()
        else:
            value_date = value
        
        if value_date <= timezone.now().date():
            raise serializers.ValidationError("Deadline must be in the future.")
        return value
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Basic E.164 format validation for Morocco (+212)
        if not value.startswith('+212') or len(value) != 13:
            raise serializers.ValidationError(
                "Phone number must be in E.164 format starting with +212 (e.g., +212XXXXXXXXX)"
            )
        
        # Check if all characters after + are digits
        if not value[1:].isdigit():
            raise serializers.ValidationError("Phone number must contain only digits after the + sign.")
        
        return value
    
    def validate_budget(self, value):
        """Validate budget if provided"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0 if provided.")
        return value
    
    def create(self, validated_data):
        """Create order and client if needed"""
        from core.models import Order, Client, User, Service, Status
        from django.utils import timezone
        
        # Extract client data
        email = validated_data['email']
        full_name = validated_data['fullName']
        phone = validated_data['phone']
        company_name = validated_data.get('companyName', '')
        
        # Get or create client
        try:
            user = User.objects.get(email=email)
            client = user.client_profile
        except User.DoesNotExist:
            # Create new user and client
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                first_name=full_name.split(' ')[0] if ' ' in full_name else full_name,
                last_name=' '.join(full_name.split(' ')[1:]) if ' ' in full_name else '',
                phone=phone
            )
            client = Client.objects.create(user=user)
        
        # Update client info if needed
        if not user.phone:
            user.phone = phone
            user.save(update_fields=['phone'])
        
        # Get service - handle both string keys and service IDs
        service_value = validated_data['service']
        if service_value in self.SERVICE_MAPPING:
            # It's a string key, use the mapping
            service_id = self.SERVICE_MAPPING[service_value]
        else:
            # It's a service ID (already validated in validate_service)
            service_id = int(service_value)
        
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            raise serializers.ValidationError("Selected service is not available.")
        
        # Get pending status
        try:
            status = Status.objects.get(name='pending')
        except Status.DoesNotExist:
            raise serializers.ValidationError("System error: Pending status not found.")
        
        # Convert date to datetime (end of day)
        from django.utils import timezone
        from datetime import datetime, time, date
        deadline_date = validated_data['deadline_date']
        if isinstance(deadline_date, date) and not isinstance(deadline_date, datetime):
            # It's a date object, convert to datetime
            naive_datetime = datetime.combine(deadline_date, time.max)
            deadline_datetime = timezone.make_aware(naive_datetime)
        else:
            # It's already a datetime object
            deadline_datetime = deadline_date
        
        # Generate order number before creating order to avoid unique constraint violation
        from django.db import transaction, IntegrityError
        
        current_year = timezone.now().year
        
        # Use database transaction with retry mechanism to handle race conditions
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    # Get the highest order number for this year
                    # Use order_by to get the last order, then lock it
                    last_order_obj = Order.objects.filter(
                        order_number__startswith=f'ORD-{current_year}-'
                    ).order_by('-order_number').first()
                    
                    if last_order_obj:
                        # Extract the number part and increment
                        last_number = int(last_order_obj.order_number.split('-')[-1])
                        new_number = last_number + 1
                    else:
                        # First order of the year
                        new_number = 1
                    
                    # Format as ORD-YYYY-NNNN
                    order_number = f'ORD-{current_year}-{new_number:04d}'
                    
                    # Prepare order data
                    order_data = {
                        'client': client,
                        'service': service,
                        'status': status,
                        'deadline_date': deadline_datetime,
                        'quotation': validated_data['quotation'],
                        'lecture': validated_data.get('lecture', ''),
                        'total_price': validated_data.get('total_price', 0.01),  # Minimum required
                        'order_number': order_number,  # Set order number before creation
                    }
                    
                    # Create order
                    order = Order.objects.create(**order_data)
                    return order
                    
            except IntegrityError as e:
                # If it's a unique constraint violation, retry with a new number
                if attempt < max_retries - 1:
                    continue  # Retry with a new number
                else:
                    raise serializers.ValidationError(
                        "Failed to create order due to a conflict. Please try again."
                    )
            except Exception as e:
                # For other errors, raise immediately
                raise
        
        # Fallback: should not reach here, but just in case
        raise serializers.ValidationError(
            "Failed to create order after multiple attempts. Please try again."
        )


class OrderCreateResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for order creation response
    """
    order_number = serializers.CharField(read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    created_at = serializers.DateTimeField(source='date', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_name',
            'service',
            'service_name',
            'deadline_date',
            'created_at'
        ]


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


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile information
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        # Strip whitespace and handle empty values
        if value:
            value = value.strip().lower()  # Normalize email to lowercase
            if not value:  # Empty string after stripping
                value = None
        
        # Only validate uniqueness if email is provided and different from current
        if value and self.instance:
            # Check if email is actually being changed
            current_email = self.instance.email
            if current_email:
                current_email = current_email.strip().lower()
            
            # If email hasn't changed, no need to validate
            if value == current_email:
                return value
            
            # Check if another user has this email
            if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError('A user with this email already exists.')
        
        return value
    
    def validate_phone(self, value):
        """Validate phone uniqueness"""
        # Strip whitespace and handle empty values
        if value:
            value = value.strip()
            if not value:  # Empty string after stripping
                value = None
        
        # Only validate uniqueness if phone is provided and different from current
        if value and self.instance:
            # Check if phone is actually being changed
            current_phone = self.instance.phone
            if current_phone:
                current_phone = current_phone.strip()
            
            # If phone hasn't changed, no need to validate
            if value == current_phone:
                return value
            
            # Check if another user has this phone number
            if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError('A user with this phone number already exists.')
        
        return value


# Notification Serializers

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    order_title = serializers.CharField(source='order.service.name', read_only=True)
    livrable_id = serializers.IntegerField(source='livrable.id', read_only=True)
    livrable_name = serializers.CharField(source='livrable.name', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'priority',
            'is_read',
            'is_email_sent',
            'created_at',
            'read_at',
            'order_id',
            'order_title',
            'livrable_id',
            'livrable_name',
            'time_ago'
        ]
        read_only_fields = ['created_at', 'read_at', 'is_email_sent']
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing notifications with minimal data
    """
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'priority',
            'is_read',
            'created_at',
            'time_ago'
        ]
    
    def get_time_ago(self, obj):
        """Get human-readable time ago"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read
    """
    is_read = serializers.BooleanField()
    
    def update(self, instance, validated_data):
        """Update notification read status"""
        is_read = validated_data.get('is_read', False)
        
        if is_read:
            instance.mark_as_read()
        else:
            instance.mark_as_unread()
        
        return instance


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics
    """
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()
    unread_by_type = serializers.DictField()
    recent_notifications = NotificationListSerializer(many=True)


# Chatbot Workflow Serializers

class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializer for language selection
    """
    class Meta:
        model = Language
        fields = ['id', 'code', 'name', 'is_active']


class ChatbotSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for chatbot session
    """
    language_name = serializers.CharField(source='language.name', read_only=True)
    service_name = serializers.CharField(source='selected_service.name', read_only=True)
    template_title = serializers.CharField(source='selected_template.title', read_only=True)
    
    class Meta:
        model = ChatbotSession
        fields = [
            'id', 'session_id', 'language', 'language_name', 'selected_service', 
            'service_name', 'selected_template', 'template_title', 'custom_description',
            'client_name', 'client_email', 'client_phone', 'is_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'session_id', 'created_at', 'updated_at']


class ChatbotSessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating chatbot session
    """
    class Meta:
        model = ChatbotSession
        fields = ['language', 'selected_service', 'selected_template', 'custom_description',
                 'client_name', 'client_email', 'client_phone']
    
    def create(self, validated_data):
        """Create session with auto-generated session_id"""
        import uuid
        session_id = str(uuid.uuid4())
        validated_data['session_id'] = session_id
        return super().create(validated_data)


class ChatbotSessionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating chatbot session
    """
    class Meta:
        model = ChatbotSession
        fields = ['language', 'selected_service', 'selected_template', 'custom_description',
                 'client_name', 'client_email', 'client_phone', 'is_completed']


class ChatbotClientRegistrationSerializer(serializers.Serializer):
    """
    Serializer for chatbot client registration
    """
    session_id = serializers.CharField()
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_session_id(self, value):
        """Validate that session exists and is not completed"""
        try:
            session = ChatbotSession.objects.get(session_id=value)
            if session.is_completed:
                raise serializers.ValidationError('Session is already completed.')
        except ChatbotSession.DoesNotExist:
            raise serializers.ValidationError('Invalid session ID.')
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value


class ChatbotOrderReviewSerializer(serializers.Serializer):
    """
    Serializer for chatbot order review
    """
    session_id = serializers.CharField()
    
    def validate_session_id(self, value):
        """Validate that session exists and has required data"""
        try:
            session = ChatbotSession.objects.get(session_id=value)
            if not session.selected_service:
                raise serializers.ValidationError('No service selected in this session.')
            if not session.client_name or not session.client_email:
                raise serializers.ValidationError('Client information is incomplete.')
        except ChatbotSession.DoesNotExist:
            raise serializers.ValidationError('Invalid session ID.')
        return value


class ChatbotOrderConfirmationSerializer(serializers.Serializer):
    """
    Serializer for chatbot order confirmation
    """
    session_id = serializers.CharField()
    confirm = serializers.BooleanField()
    
    def validate_session_id(self, value):
        """Validate that session exists and is ready for confirmation"""
        try:
            session = ChatbotSession.objects.get(session_id=value)
            if session.is_completed:
                raise serializers.ValidationError('Session is already completed.')
            if not session.selected_service:
                raise serializers.ValidationError('No service selected in this session.')
            if not session.client_name or not session.client_email:
                raise serializers.ValidationError('Client information is incomplete.')
        except ChatbotSession.DoesNotExist:
            raise serializers.ValidationError('Invalid session ID.')
        return value


class ChatbotOrderResponseSerializer(serializers.Serializer):
    """
    Serializer for chatbot order creation response
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    order_id = serializers.IntegerField(required=False)
    client_username = serializers.CharField(required=False)
    client_password = serializers.CharField(required=False)
    redirect_url = serializers.URLField(required=False)


# ==================== NOTIFICATION SERIALIZERS ====================

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    livrable_id = serializers.IntegerField(source='livrable.id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'priority',
            'is_read', 'created_at', 'read_at', 'order_id', 'livrable_id'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Serializer for notification list view
    """
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    livrable_id = serializers.IntegerField(source='livrable.id', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'priority',
            'is_read', 'created_at', 'read_at', 'order_id', 'livrable_id'
        ]


class NotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for notification statistics
    """
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()