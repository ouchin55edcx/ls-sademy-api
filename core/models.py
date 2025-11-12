from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Override groups and user_permissions to add unique related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"


class Admin(models.Model):
    """
    Admin model - One-to-One relationship with User
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='admin_profile'
    )

    class Meta:
        db_table = 'admins'
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'

    def __str__(self):
        return f"Admin: {self.user.username}"


class Collaborator(models.Model):
    """
    Collaborator model - One-to-One relationship with User
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='collaborator_profile'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'collaborators'
        verbose_name = 'Collaborator'
        verbose_name_plural = 'Collaborators'

    def __str__(self):
        return f"Collaborator: {self.user.username}"


class Client(models.Model):
    """
    Client model - One-to-One relationship with User
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='client_profile'
    )
    city = models.CharField(max_length=100, blank=True)
    is_blacklisted = models.BooleanField(
        default=False,
        help_text="Mark this client as blacklisted"
    )

    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"Client: {self.user.username}"


class Service(models.Model):
    """
    Service model
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    tool_name = models.CharField(max_length=100, blank=True)
    audio_file = models.FileField(upload_to='media/services/audio/', blank=True, null=True)
    file_audio = models.FileField(upload_to='media/', blank=True, null=True, help_text="Audio file for the service")
    created_date = models.DateTimeField(auto_now_add=True, help_text="Date when the service was created")

    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class Template(models.Model):
    """
    Template model - Each service can have multiple templates
    For public display to visitors
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='templates/files/', blank=True, null=True, help_text="Template file")
    demo_video = models.FileField(upload_to='templates/demos/', blank=True, null=True, help_text="Demo video file")

    class Meta:
        db_table = 'templates'
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.service.name}"


class Status(models.Model):
    """
    Status model for Order statuses
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'statuses'
        verbose_name = 'Status'
        verbose_name_plural = 'Statuses'

    def __str__(self):
        return self.name


