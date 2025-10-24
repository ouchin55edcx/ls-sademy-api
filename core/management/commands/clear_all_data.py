"""
Django Management Command to clear all data except admin users
Run with: python manage.py clear_all_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Admin, Collaborator, Client, Service, Template, Status, 
    Order, Livrable, Review, OrderStatusHistory, GlobalSettings
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Clears all data from all tables except admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all data except admin users',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    'This command will delete ALL data except admin users!\n'
                    'Use --confirm flag to proceed.\n'
                    'Example: python manage.py clear_all_data --confirm'
                )
            )
            return

        self.stdout.write('Starting data cleanup...')
        
        # Get admin users to preserve
        admin_users = User.objects.filter(admin_profile__isnull=False)
        admin_usernames = [user.username for user in admin_users]
        
        self.stdout.write(f'Preserving {len(admin_users)} admin users: {", ".join(admin_usernames)}')
        
        # Clear data in reverse dependency order to avoid foreign key constraints
        self.stdout.write('Clearing reviews...')
        Review.objects.all().delete()
        
        self.stdout.write('Clearing order status history...')
        OrderStatusHistory.objects.all().delete()
        
        self.stdout.write('Clearing livrables...')
        Livrable.objects.all().delete()
        
        self.stdout.write('Clearing orders...')
        Order.objects.all().delete()
        
        self.stdout.write('Clearing statuses...')
        Status.objects.all().delete()
        
        self.stdout.write('Clearing templates...')
        Template.objects.all().delete()
        
        self.stdout.write('Clearing services...')
        Service.objects.all().delete()
        
        self.stdout.write('Clearing clients...')
        Client.objects.all().delete()
        
        self.stdout.write('Clearing collaborators...')
        Collaborator.objects.all().delete()
        
        # Clear all non-admin users
        self.stdout.write('Clearing non-admin users...')
        non_admin_users = User.objects.exclude(admin_profile__isnull=False)
        non_admin_count = non_admin_users.count()
        non_admin_users.delete()
        self.stdout.write(f'Deleted {non_admin_count} non-admin users')
        
        # Keep GlobalSettings as they are configuration data
        self.stdout.write('Preserving GlobalSettings...')
        
        # Verify admin users are still there
        remaining_admin_users = User.objects.filter(admin_profile__isnull=False)
        self.stdout.write(f'Remaining admin users: {remaining_admin_users.count()}')
        
        for admin in remaining_admin_users:
            self.stdout.write(f'  ✓ {admin.username} ({admin.email})')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Data cleanup completed successfully!\n'
                f'Preserved {remaining_admin_users.count()} admin users.\n'
                f'All other data has been cleared.'
            )
        )
