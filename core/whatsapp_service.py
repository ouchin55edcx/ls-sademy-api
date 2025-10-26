"""
WhatsApp service for sending notifications via Infobip API
"""
import requests
import logging
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Service for sending WhatsApp notifications via Infobip API
    """
    
    @staticmethod
    def send_order_confirmation(order) -> Dict[str, Any]:
        """
        Send order confirmation WhatsApp message to client
        
        Args:
            order: Order instance
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Format phone number (ensure it starts with +212)
            phone = WhatsAppService._format_phone_number(order.client.user.phone)
            if not phone:
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'message_id': None
                }
            
            # Prepare message content
            message = WhatsAppService._format_order_confirmation_message(order)
            
            # Send WhatsApp message
            response = WhatsAppService._send_whatsapp_message(phone, message)
            
            if response.get('success'):
                logger.info(f"WhatsApp order confirmation sent successfully to {phone} for order #{order.id}")
                return {
                    'success': True,
                    'message_id': response.get('message_id'),
                    'phone': phone
                }
            else:
                logger.error(f"Failed to send WhatsApp order confirmation: {response.get('error')}")
                return {
                    'success': False,
                    'error': response.get('error'),
                    'message_id': None
                }
                
        except Exception as e:
            logger.error(f"Exception in send_order_confirmation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message_id': None
            }
    
    @staticmethod
    def send_admin_notification(order) -> Dict[str, Any]:
        """
        Send admin notification WhatsApp message about new order
        
        Args:
            order: Order instance
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Get admin phone numbers (you might want to store these in settings or database)
            admin_phones = WhatsAppService._get_admin_phones()
            if not admin_phones:
                return {
                    'success': False,
                    'error': 'No admin phone numbers configured',
                    'message_id': None
                }
            
            # Prepare message content
            message = WhatsAppService._format_admin_notification_message(order)
            
            # Send to all admin phones
            results = []
            for phone in admin_phones:
                response = WhatsAppService._send_whatsapp_message(phone, message)
                results.append({
                    'phone': phone,
                    'success': response.get('success', False),
                    'message_id': response.get('message_id'),
                    'error': response.get('error')
                })
            
            # Check if at least one was successful
            success_count = sum(1 for r in results if r['success'])
            
            return {
                'success': success_count > 0,
                'results': results,
                'success_count': success_count,
                'total_count': len(results)
            }
                
        except Exception as e:
            logger.error(f"Exception in send_admin_notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message_id': None
            }
    
    @staticmethod
    def _send_whatsapp_message(phone: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via Infobip API
        
        Args:
            phone: Phone number in E.164 format
            message: Message content
            
        Returns:
            Dict with success status and response details
        """
        try:
            # Check if Infobip is configured
            if not settings.INFOBIP_API_KEY or not settings.INFOBIP_SENDER:
                return {
                    'success': False,
                    'error': 'Infobip not configured',
                    'message_id': None
                }
            
            # Prepare API request
            url = f"{settings.INFOBIP_BASE_URL}/whatsapp/1/message/text"
            headers = {
                "Authorization": f"App {settings.INFOBIP_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "from": settings.INFOBIP_SENDER,
                "to": phone,
                "content": {
                    "text": message
                }
            }
            
            # Send request
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('messageId')
                return {
                    'success': True,
                    'message_id': message_id,
                    'response': response_data
                }
            else:
                error_msg = f"Infobip API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'message_id': None
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Infobip API timeout"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Infobip API request failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }
        except Exception as e:
            error_msg = f"Unexpected error sending WhatsApp message: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }
    
    @staticmethod
    def _format_phone_number(phone: str) -> Optional[str]:
        """
        Format phone number to E.164 format
        
        Args:
            phone: Raw phone number
            
        Returns:
            Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # If it doesn't start with +, add +212
        if not cleaned.startswith('+'):
            if cleaned.startswith('212'):
                cleaned = '+' + cleaned
            elif cleaned.startswith('0'):
                cleaned = '+212' + cleaned[1:]
            else:
                cleaned = '+212' + cleaned
        
        # Validate format (should be +212XXXXXXXXX)
        if cleaned.startswith('+212') and len(cleaned) == 13:
            return cleaned
        
        return None
    
    @staticmethod
    def _format_order_confirmation_message(order) -> str:
        """
        Format order confirmation message for client
        
        Args:
            order: Order instance
            
        Returns:
            Formatted message string
        """
        # Get order number (we'll add this field to the model)
        order_number = getattr(order, 'order_number', f"#{order.id}")
        
        # Format deadline
        deadline = order.deadline_date.strftime('%d/%m/%Y')
        
        # Format budget
        budget = f"{order.total_price} MAD" if order.total_price else "Devis personnalisé"
        
        # Get service name
        service_name = order.service.name
        
        # Get client name
        client_name = order.client.user.get_full_name() or order.client.user.first_name or "Client"
        
        message = f"""🎉 Nouvelle Commande Reçue!

Bonjour {client_name},

Votre commande {order_number} a été enregistrée avec succès.

📋 Service: {service_name}
📅 Échéance: {deadline}
💰 Budget: {budget}

✅ Statut: En attente de traitement

Notre équipe va examiner votre demande et vous contacter sous 1 heure.

Vous recevrez un email de confirmation à: {order.client.user.email}

Merci de votre confiance!
- L'équipe Sademy

🔗 Suivre ma commande: https://sademiy.com/orders/{order.id}"""
        
        return message
    
    @staticmethod
    def _format_admin_notification_message(order) -> str:
        """
        Format admin notification message about new order
        
        Args:
            order: Order instance
            
        Returns:
            Formatted message string
        """
        # Get order number
        order_number = getattr(order, 'order_number', f"#{order.id}")
        
        # Format deadline
        deadline = order.deadline_date.strftime('%d/%m/%Y')
        
        # Format budget
        budget = f"{order.total_price} MAD" if order.total_price else "Devis personnalisé"
        
        # Get service name
        service_name = order.service.name
        
        # Get client name
        client_name = order.client.user.get_full_name() or order.client.user.first_name or "Client"
        
        # Truncate description if too long
        description = order.quotation or order.description or "Aucune description"
        if len(description) > 200:
            description = description[:200] + "..."
        
        message = f"""🔔 Nouvelle Commande - Action Requise

Commande: {order_number}
Client: {client_name}
Service: {service_name}
Échéance: {deadline}
Budget: {budget}

📱 Téléphone: {order.client.user.phone or 'Non fourni'}
📧 Email: {order.client.user.email}

Description:
{description}

👉 Voir les détails: https://admin.sademiy.com/orders/{order.id}"""
        
        return message
    
    @staticmethod
    def _get_admin_phones() -> list:
        """
        Get admin phone numbers for notifications
        
        Returns:
            List of admin phone numbers
        """
        # For now, return empty list - you can implement this based on your needs
        # You might want to store admin phones in settings or database
        admin_phones = []
        
        # Example: Get from settings
        admin_phone = getattr(settings, 'ADMIN_PHONE', None)
        if admin_phone:
            admin_phones.append(admin_phone)
        
        # Example: Get from database (if you store admin phones)
        # from core.models import Admin
        # admin_users = Admin.objects.filter(user__phone__isnull=False)
        # admin_phones.extend([admin.user.phone for admin in admin_users if admin.user.phone])
        
        return admin_phones
