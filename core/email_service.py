"""
Email service for sending notifications
"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails with HTML templates
    """
    
    @staticmethod
    def send_order_assignment_email(order, collaborator):
        """
        Send email notification to collaborator when assigned to an order
        
        Args:
            order: Order instance
            collaborator: Collaborator instance
        """
        try:
            # Prepare email context
            context = {
                'order': order,
                'collaborator': collaborator,
                'client': order.client,
                'service': order.service,
                'status': order.status,
                'deadline_date': order.deadline_date,
                'total_price': order.total_price,
                'advance_payment': order.advance_payment,
                'remaining_payment': order.remaining_payment,
                'quotation': order.quotation,
                'lecture': order.lecture,
                'comment': order.comment,
            }
            
            # Render HTML template
            html_content = render_to_string('emails/order_assignment.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"New Order Assignment - Order #{order.id}"
            from_email = settings.EMAIL_FROM
            to_email = [collaborator.user.email]
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            logger.info(f"Order assignment email sent successfully to {collaborator.user.email} for order #{order.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order assignment email: {str(e)}")
            return False
    
    @staticmethod
    def send_order_cancellation_email(order, collaborator, cancellation_reason=""):
        """
        Send email notification to collaborator when an order is cancelled
        
        Args:
            order: Order instance
            collaborator: Collaborator instance
            cancellation_reason: Reason for cancellation (optional)
        """
        try:
            # Prepare email context
            context = {
                'order': order,
                'collaborator': collaborator,
                'client': order.client,
                'service': order.service,
                'status': order.status,
                'deadline_date': order.deadline_date,
                'total_price': order.total_price,
                'advance_payment': order.advance_payment,
                'remaining_payment': order.remaining_payment,
                'quotation': order.quotation,
                'lecture': order.lecture,
                'comment': order.comment,
                'cancellation_reason': cancellation_reason,
            }
            
            # Render HTML template
            html_content = render_to_string('emails/order_cancellation.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Order Cancelled - Order #{order.id}"
            from_email = settings.EMAIL_FROM
            to_email = [collaborator.user.email]
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            logger.info(f"Order cancellation email sent successfully to {collaborator.user.email} for order #{order.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order cancellation email: {str(e)}")
            return False
    
    @staticmethod
    def send_livrable_reviewed_email(livrable, client):
        """
        Send email notification to client when a livrable is reviewed by admin
        
        Args:
            livrable: Livrable instance
            client: Client instance
        """
        try:
            # Prepare email context
            context = {
                'livrable': livrable,
                'client': client,
                'order': livrable.order,
                'service': livrable.order.service,
                'collaborator': livrable.order.collaborator,
                'deadline_date': livrable.order.deadline_date,
                'total_price': livrable.order.total_price,
                'advance_payment': livrable.order.advance_payment,
                'remaining_payment': livrable.order.remaining_payment,
            }
            
            # Render HTML template
            html_content = render_to_string('emails/livrable_reviewed.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Your Order #{livrable.order.id} is Ready for Review - {livrable.name}"
            from_email = settings.EMAIL_FROM
            to_email = [client.user.email]
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            logger.info(f"Livrable reviewed email sent successfully to {client.user.email} for livrable #{livrable.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send livrable reviewed email: {str(e)}")
            return False
    
    @staticmethod
    def send_collaborator_account_created_email(user, password):
        """
        Send email notification to new collaborator with login credentials
        
        Args:
            user: User instance
            password: Generated password for the user
        """
        try:
            # Prepare email context
            context = {
                'user': user,
                'password': password,
            }
            
            # Render HTML template
            html_content = render_to_string('emails/collaborator_account_created.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Welcome to Sademiy - Your Collaborator Account Has Been Created"
            from_email = settings.EMAIL_FROM
            to_email = [user.email]
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            logger.info(f"Collaborator account creation email sent successfully to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send collaborator account creation email: {str(e)}")
            return False
    
    @staticmethod
    def send_test_email(to_email, subject="Test Email", message="This is a test email"):
        """
        Send a simple test email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message
        """
        try:
            from_email = settings.EMAIL_FROM
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[to_email]
            )
            
            msg.send()
            logger.info(f"Test email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            return False
    
    @staticmethod
    def send_notification_email(notification):
        """
        Send email notification based on notification type
        
        Args:
            notification: Notification instance
        """
        try:
            context = EmailService._prepare_email_context(notification)
            template_name = EmailService._get_template_name(notification.notification_type)
            
            html_content = render_to_string(f'emails/{template_name}', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject=notification.title,
                body=text_content,
                from_email=settings.EMAIL_FROM,
                to=[notification.user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            notification.is_email_sent = True
            notification.save()
            
            logger.info(f"Notification email sent successfully to {notification.user.email} for {notification.notification_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification email: {str(e)}")
            return False
    
    @staticmethod
    def _prepare_email_context(notification):
        """
        Prepare context for email templates
        
        Args:
            notification: Notification instance
        """
        context = {
            'notification': notification,
            'user': notification.user,
        }
        
        if notification.order:
            context.update({
                'order': notification.order,
                'client': notification.order.client,
                'service': notification.order.service,
                'collaborator': notification.order.collaborator,
                'status': notification.order.status,
                'deadline_date': notification.order.deadline_date,
                'total_price': notification.order.total_price,
                'advance_payment': notification.order.advance_payment,
                'remaining_payment': notification.order.remaining_payment,
            })
        
        if notification.livrable:
            context['livrable'] = notification.livrable
            
        return context
    
    @staticmethod
    def _get_template_name(notification_type):
        """
        Map notification types to email templates
        
        Args:
            notification_type: Type of notification
        """
        template_mapping = {
            'order_assigned': 'order_assignment.html',
            'order_status_changed': 'order_status_changed.html',
            'order_cancelled': 'order_cancellation.html',
            'livrable_uploaded': 'livrable_uploaded.html',
            'livrable_reviewed': 'livrable_reviewed.html',
            'livrable_accepted': 'livrable_accepted.html',
            'livrable_rejected': 'livrable_rejected.html',
            'payment_reminder': 'payment_reminder.html',
            'deadline_reminder': 'deadline_reminder.html',
            'order_completed': 'order_completed.html',
            'review_reminder': 'review_reminder.html',
            'account_created': 'collaborator_account_created.html',
            'user_blacklisted': 'user_blacklisted.html',
        }
        return template_mapping.get(notification_type, 'generic_notification.html')