class GlobalSettings(models.Model):
    """
    Global Settings model for application-wide configuration
    """
    COMMISSION_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    # Sademy Commission Settings
    commission_type = models.CharField(
        max_length=20,
        choices=COMMISSION_TYPE_CHOICES,
        default='percentage',
        help_text="Type of commission calculation"
    )
    commission_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Commission value (percentage or fixed amount)"
    )
    is_commission_enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable automatic commission calculation"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='settings_updates'
    )

    class Meta:
        db_table = 'global_settings'
        verbose_name = 'Global Settings'
        verbose_name_plural = 'Global Settings'

    def __str__(self):
        return f"Global Settings - Commission: {self.commission_value} ({self.commission_type})"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and GlobalSettings.objects.exists():
            raise ValueError("Only one GlobalSettings instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the global settings instance, create if doesn't exist"""
        settings, created = cls.objects.get_or_create(
            defaults={
                'commission_type': 'percentage',
                'commission_value': Decimal('20.00'),
                'is_commission_enabled': True,
            }
        )
        return settings


class Order(models.Model):
    """
    Order model with relationships to Client, Service, Status, and Collaborator
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    collaborator = models.ForeignKey(
        Collaborator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    chatbot_session = models.ForeignKey(
        'ChatbotSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Chatbot session that created this order"
    )
    
    # Order details
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Auto-generated order number (e.g., ORD-2024-0001)"
    )
    date = models.DateTimeField(auto_now_add=True)
    deadline_date = models.DateTimeField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    advance_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Optional fields
    description = models.TextField(blank=True, help_text="Project description from chatbot or custom input")
    quotation = models.TextField(blank=True)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    lecture = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    
    # Sademy Commission fields
    sademy_commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Calculated Sademy commission amount"
    )
    commission_type = models.CharField(
        max_length=20,
        choices=GlobalSettings.COMMISSION_TYPE_CHOICES,
        default='percentage',
        help_text="Type of commission applied to this order"
    )
    commission_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Commission value applied to this order"
    )
    
    # Blacklist fields
    is_blacklisted = models.BooleanField(
        default=False,
        help_text="Mark this order as blacklisted"
    )
    blacklist_reason = models.TextField(
        blank=True,
        help_text="Reason for blacklisting (required if is_blacklisted is True)"
    )

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-date']
        indexes = [
            models.Index(
                fields=['collaborator', 'status'],
                name='order_collab_status_idx',
            ),
            models.Index(
                fields=['client', 'status'],
                name='order_client_status_idx',
            ),
            models.Index(
                fields=['service', 'status'],
                name='order_service_status_idx',
            ),
            models.Index(
                fields=['status', 'deadline_date'],
                name='order_status_deadline_idx',
            ),
        ]

    def __str__(self):
        collaborator_name = self.collaborator.user.username if self.collaborator else "Unassigned"
        return f"Order #{self.id} - {self.client.user.username} - {self.status.name} - {collaborator_name}"

    @property
    def remaining_payment(self):
        """Calculate remaining payment"""
        return self.total_price - self.advance_payment

    @property
    def is_fully_paid(self):
        """Check if order is fully paid"""
        return self.advance_payment >= self.total_price
    
    def generate_order_number(self):
        """
        Generate unique order number in format ORD-YYYY-NNNN
        """
        from django.utils import timezone
        from django.db.models import Max
        
        if self.order_number:
            return self.order_number
        
        current_year = timezone.now().year
        
        # Get the highest order number for this year
        last_order = Order.objects.filter(
            order_number__startswith=f'ORD-{current_year}-'
        ).aggregate(max_number=Max('order_number'))
        
        if last_order['max_number']:
            # Extract the number part and increment
            last_number = int(last_order['max_number'].split('-')[-1])
            new_number = last_number + 1
        else:
            # First order of the year
            new_number = 1
        
        # Format as ORD-YYYY-NNNN
        self.order_number = f'ORD-{current_year}-{new_number:04d}'
        return self.order_number
    
    def calculate_commission(self, commission_type=None, commission_value=None):
        """
        Calculate Sademy commission based on order price and commission settings
        """
        if commission_type is None:
            commission_type = self.commission_type
        if commission_value is None:
            commission_value = self.commission_value
            
        if commission_type == 'percentage':
            # Calculate percentage commission
            commission_amount = (self.total_price * commission_value) / 100
        else:  # fixed amount
            commission_amount = commission_value
            
        return commission_amount
    
    def apply_global_commission_settings(self):
        """
        Apply global commission settings to this order
        """
        try:
            global_settings = GlobalSettings.get_settings()
            if global_settings.is_commission_enabled:
                self.commission_type = global_settings.commission_type
                self.commission_value = global_settings.commission_value
                self.sademy_commission_amount = self.calculate_commission()
        except Exception as e:
            # Log error but don't fail the order creation
            import logging
            logging.error(f"Failed to apply global commission settings: {str(e)}")
    
    def clean(self):
        """
        Validate order data
        """
        from django.core.exceptions import ValidationError
        
        # Validate blacklist reason is provided when order is blacklisted
        if self.is_blacklisted and not self.blacklist_reason.strip():
            raise ValidationError({
                'blacklist_reason': 'Blacklist reason is required when order is blacklisted.'
            })
        
        # Validate commission value based on type
        if self.commission_type == 'percentage' and self.commission_value > 100:
            raise ValidationError({
                'commission_value': 'Percentage commission cannot exceed 100%.'
            })


class Livrable(models.Model):
    """
    Livrable (Deliverable) model - linked to Order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='livrables'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_path = models.FileField(upload_to='livrables/', blank=True, null=True)
    is_accepted = models.BooleanField(default=False)
    is_reviewed_by_admin = models.BooleanField(default=False)

    class Meta:
        db_table = 'livrables'
        verbose_name = 'Livrable'
        verbose_name_plural = 'Livrables'

    def __str__(self):
        return f"Livrable: {self.name} - Order #{self.order.id}"


class OrderStatusHistory(models.Model):
    """
    Order Status History model - tracks all status changes for an order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name='status_history'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Optional notes about the status change")

    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-changed_at']

    def __str__(self):
        changed_by_name = self.changed_by.username if self.changed_by else "System"
        return f"Order #{self.order.id} - {self.status.name} - {changed_by_name} - {self.changed_at.strftime('%Y-%m-%d %H:%M')}"


class Review(models.Model):
    """
    Review model - linked to Order
    Client can review the order after it's completed and accepted
    Only one review per order per client, can be updated within 24 hours
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,  # Allow null temporarily for migration
        blank=True
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,  # Allow null temporarily for migration
        blank=True
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-date']
        unique_together = ['order', 'client']  # One review per order per client

    def __str__(self):
        return f"Review for Order #{self.order.id} by {self.client.user.username} - {self.rating} stars"
    
    def can_be_updated(self):
        """Check if review can be updated (within 24 hours of creation)"""
        from django.utils import timezone
        from datetime import timedelta
        
        time_diff = timezone.now() - self.date
        return time_diff <= timedelta(hours=24)


class Language(models.Model):
    """
    Language model for chatbot language selection
    """
    code = models.CharField(max_length=10, unique=True, help_text="Language code (e.g., 'en', 'fr', 'ar')")
    name = models.CharField(max_length=100, help_text="Language name (e.g., 'English', 'French', 'Arabic')")
    is_active = models.BooleanField(default=True, help_text="Whether this language is available for selection")
    
    class Meta:
        db_table = 'languages'
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class ChatbotSession(models.Model):
    """
    Chatbot session model to track user interactions during the order flow
    """
    session_id = models.CharField(max_length=100, unique=True, help_text="Unique session identifier")
    language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Selected language for the session"
    )
    selected_service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Service selected by the user"
    )
    selected_template = models.ForeignKey(
        Template,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template selected by the user (if any)"
    )
    custom_description = models.TextField(
        blank=True,
        help_text="Custom project description provided by the user"
    )
    client_name = models.CharField(max_length=200, blank=True, help_text="Client's name")
    client_email = models.EmailField(blank=True, help_text="Client's email")
    client_phone = models.CharField(max_length=20, blank=True, help_text="Client's phone number")
    is_completed = models.BooleanField(default=False, help_text="Whether the chatbot flow is completed")
    conversation_history = models.JSONField(default=list, help_text="Chat conversation history")
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about this session")
    chat_status = models.CharField(max_length=20, blank=True, null=True, help_text="Current chat status")
    whatsapp_link = models.CharField(max_length=200, blank=True, null=True, help_text="WhatsApp link for the session")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_sessions'
        verbose_name = 'Chatbot Session'
        verbose_name_plural = 'Chatbot Sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.client_name or 'Anonymous'}"


