"""
Tests for Livrable API endpoints
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from core.models import (
    Service, Order, Status, Livrable, Review, 
    Client, Collaborator, Admin
)

User = get_user_model()


class LivrableAPITestCase(APITestCase):
    """Test cases for Livrable API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        self.admin = Admin.objects.create(user=self.admin_user)
        
        self.collaborator_user = User.objects.create_user(
            username='collaborator',
            email='collaborator@test.com',
            password='collab123',
            first_name='John',
            last_name='Doe'
        )
        self.collaborator = Collaborator.objects.create(
            user=self.collaborator_user,
            is_active=True
        )
        
        self.client_user = User.objects.create_user(
            username='client',
            email='client@test.com',
            password='client123',
            first_name='Jane',
            last_name='Smith'
        )
        self.client_profile = Client.objects.create(user=self.client_user)
        
        # Create service
        self.service = Service.objects.create(
            name='Web Development',
            description='Professional web development',
            tool_name='React, Django',
            is_active=True
        )
        
        # Create status
        self.completed_status = Status.objects.create(name='completed')
        self.in_progress_status = Status.objects.create(name='in_progress')
        
        # Create order
        self.order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.completed_status,
            collaborator=self.collaborator,
            total_price=Decimal('1000.00'),
            advance_payment=Decimal('500.00'),
            quotation='Test order'
        )
        
        # Create livrable
        self.livrable = Livrable.objects.create(
            order=self.order,
            name='Test Website',
            description='A test website deliverable',
            is_accepted=False,
            is_reviewed_by_admin=False
        )
        
        # Create tokens
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.collaborator_token = Token.objects.create(user=self.collaborator_user)
        self.client_token = Token.objects.create(user=self.client_user)


