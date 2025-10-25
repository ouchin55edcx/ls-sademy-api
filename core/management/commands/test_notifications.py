"""
Management command to test notification system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Admin, Client, Collaborator, Order, Service, Status, Livrable
from core.notification_service import NotificationService
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Test notification system by creating sample data and triggering notifications'

    def handle(self, *args, **options):
        self.stdout.write('Testing notification system...')
        
        try:
            # Create test users if they don't exist
            admin_user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={
                    'email': 'admin@test.com',
                    'first_name': 'Test',
                    'last_name': 'Admin',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            client_user, created = User.objects.get_or_create(
                username='test_client',
                defaults={
                    'email': 'client@test.com',
                    'first_name': 'Test',
                    'last_name': 'Client'
                }
            )
            
            collaborator_user, created = User.objects.get_or_create(
                username='test_collaborator',
                defaults={
                    'email': 'collaborator@test.com',
                    'first_name': 'Test',
                    'last_name': 'Collaborator'
                }
            )
            
            # Create profiles
            admin_profile, created = Admin.objects.get_or_create(user=admin_user)
            client_profile, created = Client.objects.get_or_create(user=client_user)
            collaborator_profile, created = Collaborator.objects.get_or_create(
                user=collaborator_user,
                defaults={'is_active': True}
            )
            
            # Create test service
            service, created = Service.objects.get_or_create(
                name='Test Service',
                defaults={
                    'description': 'Test service for notifications',
                    'is_active': True
                }
            )
            
            # Create test statuses
            pending_status, created = Status.objects.get_or_create(name='pending')
            under_review_status, created = Status.objects.get_or_create(name='under_review')
            completed_status, created = Status.objects.get_or_create(name='completed')
            
            # Create test order
            order, created = Order.objects.get_or_create(
                client=client_profile,
                service=service,
                status=pending_status,
                defaults={
                    'deadline_date': datetime.now() + timedelta(days=7),
                    'total_price': Decimal('100.00'),
                    'advance_payment': Decimal('50.00')
                }
            )
            
            self.stdout.write(f'Created test order: {order.id}')
            
            # Test 1: Admin notification for new order
            self.stdout.write('Testing admin notification for new order...')
            NotificationService.create_notification(
                user=admin_user,
                notification_type='order_assigned',
                title=f'New Order Created - Order #{order.id}',
                message=f'A new order has been created by {client_user.get_full_name() or client_user.username} for {service.name}',
                priority='medium',
                order=order
            )
            self.stdout.write('✓ Admin notification created')
            
            # Test 2: Collaborator notification for order assignment
            self.stdout.write('Testing collaborator notification for order assignment...')
            NotificationService.create_notification(
                user=collaborator_user,
                notification_type='order_assigned',
                title=f'New Order Assigned - Order #{order.id}',
                message=f'You have been assigned a new order #{order.id} for {service.name} by {client_user.get_full_name() or client_user.username}',
                priority='medium',
                order=order
            )
            self.stdout.write('✓ Collaborator notification created')
            
            # Test 3: Admin notification for order under review
            self.stdout.write('Testing admin notification for order under review...')
            NotificationService.create_notification(
                user=admin_user,
                notification_type='order_status_changed',
                title=f'Order Under Review - Order #{order.id}',
                message=f'Order #{order.id} has been submitted for review by {collaborator_user.get_full_name() or collaborator_user.username}',
                priority='medium',
                order=order
            )
            self.stdout.write('✓ Admin notification for under review created')
            
            # Test 4: Client notification for livrable reviewed
            self.stdout.write('Testing client notification for livrable reviewed...')
            NotificationService.create_notification(
                user=client_user,
                notification_type='livrable_reviewed',
                title=f'Deliverable Reviewed - Order #{order.id}',
                message=f'Your deliverable has been reviewed by admin and is ready for your approval.',
                priority='medium',
                order=order
            )
            self.stdout.write('✓ Client notification for livrable reviewed created')
            
            # Test 5: Collaborator notification for livrable accepted
            self.stdout.write('Testing collaborator notification for livrable accepted...')
            NotificationService.create_notification(
                user=collaborator_user,
                notification_type='livrable_accepted',
                title=f'Deliverable Accepted - Order #{order.id}',
                message=f'Your deliverable has been accepted by {client_user.get_full_name() or client_user.username}',
                priority='medium',
                order=order
            )
            self.stdout.write('✓ Collaborator notification for livrable accepted created')
            
            # Test 6: Collaborator notification for livrable rejected
            self.stdout.write('Testing collaborator notification for livrable rejected...')
            NotificationService.create_notification(
                user=collaborator_user,
                notification_type='livrable_rejected',
                title=f'Deliverable Rejected - Order #{order.id}',
                message=f'Your deliverable has been rejected by {client_user.get_full_name() or client_user.username}. Please review and resubmit.',
                priority='high',
                order=order
            )
            self.stdout.write('✓ Collaborator notification for livrable rejected created')
            
            # Test 7: Admin notification for order cancelled
            self.stdout.write('Testing admin notification for order cancelled...')
            NotificationService.create_notification(
                user=admin_user,
                notification_type='order_cancelled',
                title=f'Order Cancelled by Client - Order #{order.id}',
                message=f'Order #{order.id} has been cancelled by {client_user.get_full_name() or client_user.username}',
                priority='high',
                order=order
            )
            self.stdout.write('✓ Admin notification for order cancelled created')
            
            # Test notification stats
            self.stdout.write('Testing notification statistics...')
            admin_stats = NotificationService.get_notification_stats(admin_user)
            client_stats = NotificationService.get_notification_stats(client_user)
            collaborator_stats = NotificationService.get_notification_stats(collaborator_user)
            
            self.stdout.write(f'Admin notifications: {admin_stats}')
            self.stdout.write(f'Client notifications: {client_stats}')
            self.stdout.write(f'Collaborator notifications: {collaborator_stats}')
            
            self.stdout.write(
                self.style.SUCCESS('✓ All notification tests completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing notifications: {str(e)}')
            )
