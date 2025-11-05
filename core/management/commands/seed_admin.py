"""
Django Management Command to seed admin data only
Run with: python manage.py seed_admin
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Admin, GlobalSettings, Status
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with admin data only (admin users, global settings, and statuses)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the admin user (default: admin)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@sademiy.com',
            help='Email for the admin user (default: admin@sademiy.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the admin user (default: admin123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Super',
            help='First name for the admin user (default: Super)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name for the admin user (default: Admin)'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='+212600000001',
            help='Phone number for the admin user (default: +212600000001)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting admin data seeding...')

        # Create Admin User
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone = options['phone']

        self.stdout.write('Creating admin user...')
        
        # Check if admin user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  User with username "{username}" already exists. Skipping...')
            )
        elif User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'  ⚠️  User with email "{email}" already exists. Skipping...')
            )
        else:
            try:
                # Create superuser
                admin_user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,
                    is_superuser=True
                )
                admin_user.phone = phone
                admin_user.save()

                # Create admin profile
                Admin.objects.create(user=admin_user)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created admin user:\n'
                        f'     Username: {username}\n'
                        f'     Email: {email}\n'
                        f'     Password: {password}\n'
                        f'     Phone: {phone}\n'
                        f'     Name: {first_name} {last_name}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error creating admin user: {str(e)}')
                )

        # Create Global Settings if they don't exist
        self.stdout.write('Creating global settings...')
        try:
            if GlobalSettings.objects.exists():
                self.stdout.write(
                    self.style.WARNING('  ℹ️  Global settings already exist. Skipping...')
                )
            else:
                settings, created = GlobalSettings.objects.get_or_create(
                    defaults={
                        'commission_type': 'percentage',
                        'commission_value': Decimal('20.00'),
                        'is_commission_enabled': True,
                    }
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created global settings:\n'
                            f'     Commission Type: {settings.commission_type}\n'
                            f'     Commission Value: {settings.commission_value}\n'
                            f'     Commission Enabled: {settings.is_commission_enabled}'
                        )
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error creating global settings: {str(e)}')
            )

        # Create Statuses
        self.stdout.write('Creating statuses...')
        statuses = ['pending', 'confirmed', 'in_progress', 'under_review', 'completed', 'cancelled']
        created_count = 0
        skipped_count = 0
        
        for status_name in statuses:
            try:
                status, created = Status.objects.get_or_create(name=status_name)
                if created:
                    self.stdout.write(f'  ✓ Created status: {status_name}')
                    created_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error creating status "{status_name}": {str(e)}')
                )
        
        if skipped_count > 0:
            self.stdout.write(f'  ℹ️  {skipped_count} status(es) already exist')

        # Summary
        admin_count = Admin.objects.count()
        user_count = User.objects.filter(admin_profile__isnull=False).count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Admin data seeding completed!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        status_count = Status.objects.count()
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  • {admin_count} Admin profile(s)')
        self.stdout.write(f'  • {user_count} Admin user(s)')
        self.stdout.write(f'  • {status_count} Status(es)')
        
        if admin_count > 0:
            self.stdout.write('\nAdmin Users:')
            for admin in Admin.objects.all():
                self.stdout.write(
                    f'  • {admin.user.username} ({admin.user.email}) - '
                    f'Phone: {admin.user.phone or "N/A"}'
                )