class CollaboratorLivrableTests(LivrableAPITestCase):
    """Test collaborator livrable endpoints"""
    
    def test_collaborator_list_livrables(self):
        """Test collaborator can list their livrables"""
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Website')
    
    def test_collaborator_create_livrable(self):
        """Test collaborator can create livrable"""
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': self.order.id,
            'name': 'New Website',
            'description': 'A new website deliverable',
            'file_path': None
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Website')
        self.assertTrue(Livrable.objects.filter(name='New Website').exists())
    
    def test_collaborator_create_livrable_with_file(self):
        """Test collaborator can create livrable with file upload"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        data = {
            'order': self.order.id,
            'name': 'Website with File',
            'description': 'A website deliverable with attached file',
            'file_path': test_file
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Website with File')
        self.assertIsNotNone(response.data['file_url'])
        self.assertTrue(Livrable.objects.filter(name='Website with File').exists())
    
    def test_livrable_file_download(self):
        """Test file download endpoint"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a livrable with file
        test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        livrable = Livrable.objects.create(
            order=self.order,
            name='Test File Livrable',
            description='Test file',
            file_path=test_file
        )
        
        # Test collaborator can download their own file
        url = reverse('core:livrable-file-download', kwargs={'pk': livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_collaborator_cannot_create_livrable_for_unassigned_order(self):
        """Test collaborator cannot create livrable for order not assigned to them"""
        # Create another collaborator and order
        other_collaborator_user = User.objects.create_user(
            username='other_collab',
            email='other@test.com',
            password='other123'
        )
        other_collaborator = Collaborator.objects.create(
            user=other_collaborator_user,
            is_active=True
        )
        
        other_order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.in_progress_status,
            collaborator=other_collaborator,
            total_price=Decimal('2000.00'),
            advance_payment=Decimal('1000.00'),
            quotation='Other order'
        )
        
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': other_order.id,
            'name': 'Unauthorized Website',
            'description': 'Should not be created'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You can only create livrables for orders assigned to you', str(response.data))
    
    def test_collaborator_retrieve_livrable(self):
        """Test collaborator can retrieve their livrable"""
        url = reverse('core:collaborator-livrable-detail', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Website')
    
    def test_collaborator_update_livrable(self):
        """Test collaborator can update their livrable"""
        url = reverse('core:collaborator-livrable-detail', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': self.order.id,
            'name': 'Updated Website',
            'description': 'Updated description'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Website')
        
        # Verify in database
        self.livrable.refresh_from_db()
        self.assertEqual(self.livrable.name, 'Updated Website')
    
    def test_collaborator_delete_livrable(self):
        """Test collaborator can delete their livrable"""
        url = reverse('core:collaborator-livrable-detail', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Livrable.objects.filter(id=self.livrable.id).exists())
    
    def test_unauthorized_access_to_collaborator_endpoints(self):
        """Test that non-collaborators cannot access collaborator endpoints"""
        url = reverse('core:collaborator-livrables-list-create')
        
        # Test with client token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminLivrableTests(LivrableAPITestCase):
    """Test admin livrable endpoints"""
    
    def test_admin_list_livrables(self):
        """Test admin can list all completed livrables"""
        url = reverse('core:admin-livrables-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Website')
    
    def test_admin_retrieve_livrable(self):
        """Test admin can retrieve specific livrable"""
        url = reverse('core:admin-livrable-detail', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Website')
        self.assertEqual(response.data['client_name'], 'Jane Smith')
        self.assertEqual(response.data['collaborator_name'], 'John Doe')
    
    def test_admin_only_sees_completed_livrables(self):
        """Test admin only sees livrables from completed orders"""
        # Create order with in-progress status
        in_progress_order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.in_progress_status,
            collaborator=self.collaborator,
            total_price=Decimal('1500.00'),
            advance_payment=Decimal('750.00'),
            quotation='In progress order'
        )
        
        # Create livrable for in-progress order
        Livrable.objects.create(
            order=in_progress_order,
            name='In Progress Website',
            description='Should not appear in admin list'
        )
        
        url = reverse('core:admin-livrables-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only completed order's livrable
        self.assertEqual(response.data[0]['name'], 'Test Website')
    
    def test_admin_mark_livrable_as_reviewed(self):
        """Test admin can mark livrable as reviewed"""
        url = reverse('core:admin-livrable-review', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        data = {'is_reviewed_by_admin': True}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_reviewed_by_admin'])
        
        # Verify in database
        self.livrable.refresh_from_db()
        self.assertTrue(self.livrable.is_reviewed_by_admin)
    
    def test_admin_unmark_livrable_as_reviewed(self):
        """Test admin can unmark livrable as reviewed"""
        # First mark as reviewed
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        url = reverse('core:admin-livrable-review', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        
        data = {'is_reviewed_by_admin': False}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_reviewed_by_admin'])
        
        # Verify in database
        self.livrable.refresh_from_db()
        self.assertFalse(self.livrable.is_reviewed_by_admin)
    
    def test_unauthorized_access_to_admin_endpoints(self):
        """Test that non-admins cannot access admin endpoints"""
        url = reverse('core:admin-livrables-list')
        
        # Test with collaborator token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with client token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ClientLivrableTests(LivrableAPITestCase):
    """Test client livrable endpoints"""
    
    def test_client_list_livrables(self):
        """Test client can list their completed and reviewed livrables"""
        # First mark the livrable as reviewed by admin
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        url = reverse('core:client-livrables-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Website')
    
    def test_client_cannot_see_unreviewed_livrables(self):
        """Test client cannot see completed livrables that haven't been reviewed by admin"""
        # Ensure livrable is not reviewed by admin
        self.livrable.is_reviewed_by_admin = False
        self.livrable.save()
        
        url = reverse('core:client-livrables-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No livrables should be visible
    
    def test_client_only_sees_their_completed_and_reviewed_livrables(self):
        """Test client only sees livrables from their completed orders that are reviewed"""
        # Mark current livrable as reviewed
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        # Create another client
        other_client_user = User.objects.create_user(
            username='other_client',
            email='other_client@test.com',
            password='other123'
        )
        other_client = Client.objects.create(user=other_client_user)
        
        # Create order for other client
        other_order = Order.objects.create(
            client=other_client,
            service=self.service,
            status=self.completed_status,
            collaborator=self.collaborator,
            total_price=Decimal('2000.00'),
            advance_payment=Decimal('1000.00'),
            quotation='Other client order'
        )
        
        # Create livrable for other client (reviewed)
        other_livrable = Livrable.objects.create(
            order=other_order,
            name='Other Client Website',
            description='Should not appear in current client list',
            is_reviewed_by_admin=True
        )
        
        url = reverse('core:client-livrables-list')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only current client's livrable
        self.assertEqual(response.data[0]['name'], 'Test Website')
    
    def test_client_accept_livrable(self):
        """Test client can accept a reviewed livrable"""
        # First mark as reviewed by admin
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': True}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_accepted'])
        
        # Verify in database
        self.livrable.refresh_from_db()
        self.assertTrue(self.livrable.is_accepted)
    
    def test_client_reject_livrable(self):
        """Test client can reject a reviewed livrable"""
        # First mark as reviewed by admin and accept it
        self.livrable.is_reviewed_by_admin = True
        self.livrable.is_accepted = True
        self.livrable.save()
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': False}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_accepted'])
        
        # Verify in database
        self.livrable.refresh_from_db()
        self.assertFalse(self.livrable.is_accepted)
    
    def test_client_cannot_accept_reject_other_client_livrable(self):
        """Test client cannot accept/reject livrables from other clients"""
        # Create another client and their order
        other_client_user = User.objects.create_user(
            username='other_client2',
            email='other_client2@test.com',
            password='other123'
        )
        other_client = Client.objects.create(user=other_client_user)
        
        other_order = Order.objects.create(
            client=other_client,
            service=self.service,
            status=self.completed_status,
            collaborator=self.collaborator,
            total_price=Decimal('2000.00'),
            advance_payment=Decimal('1000.00'),
            quotation='Other client order'
        )
        
        other_livrable = Livrable.objects.create(
            order=other_order,
            name='Other Client Website',
            description='Should not be accessible'
        )
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': other_livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': True}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_client_cannot_accept_reject_unreviewed_livrable(self):
        """Test client cannot accept/reject livrables that haven't been reviewed by admin"""
        # Ensure livrable is not reviewed by admin
        self.livrable.is_reviewed_by_admin = False
        self.livrable.save()
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': True}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthorized_access_to_client_endpoints(self):
        """Test that non-clients cannot access client endpoints"""
        url = reverse('core:client-livrables-list')
        
        # Test with collaborator token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_order_status_changes_to_completed_when_livrable_accepted(self):
        """Test that order status automatically changes to 'Completed' when livrable is accepted"""
        # First mark as reviewed by admin
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        # Ensure order is in 'under_review' status
        self.order.status = Status.objects.get(name='under_review')
        self.order.save()
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': True}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_accepted'])
        
        # Verify livrable is accepted
        self.livrable.refresh_from_db()
        self.assertTrue(self.livrable.is_accepted)
        
        # Verify order status changed to 'Completed'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, 'Completed')
    
    def test_order_status_does_not_change_when_livrable_rejected(self):
        """Test that order status does not change when livrable is rejected"""
        # First mark as reviewed by admin
        self.livrable.is_reviewed_by_admin = True
        self.livrable.save()
        
        # Ensure order is in 'under_review' status
        self.order.status = Status.objects.get(name='under_review')
        self.order.save()
        
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': False}
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_accepted'])
        
        # Verify livrable is rejected
        self.livrable.refresh_from_db()
        self.assertFalse(self.livrable.is_accepted)
        
        # Verify order status remains 'under_review'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, 'under_review')

    def test_order_status_changes_to_under_review_when_livrable_created(self):
        """Test that order status automatically changes to 'under_review' when collaborator creates a livrable"""
        # Ensure order starts with 'in_progress' status
        in_progress_status = Status.objects.get(name='in_progress')
        self.order.status = in_progress_status
        self.order.save()
        
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': self.order.id,
            'name': 'New Deliverable',
            'description': 'A new deliverable that should trigger status change'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify livrable was created
        self.assertTrue(Livrable.objects.filter(name='New Deliverable').exists())
        
        # Verify order status changed to 'under_review'
        self.order.refresh_from_db()
        self.assertEqual(self.order.status.name, 'under_review')
        
        # Verify status history was created
        status_history = OrderStatusHistory.objects.filter(
            order=self.order,
            status__name='under_review'
        ).first()
        self.assertIsNotNone(status_history)
        self.assertEqual(status_history.changed_by, self.collaborator_user)
        self.assertIn('New Deliverable', status_history.notes)


