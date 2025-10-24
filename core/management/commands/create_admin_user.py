#!/usr/bin/env python3
"""
Django management command to create an admin user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Admin, User

User = get_user_model()

class Command(BaseCommand):
    help = 'Create an admin user with admin role'

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
            default='Admin',
            help='First name for the admin user (default: Admin)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Last name for the admin user (default: User)'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with username "{username}" already exists.')
                )
                return

            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with email "{email}" already exists.')
                )
                return

            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True
            )

            # Create admin profile
            admin_profile = Admin.objects.create(user=user)

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Admin user created successfully!\n'
                    f'   Username: {username}\n'
                    f'   Email: {email}\n'
                    f'   Password: {password}\n'
                    f'   User ID: {user.id}\n'
                    f'   Admin Profile: {admin_profile}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user: {str(e)}')
            )
