"""
Django Management Command to clear all data from the database
Run with: python manage.py clear_all_data --confirm
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Admin, Collaborator, Client, Service, Template, Status, 
    Order, Livrable, Review, OrderStatusHistory, GlobalSettings,
    ChatbotSession, Notification, Language
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Clears ALL data from ALL tables (including admin users)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete ALL data (including admin users)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    '⚠️  WARNING: This command will delete ALL data including admin users!\n'
                    'This action cannot be undone!\n'
                    'Use --confirm flag to proceed.\n'
                    'Example: python manage.py clear_all_data --confirm'
                )
            )
            return

        self.stdout.write('Starting complete data cleanup...')
        
        # Clear data in reverse dependency order to avoid foreign key constraints
        self.stdout.write('Clearing notifications...')
        Notification.objects.all().delete()
        
        self.stdout.write('Clearing reviews...')
        Review.objects.all().delete()
        
        self.stdout.write('Clearing order status history...')
        OrderStatusHistory.objects.all().delete()
        
        self.stdout.write('Clearing livrables...')
        Livrable.objects.all().delete()
        
        self.stdout.write('Clearing orders...')
        Order.objects.all().delete()
        
        self.stdout.write('Clearing chatbot sessions...')
        ChatbotSession.objects.all().delete()
        
        self.stdout.write('Clearing statuses...')
        Status.objects.all().delete()
        
        self.stdout.write('Clearing templates...')
        Template.objects.all().delete()
        
        self.stdout.write('Clearing services...')
        Service.objects.all().delete()
        
        self.stdout.write('Clearing languages...')
        Language.objects.all().delete()
        
        self.stdout.write('Clearing clients...')
        Client.objects.all().delete()
        
        self.stdout.write('Clearing collaborators...')
        Collaborator.objects.all().delete()
        
        self.stdout.write('Clearing admins...')
        Admin.objects.all().delete()
        
        self.stdout.write('Clearing global settings...')
        GlobalSettings.objects.all().delete()
        
        # Clear ALL users (including admin users)
        self.stdout.write('Clearing ALL users...')
        user_count = User.objects.count()
        User.objects.all().delete()
        self.stdout.write(f'Deleted {user_count} users (including admins)')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Data cleanup completed successfully!\n'
                f'All data has been deleted from the database.\n'
                f'The database is now empty.'
            )
        )