class Notification(models.Model):
    """
    Notification model for in-app and email notifications
    """
    NOTIFICATION_TYPES = [
        ('order_assigned', 'Order Assigned'),
        ('order_status_changed', 'Order Status Changed'),
        ('order_cancelled', 'Order Cancelled'),
        ('livrable_uploaded', 'Deliverable Uploaded'),
        ('livrable_reviewed', 'Deliverable Reviewed'),
        ('livrable_accepted', 'Deliverable Accepted'),
        ('livrable_rejected', 'Deliverable Rejected'),
        ('payment_reminder', 'Payment Reminder'),
        ('deadline_reminder', 'Deadline Reminder'),
        ('order_completed', 'Order Completed'),
        ('review_reminder', 'Review Reminder'),
        ('system_alert', 'System Alert'),
        ('account_created', 'Account Created'),
        ('user_blacklisted', 'User Blacklisted'),
        ('chatbot_order_created', 'Chatbot Order Created'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text="User who will receive the notification"
    )
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES,
        help_text="Type of notification"
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message content"
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_LEVELS, 
        default='medium',
        help_text="Notification priority level"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    is_email_sent = models.BooleanField(
        default=False,
        help_text="Whether email notification was sent"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the notification was created"
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the notification was read"
    )
    
    # Optional related objects
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications',
        help_text="Related order (if applicable)"
    )
    livrable = models.ForeignKey(
        Livrable, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications',
        help_text="Related deliverable (if applicable)"
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username} ({'Read' if self.is_read else 'Unread'})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None
        self.save()


