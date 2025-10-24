#!/usr/bin/env python3
"""
Django management command to list all admin users
"""
from django.core.management.base import BaseCommand
from core.models import Admin

class Command(BaseCommand):
    help = 'List all admin users'

    def handle(self, *args, **options):
        try:
            admins = Admin.objects.all()
            
            if not admins:
                self.stdout.write(
                    self.style.WARNING('No admin users found.')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f'Found {len(admins)} admin user(s):\n')
            )

            for admin in admins:
                user = admin.user
                self.stdout.write(
                    f'👤 Admin: {admin}\n'
                    f'   Username: {user.username}\n'
                    f'   Email: {user.email}\n'
                    f'   Full Name: {user.first_name} {user.last_name}\n'
                    f'   User ID: {user.id}\n'
                    f'   Is Staff: {user.is_staff}\n'
                    f'   Is Superuser: {user.is_superuser}\n'
                    f'   Date Joined: {user.date_joined}\n'
                    f'   Last Login: {user.last_login or "Never"}\n'
                    f'   ---'
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error listing admin users: {str(e)}')
            )
