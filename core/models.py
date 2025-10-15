from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
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
    file = models.FileField(upload_to='media/templates/files/', blank=True, null=True, help_text="Template file")
    demo_video = models.FileField(upload_to='media/templates/demos/', blank=True, null=True, help_text="Demo video file")

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
    
    # Order details
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
    quotation = models.TextField(blank=True)
    discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    lecture = models.TextField(blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-date']

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

    class Meta:
        db_table = 'livrables'
        verbose_name = 'Livrable'
        verbose_name_plural = 'Livrables'

    def __str__(self):
        return f"Livrable: {self.name} - Order #{self.order.id}"


class Review(models.Model):
    """
    Review model - linked to Livrable
    Client can review the deliverable
    """
    livrable = models.ForeignKey(
        Livrable,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-date']

    def __str__(self):
        return f"Review for {self.livrable.name} - {self.rating} stars"