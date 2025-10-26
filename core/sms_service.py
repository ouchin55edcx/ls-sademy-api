"""
SMS service for sending notifications via Infobip API
"""
import http.client
import json
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SMSService:
    """
    Service for sending SMS notifications via Infobip API
    """
    
    @staticmethod
    def send_order_confirmation(order) -> Dict[str, Any]:
        """
        Send order confirmation SMS message to client
        
        Args:
            order: Order instance
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Format phone number (ensure it starts with +212)
            phone = SMSService._format_phone_number(order.client.user.phone)
            if not phone:
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'message_id': None
                }
            
            # Prepare message content
            message = SMSService._format_order_confirmation_message(order)
            
            # Send SMS message
            response = SMSService._send_sms_message(phone, message)
            
            if response.get('success'):
                logger.info(f"SMS order confirmation sent successfully to {phone} for order #{order.id}")
                return {
                    'success': True,
                    'message_id': response.get('message_id'),
                    'phone': phone
                }
            else:
                logger.error(f"Failed to send SMS order confirmation: {response.get('error')}")
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
        Send admin notification SMS message about new order
        
        Args:
            order: Order instance
            
        Returns:
            Dict with success status and message details
        """
        try:
            # Get admin phone numbers
            admin_phones = SMSService._get_admin_phones()
            if not admin_phones:
                return {
                    'success': False,
                    'error': 'No admin phone numbers configured',
                    'message_id': None
                }
            
            # Prepare message content
            message = SMSService._format_admin_notification_message(order)
            
            # Send to all admin phones
            results = []
            logger.info(f"Admin phones to notify: {admin_phones}")
            for phone in admin_phones:
                logger.info(f"Sending SMS to admin phone: {phone}")
                response = SMSService._send_sms_message(phone, message)
                logger.info(f"SMS response: {response}")
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
    def _send_sms_message(phone: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message via Infobip API
        
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
            conn = http.client.HTTPSConnection("api.infobip.com")
            
            # Remove + from phone number for SMS
            phone_clean = phone.replace('+', '')
            
            payload = json.dumps({
                "messages": [
                    {
                        "destinations": [{"to": phone_clean}],
                        "from": settings.INFOBIP_SMS_SENDER,
                        "text": message
                    }
                ]
            })
            
            logger.info(f"SMS payload: {payload}")
            logger.info(f"Phone clean: {phone_clean}, Sender: {settings.INFOBIP_SMS_SENDER}")
            
            headers = {
                'Authorization': f'App {settings.INFOBIP_API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Send request
            conn.request("POST", "/sms/2/text/advanced", payload, headers)
            res = conn.getresponse()
            data = res.read()
            response_data = json.loads(data.decode("utf-8"))
            
            if res.status == 200:
                message_id = response_data.get('messages', [{}])[0].get('messageId')
                return {
                    'success': True,
                    'message_id': message_id,
                    'response': response_data
                }
            else:
                error_msg = f"Infobip SMS API error {res.status}: {data.decode('utf-8')}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'message_id': None
                }
                
        except Exception as e:
            error_msg = f"Unexpected error sending SMS message: {str(e)}"
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
        
        message = f"""Nouvelle Commande Reçue!

Bonjour {client_name},

Votre commande {order_number} a été enregistrée avec succès.

Service: {service_name}
Échéance: {deadline}
Budget: {budget}

Statut: En attente de traitement

Notre équipe va examiner votre demande et vous contacter sous 1 heure.

Merci de votre confiance!
- L'équipe Sademy"""
        
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
        if len(description) > 100:
            description = description[:100] + "..."
        
        message = f"""Nouvelle Commande - Action Requise

Commande: {order_number}
Client: {client_name}
Service: {service_name}
Échéance: {deadline}
Budget: {budget}

Téléphone: {order.client.user.phone or 'Non fourni'}
Email: {order.client.user.email}

Description: {description}"""
        
        return message
    
    @staticmethod
    def _get_admin_phones() -> list:
        """
        Get admin phone numbers for notifications
        
        Returns:
            List of admin phone numbers
        """
        admin_phones = []
        
        # Get from settings
        admin_phone = getattr(settings, 'ADMIN_PHONE', None)
        if admin_phone:
            # Format the phone number properly - ensure it starts with +
            if not admin_phone.startswith('+'):
                admin_phone = '+' + admin_phone
            formatted_phone = SMSService._format_phone_number(admin_phone)
            if formatted_phone:
                admin_phones.append(formatted_phone)
        
        return admin_phones
