"""
Django Management Command to seed database
Place this file in: core/management/commands/seed_data.py
Run with: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Admin, Collaborator, Client, Service, Status, 
    Order, Livrable, Review
)
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seeding...')

        # Clear existing data (optional - comment out if you don't want to clear)
        self.stdout.write('Clearing existing data...')
        Review.objects.all().delete()
        Livrable.objects.all().delete()
        Order.objects.all().delete()
        Status.objects.all().delete()
        Service.objects.all().delete()
        Client.objects.all().delete()
        Collaborator.objects.all().delete()
        Admin.objects.all().delete()
        User.objects.all().delete()

        # Create Statuses
        self.stdout.write('Creating statuses...')
        statuses = ['Pending', 'In Progress', 'Completed', 'Cancelled', 'On Hold']
        status_objects = {}
        for status_name in statuses:
            status = Status.objects.create(name=status_name)
            status_objects[status_name] = status
            self.stdout.write(f'  ✓ Created status: {status_name}')

        # Create Admin Users
        self.stdout.write('Creating admin users...')
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@sademiy.com',
            password='admin123',
            first_name='Super',
            last_name='Admin'
        )
        admin_user.phone = '+212600000001'
        admin_user.save()
        Admin.objects.create(user=admin_user)
        self.stdout.write('  ✓ Created admin: admin (password: admin123)')

        # Create Collaborators
        self.stdout.write('Creating collaborators...')
        collab_data = [
            {'username': 'collaborator1', 'email': 'collab1@sademiy.com', 'first_name': 'Ahmed', 'last_name': 'Bennani', 'phone': '+212600000002'},
            {'username': 'collaborator2', 'email': 'collab2@sademiy.com', 'first_name': 'Fatima', 'last_name': 'Alaoui', 'phone': '+212600000003'},
        ]
        
        for data in collab_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='collab123',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            user.phone = data['phone']
            user.save()
            Collaborator.objects.create(user=user, is_active=True)
            self.stdout.write(f"  ✓ Created collaborator: {data['username']} (password: collab123)")

        # Create Clients
        self.stdout.write('Creating clients...')
        client_data = [
            {'username': 'client1', 'email': 'client1@example.com', 'first_name': 'Youssef', 'last_name': 'Tazi', 'phone': '+212600000004', 'city': 'Marrakesh'},
            {'username': 'client2', 'email': 'client2@example.com', 'first_name': 'Sara', 'last_name': 'Idrissi', 'phone': '+212600000005', 'city': 'Casablanca'},
            {'username': 'client3', 'email': 'client3@example.com', 'first_name': 'Omar', 'last_name': 'Benjelloun', 'phone': '+212600000006', 'city': 'Rabat'},
            {'username': 'client4', 'email': 'client4@example.com', 'first_name': 'Leila', 'last_name': 'Chraibi', 'phone': '+212600000007', 'city': 'Marrakesh'},
        ]
        
        clients = []
        for data in client_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='client123',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            user.phone = data['phone']
            user.save()
            client = Client.objects.create(user=user, city=data['city'])
            clients.append(client)
            self.stdout.write(f"  ✓ Created client: {data['username']} (password: client123)")

        # Create Services
        self.stdout.write('Creating services...')
        service_data = [
            {
                'name': 'Web Development',
                'price': Decimal('5000.00'),
                'description': 'Professional web development services including responsive design, e-commerce solutions, and custom web applications.',
                'is_active': True,
                'last_name': 'Development'
            },
            {
                'name': 'Mobile App Development',
                'price': Decimal('8000.00'),
                'description': 'Native and cross-platform mobile application development for iOS and Android.',
                'is_active': True,
                'last_name': 'Development'
            },
            {
                'name': 'Digital Marketing',
                'price': Decimal('3000.00'),
                'description': 'Complete digital marketing services including SEO, social media management, and content marketing.',
                'is_active': True,
                'last_name': 'Marketing'
            },
            {
                'name': 'Graphic Design',
                'price': Decimal('2000.00'),
                'description': 'Professional graphic design services for logos, branding, and marketing materials.',
                'is_active': True,
                'last_name': 'Design'
            },
            {
                'name': 'Video Production',
                'price': Decimal('4500.00'),
                'description': 'High-quality video production services for commercials, corporate videos, and promotional content.',
                'is_active': True,
                'last_name': 'Media'
            },
            {
                'name': 'Legacy Service',
                'price': Decimal('1500.00'),
                'description': 'This service is no longer active.',
                'is_active': False,
                'last_name': 'Deprecated'
            },
        ]
        
        services = []
        for data in service_data:
            service = Service.objects.create(**data)
            services.append(service)
            status_text = "✓ Active" if data['is_active'] else "✗ Inactive"
            self.stdout.write(f"  {status_text} Created service: {data['name']}")

        # Create Orders
        self.stdout.write('Creating orders...')
        orders = []
        
        # Order 1: Completed
        order1 = Order.objects.create(
            client=clients[0],
            service=services[0],  # Web Development
            status=status_objects['Completed'],
            deadline_date=timezone.now() + timedelta(days=30),
            total_price=Decimal('5000.00'),
            advance_payment=Decimal('5000.00'),
            discount=Decimal('0.00'),
            quotation='Complete e-commerce website with payment integration',
            comment='Client satisfied with the delivery'
        )
        orders.append(order1)
        
        # Order 2: In Progress
        order2 = Order.objects.create(
            client=clients[1],
            service=services[1],  # Mobile App
            status=status_objects['In Progress'],
            deadline_date=timezone.now() + timedelta(days=45),
            total_price=Decimal('8000.00'),
            advance_payment=Decimal('4000.00'),
            discount=Decimal('5.00'),
            quotation='iOS and Android mobile app for fitness tracking',
            comment='Development is on schedule'
        )
        orders.append(order2)
        
        # Order 3: Completed
        order3 = Order.objects.create(
            client=clients[2],
            service=services[2],  # Digital Marketing
            status=status_objects['Completed'],
            deadline_date=timezone.now() + timedelta(days=15),
            total_price=Decimal('3000.00'),
            advance_payment=Decimal('3000.00'),
            discount=Decimal('10.00'),
            quotation='3-month digital marketing campaign',
            comment='Campaign exceeded expectations'
        )
        orders.append(order3)
        
        # Order 4: Pending
        order4 = Order.objects.create(
            client=clients[3],
            service=services[3],  # Graphic Design
            status=status_objects['Pending'],
            deadline_date=timezone.now() + timedelta(days=20),
            total_price=Decimal('2000.00'),
            advance_payment=Decimal('500.00'),
            discount=Decimal('0.00'),
            quotation='Complete branding package with logo and marketing materials'
        )
        orders.append(order4)
        
        # Order 5: Completed
        order5 = Order.objects.create(
            client=clients[0],
            service=services[4],  # Video Production
            status=status_objects['Completed'],
            deadline_date=timezone.now() + timedelta(days=25),
            total_price=Decimal('4500.00'),
            advance_payment=Decimal('4500.00'),
            discount=Decimal('0.00'),
            quotation='Corporate promotional video - 3 minutes',
            comment='Excellent quality video delivered'
        )
        orders.append(order5)
        
        self.stdout.write(f'  ✓ Created {len(orders)} orders')

        # Create Livrables
        self.stdout.write('Creating livrables...')
        livrables = []
        
        # Livrables for Order 1 (Completed)
        livrable1 = Livrable.objects.create(
            order=order1,
            name='E-commerce Website Final Delivery',
            description='Complete website with all features implemented',
            is_accepted=True
        )
        livrables.append(livrable1)
        
        # Livrables for Order 2 (In Progress)
        livrable2 = Livrable.objects.create(
            order=order2,
            name='Mobile App Beta Version',
            description='Beta version for testing',
            is_accepted=False
        )
        livrables.append(livrable2)
        
        # Livrables for Order 3 (Completed)
        livrable3 = Livrable.objects.create(
            order=order3,
            name='Marketing Campaign Report',
            description='Complete analytics and campaign performance report',
            is_accepted=True
        )
        livrables.append(livrable3)
        
        # Livrables for Order 5 (Completed)
        livrable4 = Livrable.objects.create(
            order=order5,
            name='Corporate Video Final Cut',
            description='Final edited video in 4K resolution',
            is_accepted=True
        )
        livrables.append(livrable4)
        
        livrable5 = Livrable.objects.create(
            order=order1,
            name='Website Documentation',
            description='User manual and technical documentation',
            is_accepted=True
        )
        livrables.append(livrable5)
        
        self.stdout.write(f'  ✓ Created {len(livrables)} livrables')

        # Create Reviews
        self.stdout.write('Creating reviews...')
        reviews_data = [
            {
                'livrable': livrable1,
                'rating': 5,
                'comment': 'Outstanding work! The website exceeded our expectations. Professional, responsive, and delivered on time.'
            },
            {
                'livrable': livrable3,
                'rating': 5,
                'comment': 'The marketing campaign was incredibly successful. We saw a 200% increase in engagement!'
            },
            {
                'livrable': livrable4,
                'rating': 4,
                'comment': 'Great video quality and creative direction. Minor revisions needed but overall excellent work.'
            },
            {
                'livrable': livrable5,
                'rating': 5,
                'comment': 'Very detailed documentation. Makes it easy to maintain the website.'
            },
            {
                'livrable': livrable1,
                'rating': 5,
                'comment': 'Second review: After using the site for a month, we are very satisfied. Great support too!'
            },
        ]
        
        for review_data in reviews_data:
            Review.objects.create(**review_data)
            self.stdout.write(f"  ✓ Created review for {review_data['livrable'].name} - {review_data['rating']} stars")

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\nCreated:')
        self.stdout.write(f'  • {User.objects.count()} Users')
        self.stdout.write(f'  • {Admin.objects.count()} Admins')
        self.stdout.write(f'  • {Collaborator.objects.count()} Collaborators')
        self.stdout.write(f'  • {Client.objects.count()} Clients')
        self.stdout.write(f'  • {Service.objects.count()} Services ({Service.objects.filter(is_active=True).count()} active)')
        self.stdout.write(f'  • {Status.objects.count()} Statuses')
        self.stdout.write(f'  • {Order.objects.count()} Orders')
        self.stdout.write(f'  • {Livrable.objects.count()} Livrables')
        self.stdout.write(f'  • {Review.objects.count()} Reviews')
        
        self.stdout.write('\nTest Credentials:')
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  Collaborator: username=collaborator1, password=collab123')
        self.stdout.write('  Client: username=client1, password=client123')
        self.stdout.write('  (Phone login also available with phone number)')