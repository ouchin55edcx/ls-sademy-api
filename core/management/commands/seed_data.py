"""
Django Management Command to seed database
Place this file in: core/management/commands/seed_data.py
Run with: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import (
    Admin, Collaborator, Client, Service, Template, Status, 
    Order, Livrable, Review, Language, Notification
)
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database seeding...')

        # Skip clearing existing data to avoid foreign key constraints
        self.stdout.write('Skipping data clearing to avoid foreign key constraints...')

        # Create Languages
        self.stdout.write('Creating languages...')
        languages_data = [
            {'code': 'en', 'name': 'English', 'is_active': True},
            {'code': 'fr', 'name': 'French', 'is_active': True},
            {'code': 'ar', 'name': 'Arabic', 'is_active': True},
            {'code': 'es', 'name': 'Spanish', 'is_active': True},
        ]
        
        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults=lang_data
            )
            if created:
                self.stdout.write(f'  ✓ Created language: {language.name}')
            else:
                self.stdout.write(f'  ℹ️  Language already exists: {language.name}')

        # Create Statuses
        self.stdout.write('Creating statuses...')
        statuses = ['pending', 'confirmed', 'in_progress', 'under_review', 'completed', 'cancelled']
        status_objects = {}
        for status_name in statuses:
            status, created = Status.objects.get_or_create(name=status_name)
            status_objects[status_name] = status
            if created:
                self.stdout.write(f'  ✓ Created status: {status_name}')
            else:
                self.stdout.write(f'  ℹ️  Status already exists: {status_name}')

        # Create Admin Users
        self.stdout.write('Creating admin users...')
        try:
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@sademiy.com',
                    'first_name': 'Super',
                    'last_name': 'Admin',
                    'phone': '+212600000001',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                Admin.objects.create(user=admin_user)
                self.stdout.write('  ✓ Created admin: admin (password: admin123)')
            else:
                self.stdout.write('  ℹ️  Admin user already exists: admin')
                # Make sure Admin profile exists
                Admin.objects.get_or_create(user=admin_user)
        except Exception as e:
            self.stdout.write(f'  ⚠️  Could not create admin user: {str(e)}')

        # Create Collaborators
        self.stdout.write('Creating collaborators...')
        collab_data = [
            {'username': 'collaborator1', 'email': 'collab1@sademiy.com', 'first_name': 'Ahmed', 'last_name': 'Bennani', 'phone': '+212600000002'},
            {'username': 'collaborator2', 'email': 'collab2@sademiy.com', 'first_name': 'Fatima', 'last_name': 'Alaoui', 'phone': '+212600000003'},
        ]
        
        for data in collab_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                }
            )
            if created:
                user.set_password('collab123')
                user.save()
                Collaborator.objects.create(user=user, is_active=True)
                self.stdout.write(f"  ✓ Created collaborator: {data['username']} (password: collab123)")
            else:
                self.stdout.write(f"  ℹ️  Collaborator already exists: {data['username']}")
                Collaborator.objects.get_or_create(user=user, defaults={'is_active': True})

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
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                }
            )
            if created:
                user.set_password('client123')
                user.save()
                client = Client.objects.create(user=user, city=data['city'])
                clients.append(client)
                self.stdout.write(f"  ✓ Created client: {data['username']} (password: client123)")
            else:
                self.stdout.write(f"  ℹ️  Client already exists: {data['username']}")
                client, _ = Client.objects.get_or_create(user=user, defaults={'city': data['city']})
                clients.append(client)

        # Create Services
        self.stdout.write('Creating services...')
        service_data = [
            {
                'name': 'Web Development',
                'description': 'Professional web development services including responsive design, e-commerce solutions, and custom web applications.',
                'is_active': True,
                'tool_name': 'React, Django, PostgreSQL'
            },
            {
                'name': 'Mobile App Development',
                'description': 'Native and cross-platform mobile application development for iOS and Android.',
                'is_active': True,
                'tool_name': 'React Native, Flutter, Swift'
            },
            {
                'name': 'Digital Marketing',
                'description': 'Complete digital marketing services including SEO, social media management, and content marketing.',
                'is_active': True,
                'tool_name': 'Google Analytics, SEMrush, Hootsuite'
            },
            {
                'name': 'Graphic Design',
                'description': 'Professional graphic design services for logos, branding, and marketing materials.',
                'is_active': True,
                'tool_name': 'Adobe Photoshop, Illustrator, Figma'
            },
            {
                'name': 'Video Production',
                'description': 'High-quality video production services for commercials, corporate videos, and promotional content.',
                'is_active': True,
                'tool_name': 'Adobe Premiere, After Effects, DaVinci Resolve'
            },
            {
                'name': 'Legacy Service',
                'description': 'This service is no longer active.',
                'is_active': False,
                'tool_name': ''
            },
        ]
        
        services = []
        for data in service_data:
            service = Service.objects.create(**data)
            services.append(service)
            status_text = "✓ Active" if data['is_active'] else "✗ Inactive"
            self.stdout.write(f"  {status_text} Created service: {data['name']}")

        # Create Templates
        self.stdout.write('Creating templates...')
        template_data = [
            # Web Development Templates
            {
                'service': services[0],  # Web Development
                'title': 'E-commerce Website Template',
                'description': 'Modern e-commerce template with shopping cart, payment integration, and product management.',
                'file': '/templates/web/ecommerce-template.zip',
                'demo_video': '/templates/demos/ecommerce-demo.mp4'
            },
            {
                'service': services[0],
                'title': 'Portfolio Website Template',
                'description': 'Clean and professional portfolio template for showcasing your work.',
                'file': '/templates/web/portfolio-template.zip',
                'demo_video': '/templates/demos/portfolio-demo.mp4'
            },
            {
                'service': services[0],
                'title': 'Corporate Website Template',
                'description': 'Professional corporate website template with CMS integration.',
                'file': '/templates/web/corporate-template.zip',
                'demo_video': '/templates/demos/corporate-demo.mp4'
            },
            # Mobile App Templates
            {
                'service': services[1],  # Mobile App Development
                'title': 'Food Delivery App Template',
                'description': 'Complete food delivery app template with order tracking and payments.',
                'file': '/templates/mobile/food-delivery-app.zip',
                'demo_video': '/templates/demos/food-app-demo.mp4'
            },
            {
                'service': services[1],
                'title': 'Fitness Tracker App Template',
                'description': 'Health and fitness tracking app with workout plans and progress monitoring.',
                'file': '/templates/mobile/fitness-app.zip',
                'demo_video': '/templates/demos/fitness-app-demo.mp4'
            },
            # Digital Marketing Templates
            {
                'service': services[2],  # Digital Marketing
                'title': 'Social Media Campaign Template',
                'description': 'Ready-to-use social media campaign templates for various platforms.',
                'file': '/templates/marketing/social-campaign.zip',
                'demo_video': '/templates/demos/social-campaign-demo.mp4'
            },
            {
                'service': services[2],
                'title': 'Email Marketing Template Pack',
                'description': 'Professional email marketing templates with high conversion rates.',
                'file': '/templates/marketing/email-templates.zip',
                'demo_video': '/templates/demos/email-templates-demo.mp4'
            },
            # Graphic Design Templates
            {
                'service': services[3],  # Graphic Design
                'title': 'Brand Identity Kit',
                'description': 'Complete brand identity kit with logo, business cards, and letterhead templates.',
                'file': '/templates/design/brand-identity.zip',
                'demo_video': '/templates/demos/brand-identity-demo.mp4'
            },
            {
                'service': services[3],
                'title': 'Marketing Materials Pack',
                'description': 'Professional marketing materials including flyers, brochures, and posters.',
                'file': '/templates/design/marketing-pack.zip',
                'demo_video': '/templates/demos/marketing-materials-demo.mp4'
            },
            # Video Production Templates
            {
                'service': services[4],  # Video Production
                'title': 'Corporate Video Template',
                'description': 'Professional corporate video template with motion graphics.',
                'file': '/templates/video/corporate-video.zip',
                'demo_video': '/templates/demos/corporate-video-demo.mp4'
            },
            {
                'service': services[4],
                'title': 'Product Promotion Video Template',
                'description': 'Engaging product promotion video template with animations.',
                'file': '/templates/video/product-promo.zip',
                'demo_video': '/templates/demos/product-promo-demo.mp4'
            },
        ]
        
        templates = []
        for data in template_data:
            template = Template.objects.create(**data)
            templates.append(template)
            self.stdout.write(f"  ✓ Created template: {data['title']} for {data['service'].name}")
        
        self.stdout.write(f'  ✓ Created {len(templates)} templates total')

        # Get collaborators for assignment
        collaborators = list(Collaborator.objects.filter(is_active=True))
        
        # Create Orders
        self.stdout.write('Creating orders...')
        orders = []
        
        # Order 1: Completed
        order1 = Order.objects.create(
            client=clients[0],
            service=services[0],  # Web Development
            status=status_objects['completed'],
            collaborator=collaborators[0] if collaborators else None,  # Assign to first collaborator
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
            status=status_objects['in_progress'],
            collaborator=collaborators[1] if len(collaborators) > 1 else collaborators[0] if collaborators else None,  # Assign to second collaborator
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
            status=status_objects['completed'],
            collaborator=collaborators[0] if collaborators else None,  # Assign to first collaborator
            deadline_date=timezone.now() + timedelta(days=15),
            total_price=Decimal('3000.00'),
            advance_payment=Decimal('3000.00'),
            discount=Decimal('10.00'),
            quotation='3-month digital marketing campaign',
            comment='Campaign exceeded expectations'
        )
        orders.append(order3)
        
        # Order 4: Pending (Unassigned)
        order4 = Order.objects.create(
            client=clients[3],
            service=services[3],  # Graphic Design
            status=status_objects['pending'],
            collaborator=None,  # Unassigned order
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
            status=status_objects['completed'],
            collaborator=collaborators[1] if len(collaborators) > 1 else collaborators[0] if collaborators else None,  # Assign to second collaborator
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
                'order': order1,
                'client': clients[0],
                'rating': 5,
                'comment': 'Outstanding work! The website exceeded our expectations. Professional, responsive, and delivered on time.'
            },
            {
                'order': order3,
                'client': clients[2],
                'rating': 5,
                'comment': 'The marketing campaign was incredibly successful. We saw a 200% increase in engagement!'
            },
            {
                'order': order5,
                'client': clients[0],
                'rating': 4,
                'comment': 'Great video quality and creative direction. Minor revisions needed but overall excellent work.'
            },
            {
                'order': order1,
                'client': clients[0],
                'rating': 5,
                'comment': 'Very detailed documentation. Makes it easy to maintain the website.'
            },
        ]
        
        for review_data in reviews_data:
            Review.objects.create(**review_data)
            self.stdout.write(f"  ✓ Created review for Order #{review_data['order'].id} - {review_data['rating']} stars")

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\nCreated:')
        self.stdout.write(f'  • {User.objects.count()} Users')
        self.stdout.write(f'  • {Admin.objects.count()} Admins')
        self.stdout.write(f'  • {Collaborator.objects.count()} Collaborators')
        self.stdout.write(f'  • {Client.objects.count()} Clients')
        self.stdout.write(f'  • {Language.objects.count()} Languages')
        self.stdout.write(f'  • {Service.objects.count()} Services ({Service.objects.filter(is_active=True).count()} active)')
        self.stdout.write(f'  • {Template.objects.count()} Templates')
        self.stdout.write(f'  • {Status.objects.count()} Statuses')
        self.stdout.write(f'  • {Order.objects.count()} Orders')
        self.stdout.write(f'  • {Livrable.objects.count()} Livrables')
        self.stdout.write(f'  • {Review.objects.count()} Reviews')
        
        self.stdout.write('\nTest Credentials:')
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  Collaborator: username=collaborator1, password=collab123')
        self.stdout.write('  Client: username=client1, password=client123')
        self.stdout.write('  (Phone login also available with phone number)')
        
        self.stdout.write('\nPublic Endpoints:')
        self.stdout.write('  GET /api/services/ - List all active services with templates count')
        self.stdout.write('  GET /api/services/{id}/ - Service details with templates and reviews')