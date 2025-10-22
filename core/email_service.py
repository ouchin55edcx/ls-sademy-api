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