class LivrableValidationTests(LivrableAPITestCase):
    """Test livrable validation and edge cases"""
    
    def test_create_livrable_without_name(self):
        """Test creating livrable without name fails"""
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': self.order.id,
            'description': 'No name provided'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
    
    def test_create_livrable_with_empty_name(self):
        """Test creating livrable with empty name fails"""
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        data = {
            'order': self.order.id,
            'name': '   ',
            'description': 'Empty name'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
    
    def test_accept_reject_without_is_accepted_field(self):
        """Test accept/reject without is_accepted field fails"""
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {}  # Missing is_accepted field
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_accepted', response.data)
    
    def test_accept_reject_with_null_is_accepted(self):
        """Test accept/reject with null is_accepted fails"""
        url = reverse('core:client-livrable-accept-reject', kwargs={'pk': self.livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.client_token.key}')
        
        data = {'is_accepted': None}
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_accepted', response.data)


class LivrablePermissionsTests(LivrableAPITestCase):
    """Test livrable permissions and access control"""
    
    def test_inactive_collaborator_cannot_access_endpoints(self):
        """Test inactive collaborator cannot access livrable endpoints"""
        # Deactivate collaborator
        self.collaborator.is_active = False
        self.collaborator.save()
        
        url = reverse('core:collaborator-livrables-list-create')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_user_cannot_access_any_endpoint(self):
        """Test unauthenticated users cannot access any livrable endpoint"""
        endpoints = [
            'core:collaborator-livrables-list-create',
            'core:admin-livrables-list',
            'core:client-livrables-list'
        ]
        
        for endpoint in endpoints:
            url = reverse(endpoint)
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_collaborator_cannot_access_other_collaborator_livrables(self):
        """Test collaborator cannot access livrables from other collaborators"""
        # Create another collaborator and their order
        other_collaborator_user = User.objects.create_user(
            username='other_collab2',
            email='other_collab2@test.com',
            password='other123'
        )
        other_collaborator = Collaborator.objects.create(
            user=other_collaborator_user,
            is_active=True
        )
        
        other_order = Order.objects.create(
            client=self.client_profile,
            service=self.service,
            status=self.completed_status,
            collaborator=other_collaborator,
            total_price=Decimal('2000.00'),
            advance_payment=Decimal('1000.00'),
            quotation='Other collaborator order'
        )
        
        other_livrable = Livrable.objects.create(
            order=other_order,
            name='Other Collaborator Website',
            description='Should not be accessible'
        )
        
        # Try to access other collaborator's livrable
        url = reverse('core:collaborator-livrable-detail', kwargs={'pk': other_livrable.id})
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.collaborator_token.key}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)