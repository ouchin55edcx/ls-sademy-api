from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model

from core.models import (
    Admin,
    Client,
    Collaborator,
    GlobalSettings,
    Order,
    Service,
    ServiceCollaboratorCommission,
    Status,
)
from core.views import AdminRevenueSummaryAPIView, CollaboratorRevenueSummaryAPIView


class CommissionCalculationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_user(
            username='admin-user', password='testpass'
        )
        Admin.objects.create(user=self.admin_user)

        self.client_user = user_model.objects.create_user(
            username='client-user', password='testpass'
        )
        self.collaborator_user = user_model.objects.create_user(
            username='collab-user', password='testpass'
        )

        self.client_profile = Client.objects.create(user=self.client_user)
        self.collaborator_profile = Collaborator.objects.create(user=self.collaborator_user)

        self.status_completed = Status.objects.create(name='completed')
        self.status_in_progress = Status.objects.create(name='in_progress')
        self.status_pending = Status.objects.create(name='pending')

        self.service = Service.objects.create(name='Service A', is_active=True)

        self.settings = GlobalSettings.get_settings()
        self.settings.commission_type = 'percentage'
        self.settings.commission_value = Decimal('20.00')
        self.settings.is_commission_enabled = True
        self.settings.collaborator_commission_type = 'percentage'
        self.settings.collaborator_commission_value = Decimal('60.00')
        self.settings.is_collaborator_commission_enabled = True
        self.settings.save()

        self.order_completed = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.status_completed,
            collaborator=self.collaborator_profile,
            deadline_date=timezone.now(),
            total_price=Decimal('1000.00'),
            advance_payment=Decimal('0.00'),
        )
        self.order_completed.apply_global_commission_settings()
        self.order_completed.apply_collaborator_commission_settings()
        self.order_completed.save()

        self.order_in_progress = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.status_in_progress,
            collaborator=self.collaborator_profile,
            deadline_date=timezone.now(),
            total_price=Decimal('500.00'),
            advance_payment=Decimal('0.00'),
        )
        self.order_in_progress.apply_global_commission_settings()
        self.order_in_progress.apply_collaborator_commission_settings()
        self.order_in_progress.save()

        self.factory = APIRequestFactory()

    def test_global_collaborator_commission_applied(self):
        self.order_completed.refresh_from_db()
        self.assertEqual(self.order_completed.collaborator_commission_type, 'percentage')
        self.assertEqual(self.order_completed.collaborator_commission_value, Decimal('60.00'))
        self.assertEqual(self.order_completed.collaborator_commission_amount, Decimal('600.00'))

    def test_service_override_commission_applied(self):
        ServiceCollaboratorCommission.objects.create(
            service=self.service,
            commission_type='fixed',
            commission_value=Decimal('100.00'),
        )

        override_order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.status_pending,
            collaborator=self.collaborator_profile,
            deadline_date=timezone.now(),
            total_price=Decimal('750.00'),
            advance_payment=Decimal('0.00'),
        )
        override_order.apply_collaborator_commission_settings()

        self.assertEqual(override_order.collaborator_commission_type, 'fixed')
        self.assertEqual(override_order.collaborator_commission_value, Decimal('100.00'))
        self.assertEqual(override_order.collaborator_commission_amount, Decimal('100.00'))

    def test_admin_revenue_summary_view(self):
        request = self.factory.get('/api/admin/revenue-summary/')
        force_authenticate(request, user=self.admin_user)
        response = AdminRevenueSummaryAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        summary = response.data['summary']
        self.assertEqual(summary['gross_revenue'], '1500.00')
        self.assertEqual(summary['collaborator_payouts'], '900.00')
        self.assertEqual(summary['sademy_commission'], '300.00')
        self.assertEqual(summary['platform_net_revenue'], '600.00')

    def test_collaborator_revenue_summary_view(self):
        request = self.factory.get('/api/collaborator/revenue/')
        force_authenticate(request, user=self.collaborator_user)
        response = CollaboratorRevenueSummaryAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        summary = response.data['summary']
        self.assertEqual(summary['completed_orders'], 1)
        self.assertEqual(summary['in_progress_orders'], 1)
        self.assertEqual(summary['completed_payout'], '600.00')
        self.assertEqual(summary['projected_payout'], '900.00')

