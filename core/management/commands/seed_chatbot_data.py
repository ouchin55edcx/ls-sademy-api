"""
Management command to seed chatbot data
Run with: python manage.py seed_chatbot_data
"""

from django.core.management.base import BaseCommand
from core.models import Language, Service, Template, Status
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed chatbot data (languages, services, templates, statuses)'
    
    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding chatbot data...')
        
        # Create languages
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
                self.stdout.write(f'✅ Created language: {language.name}')
            else:
                self.stdout.write(f'ℹ️  Language already exists: {language.name}')
        
        # Create statuses
        statuses_data = [
            {'name': 'Pending'},
            {'name': 'In Progress'},
            {'name': 'Completed'},
            {'name': 'Cancelled'},
        ]
        
        for status_data in statuses_data:
            status, created = Status.objects.get_or_create(
                name=status_data['name']
            )
            if created:
                self.stdout.write(f'✅ Created status: {status.name}')
            else:
                self.stdout.write(f'ℹ️  Status already exists: {status.name}')
        
        # Create services
        services_data = [
            {
                'name': 'Web Development',
                'description': 'Professional web development services including frontend, backend, and full-stack solutions',
                'tool_name': 'React, Node.js, Django',
                'is_active': True
            },
            {
                'name': 'Mobile App Development',
                'description': 'Native and cross-platform mobile application development',
                'tool_name': 'React Native, Flutter',
                'is_active': True
            },
            {
                'name': 'UI/UX Design',
                'description': 'User interface and user experience design services',
                'tool_name': 'Figma, Adobe XD, Sketch',
                'is_active': True
            },
            {
                'name': 'Data Analysis',
                'description': 'Data analysis and visualization services',
                'tool_name': 'Python, R, Tableau',
                'is_active': True
            },
            {
                'name': 'Digital Marketing',
                'description': 'Digital marketing and SEO services',
                'tool_name': 'Google Analytics, Facebook Ads',
                'is_active': True
            }
        ]
        
        for service_data in services_data:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            if created:
                self.stdout.write(f'✅ Created service: {service.name}')
            else:
                self.stdout.write(f'ℹ️  Service already exists: {service.name}')
        
        # Create templates for services
        templates_data = [
            # Web Development templates
            {
                'service_name': 'Web Development',
                'title': 'E-commerce Website',
                'description': 'Complete e-commerce solution with shopping cart, payment integration, and admin panel'
            },
            {
                'service_name': 'Web Development',
                'title': 'Corporate Website',
                'description': 'Professional corporate website with company information, services, and contact forms'
            },
            {
                'service_name': 'Web Development',
                'title': 'Portfolio Website',
                'description': 'Personal or business portfolio website to showcase work and projects'
            },
            # Mobile App Development templates
            {
                'service_name': 'Mobile App Development',
                'title': 'E-commerce Mobile App',
                'description': 'Mobile application for e-commerce with product catalog, cart, and payment features'
            },
            {
                'service_name': 'Mobile App Development',
                'title': 'Social Media App',
                'description': 'Social networking application with user profiles, posts, and messaging'
            },
            # UI/UX Design templates
            {
                'service_name': 'UI/UX Design',
                'title': 'Website Design',
                'description': 'Complete website design including wireframes, mockups, and style guides'
            },
            {
                'service_name': 'UI/UX Design',
                'title': 'Mobile App Design',
                'description': 'Mobile application design with user interface and user experience optimization'
            },
            # Data Analysis templates
            {
                'service_name': 'Data Analysis',
                'title': 'Business Intelligence Dashboard',
                'description': 'Interactive dashboard for business data visualization and analysis'
            },
            {
                'service_name': 'Data Analysis',
                'title': 'Market Research Report',
                'description': 'Comprehensive market research analysis with data visualization and insights'
            },
            # Digital Marketing templates
            {
                'service_name': 'Digital Marketing',
                'title': 'SEO Campaign',
                'description': 'Search engine optimization campaign to improve website visibility and rankings'
            },
            {
                'service_name': 'Digital Marketing',
                'title': 'Social Media Strategy',
                'description': 'Complete social media marketing strategy and content planning'
            }
        ]
        
        for template_data in templates_data:
            try:
                service = Service.objects.get(name=template_data['service_name'])
                template, created = Template.objects.get_or_create(
                    service=service,
                    title=template_data['title'],
                    defaults={'description': template_data['description']}
                )
                if created:
                    self.stdout.write(f'✅ Created template: {template.title} for {service.name}')
                else:
                    self.stdout.write(f'ℹ️  Template already exists: {template.title}')
            except Service.DoesNotExist:
                self.stdout.write(f'❌ Service not found: {template_data["service_name"]}')
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Chatbot data seeding completed successfully!')
        )
        self.stdout.write('📊 Summary:')
        self.stdout.write(f'   - Languages: {Language.objects.count()}')
        self.stdout.write(f'   - Services: {Service.objects.count()}')
        self.stdout.write(f'   - Templates: {Template.objects.count()}')
        self.stdout.write(f'   - Statuses: {Status.objects.count()}')