# Signal handlers for automatic status history tracking
# @receiver(post_save, sender=Order)
# def create_status_history_on_order_creation(sender, instance, created, **kwargs):
#     """
#     Create initial status history entry when an order is created
#     """
#     if created:
#         OrderStatusHistory.objects.create(
#             order=instance,
#             status=instance.status,
#             changed_by=None,  # System created
#             notes="Order created"
#         )


# @receiver(pre_save, sender=Order)
# def track_status_change(sender, instance, **kwargs):
#     """
#     Track status changes before saving the order
#     """
#     if instance.pk:  # Only for existing orders
#         try:
#             old_order = Order.objects.get(pk=instance.pk)
#             if old_order.status != instance.status:
#                 # Store the old status to create history entry after save
#                 instance._status_changed = True
#                 instance._old_status = old_order.status
#         except Order.DoesNotExist:
#             pass


# @receiver(post_save, sender=Order)
# def create_status_history_on_status_change(sender, instance, created, **kwargs):
#     """
#     Create status history entry when status changes
#     """
#     if not created and hasattr(instance, '_status_changed') and instance._status_changed:
#         # Try to get the user from the current request context
#         # This will be set by the view when updating the order
#         changed_by = getattr(instance, '_changed_by_user', None)
#         notes = getattr(instance, '_status_change_notes', '')
#         
#         OrderStatusHistory.objects.create(
#             order=instance,
#             status=instance.status,
#             changed_by=changed_by,
#             notes=notes
#         )
#         
#         # Clean up temporary attributes
#         delattr(instance, '_status_changed')
#         delattr(instance, '_old_status')
#         if hasattr(instance, '_changed_by_user'):
#             delattr(instance, '_changed_by_user')
#         if hasattr(instance, '_status_change_notes'):
#             delattr(instance, '_status_change_notes')


# @receiver(post_save, sender=Order)
# def blacklist_client_on_order_blacklist(sender, instance, created, **kwargs):
#     """
#     Blacklist client when order is blacklisted
#     """
#     if not created and instance.is_blacklisted:
#         # Check if the client is not already blacklisted
#         if not instance.client.is_blacklisted:
#             instance.client.is_blacklisted = True
#             instance.client.save()


# Notification signal handlers
# @receiver(post_save, sender=Order)
# def generate_order_number(sender, instance, created, **kwargs):
#     """Generate order number when order is created"""
#     if created and not instance.order_number:
#         instance.generate_order_number()
#         instance.save(update_fields=['order_number'])


# @receiver(post_save, sender=Order)
# def notify_order_status_change(sender, instance, created, **kwargs):
#     """Send notifications when order status changes"""
#     if not created and hasattr(instance, '_status_changed') and instance._status_changed:
#         old_status = getattr(instance, '_old_status', None)
#         if old_status and old_status != instance.status:
#             from core.notification_service import NotificationService
#             NotificationService.notify_order_status_change(
#                 instance, old_status, instance.status, 
#                 getattr(instance, '_changed_by_user', None)
#             )


@receiver(post_save, sender=Livrable)
def notify_livrable_uploaded(sender, instance, created, **kwargs):
    """Notify client when collaborator uploads deliverable"""
    if created and instance.order.client:
        from core.notification_service import NotificationService
        NotificationService.notify_livrable_uploaded(instance)


@receiver(post_save, sender=Livrable)
def notify_livrable_reviewed(sender, instance, created, **kwargs):
    """Notify client when admin reviews deliverable"""
    if not created and instance.is_reviewed_by_admin:
        from core.notification_service import NotificationService
        NotificationService.notify_livrable_reviewed(instance)


@receiver(post_save, sender=Livrable)
def notify_livrable_accepted(sender, instance, created, **kwargs):
    """Notify collaborator when client accepts deliverable"""
    if not created and instance.is_accepted:
        from core.notification_service import NotificationService
        NotificationService.notify_livrable_accepted(instance)


# @receiver(post_save, sender=Order)
# def notify_order_completed(sender, instance, created, **kwargs):
#     """Notify users when order is completed"""
#     if not created and instance.status.name.lower() == 'completed':
#         from core.notification_service import NotificationService
#         NotificationService.notify_order_completed(instance)