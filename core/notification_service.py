"""
Notification Service for managing notifications
"""
from django.utils import timezone
from django.db.models import Q
from core.models import Notification, Order, Livrable, User
from core.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for creating and managing notifications
    """
    
    @staticmethod
    def create_notification(user, notification_type, title, message, 
                          priority='medium', order=None, livrable=None, send_email=True):
        """
        Create and optionally send notification
        
        Args:
            user: User instance to receive notification
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, urgent)
            order: Related order (optional)
            livrable: Related deliverable (optional)
            send_email: Whether to send email notification
        """
        try:
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                order=order,
                livrable=livrable
            )
            
            # Send email if requested and user has email
            if send_email and user.email:
                EmailService.send_notification_email(notification)
            
            logger.info(f"Notification created: {notification_type} for user {user.username}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {str(e)}")
            return None
    
    @staticmethod
    def notify_order_status_change(order, old_status, new_status, changed_by):
        """
        Notify relevant users about order status change
        
        Args:
            order: Order instance
            old_status: Previous status
            new_status: New status
            changed_by: User who made the change
        """
        notifications = []
        
        # Notify client
        if order.client and order.client.user.email:
            notification = NotificationService.create_notification(
                user=order.client.user,
                notification_type='order_status_changed',
                title=f'Order #{order.id} Status Updated',
                message=f'Your order status has been changed from {old_status.name} to {new_status.name}',
                priority='medium',
                order=order
            )
            if notification:
                notifications.append(notification)
        
        # Notify collaborator
        if order.collaborator and order.collaborator.user.email:
            notification = NotificationService.create_notification(
                user=order.collaborator.user,
                notification_type='order_status_changed',
                title=f'Order #{order.id} Status Updated',
                message=f'Order status has been changed from {old_status.name} to {new_status.name}',
                priority='medium',
                order=order
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_livrable_uploaded(livrable):
        """
        Notify client when collaborator uploads deliverable
        
        Args:
            livrable: Livrable instance
        """
        if livrable.order.client and livrable.order.client.user.email:
            return NotificationService.create_notification(
                user=livrable.order.client.user,
                notification_type='livrable_uploaded',
                title=f'New Deliverable Available - Order #{livrable.order.id}',
                message=f'A new deliverable "{livrable.name}" has been uploaded for your order.',
                priority='medium',
                order=livrable.order,
                livrable=livrable
            )
        return None
    
    @staticmethod
    def notify_livrable_reviewed(livrable):
        """
        Notify client when admin reviews deliverable
        
        Args:
            livrable: Livrable instance
        """
        if livrable.order.client and livrable.order.client.user.email:
            return NotificationService.create_notification(
                user=livrable.order.client.user,
                notification_type='livrable_reviewed',
                title=f'Deliverable Reviewed - Order #{livrable.order.id}',
                message=f'Your deliverable "{livrable.name}" has been reviewed and is ready for your approval.',
                priority='medium',
                order=livrable.order,
                livrable=livrable
            )
        return None
    
    @staticmethod
    def notify_livrable_accepted(livrable):
        """
        Notify collaborator when client accepts deliverable
        
        Args:
            livrable: Livrable instance
        """
        if livrable.order.collaborator and livrable.order.collaborator.user.email:
            return NotificationService.create_notification(
                user=livrable.order.collaborator.user,
                notification_type='livrable_accepted',
                title=f'Deliverable Accepted - Order #{livrable.order.id}',
                message=f'Your deliverable "{livrable.name}" has been accepted by the client.',
                priority='medium',
                order=livrable.order,
                livrable=livrable
            )
        return None
    
    @staticmethod
    def notify_livrable_rejected(livrable):
        """
        Notify collaborator when client rejects deliverable
        
        Args:
            livrable: Livrable instance
        """
        if livrable.order.collaborator and livrable.order.collaborator.user.email:
            return NotificationService.create_notification(
                user=livrable.order.collaborator.user,
                notification_type='livrable_rejected',
                title=f'Deliverable Rejected - Order #{livrable.order.id}',
                message=f'Your deliverable "{livrable.name}" has been rejected by the client. Please review and resubmit.',
                priority='high',
                order=livrable.order,
                livrable=livrable
            )
        return None
    
    @staticmethod
    def notify_order_completed(order):
        """
        Notify client and collaborator when order is completed
        
        Args:
            order: Order instance
        """
        notifications = []
        
        # Notify client
        if order.client and order.client.user.email:
            notification = NotificationService.create_notification(
                user=order.client.user,
                notification_type='order_completed',
                title=f'Order #{order.id} Completed',
                message=f'Your order has been completed successfully. Please review and rate the service.',
                priority='medium',
                order=order
            )
            if notification:
                notifications.append(notification)
        
        # Notify collaborator
        if order.collaborator and order.collaborator.user.email:
            notification = NotificationService.create_notification(
                user=order.collaborator.user,
                notification_type='order_completed',
                title=f'Order #{order.id} Completed',
                message=f'Congratulations! Your order has been completed successfully.',
                priority='medium',
                order=order
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_payment_reminder(order, days_overdue=0):
        """
        Notify client about payment reminder
        
        Args:
            order: Order instance
            days_overdue: Number of days payment is overdue
        """
        if order.client and order.client.user.email:
            if days_overdue > 0:
                title = f'Payment Overdue - Order #{order.id}'
                message = f'Your payment for Order #{order.id} is {days_overdue} days overdue. Please make payment to avoid service interruption.'
                priority = 'high'
            else:
                title = f'Payment Reminder - Order #{order.id}'
                message = f'Reminder: Payment is due for Order #{order.id}. Please make payment to continue service.'
                priority = 'medium'
            
            return NotificationService.create_notification(
                user=order.client.user,
                notification_type='payment_reminder',
                title=title,
                message=message,
                priority=priority,
                order=order
            )
        return None
    
    @staticmethod
    def notify_deadline_reminder(order, hours_remaining=24):
        """
        Notify collaborator about deadline reminder
        
        Args:
            order: Order instance
            hours_remaining: Hours until deadline
        """
        if order.collaborator and order.collaborator.user.email:
            if hours_remaining <= 24:
                title = f'Deadline Approaching - Order #{order.id}'
                message = f'Order #{order.id} deadline is approaching. Please ensure timely completion.'
                priority = 'high'
            else:
                title = f'Deadline Reminder - Order #{order.id}'
                message = f'Reminder: Order #{order.id} deadline is in {hours_remaining} hours.'
                priority = 'medium'
            
            return NotificationService.create_notification(
                user=order.collaborator.user,
                notification_type='deadline_reminder',
                title=title,
                message=message,
                priority=priority,
                order=order
            )
        return None
    
    @staticmethod
    def notify_review_reminder(order):
        """
        Notify client to leave review after order completion
        
        Args:
            order: Order instance
        """
        if order.client and order.client.user.email:
            return NotificationService.create_notification(
                user=order.client.user,
                notification_type='review_reminder',
                title=f'Please Review Your Service - Order #{order.id}',
                message=f'Your order has been completed. Please take a moment to review the service quality.',
                priority='low',
                order=order
            )
        return None
    
    @staticmethod
    def notify_user_blacklisted(user, reason=""):
        """
        Notify user when they are blacklisted
        
        Args:
            user: User instance
            reason: Reason for blacklisting
        """
        return NotificationService.create_notification(
            user=user,
            notification_type='user_blacklisted',
            title='Account Status Update',
            message=f'Your account has been restricted. Reason: {reason}' if reason else 'Your account has been restricted.',
            priority='urgent',
            send_email=True
        )
    
    @staticmethod
    def get_user_notifications(user, unread_only=False, limit=None):
        """
        Get notifications for a user
        
        Args:
            user: User instance
            unread_only: Whether to return only unread notifications
            limit: Maximum number of notifications to return
        """
        queryset = Notification.objects.filter(user=user)
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def mark_notification_as_read(notification_id, user):
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            user: User instance
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return notification
        except Notification.DoesNotExist:
            return None
    
    @staticmethod
    def mark_all_notifications_as_read(user):
        """
        Mark all notifications as read for a user
        
        Args:
            user: User instance
        """
        return Notification.objects.filter(user=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @staticmethod
    def get_notification_stats(user):
        """
        Get notification statistics for a user
        
        Args:
            user: User instance
        """
        total = Notification.objects.filter(user=user).count()
        unread = Notification.objects.filter(user=user, is_read=False).count()
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread
        }
