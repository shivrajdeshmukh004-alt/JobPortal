"""
Custom email backend that uses Brevo's HTTP API instead of SMTP.
Render's free tier blocks outbound SMTP connections, so we use the REST API.
"""
import requests
import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'


class BrevoEmailBackend(BaseEmailBackend):
    """
    Email backend that sends mail via Brevo's HTTP API.
    
    Required settings:
        BREVO_API_KEY = 'your-brevo-api-key'
        DEFAULT_FROM_EMAIL = 'verified-sender@example.com'
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', None)
    
    def send_messages(self, email_messages):
        if not self.api_key:
            logger.error("BREVO_API_KEY is not set. Cannot send emails.")
            if not self.fail_silently:
                raise ValueError("BREVO_API_KEY is not configured.")
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                if self._send_one(message):
                    sent_count += 1
            except Exception as e:
                logger.error(f"Brevo email send failed: {e}")
                if not self.fail_silently:
                    raise
        return sent_count
    
    def _send_one(self, message):
        """Send a single email via Brevo API."""
        # Build recipient list
        to_list = [{'email': addr} for addr in message.to] if message.to else []
        cc_list = [{'email': addr} for addr in message.cc] if message.cc else []
        bcc_list = [{'email': addr} for addr in message.bcc] if message.bcc else []
        
        if not to_list and not bcc_list:
            logger.warning("No recipients for email, skipping.")
            return False
        
        # Build payload
        payload = {
            'sender': {
                'email': message.from_email or settings.DEFAULT_FROM_EMAIL,
            },
            'subject': message.subject,
        }
        
        # Add recipients
        if to_list:
            payload['to'] = to_list
        elif bcc_list:
            # Brevo requires at least 'to', use first bcc as 'to' if no 'to'
            payload['to'] = [bcc_list[0]]
            bcc_list = bcc_list[1:]
        
        if cc_list:
            payload['cc'] = cc_list
        if bcc_list:
            payload['bcc'] = bcc_list
        
        # Check for HTML content
        html_content = None
        if message.alternatives:
            for content, mimetype in message.alternatives:
                if mimetype == 'text/html':
                    html_content = content
                    break
        
        if html_content:
            payload['htmlContent'] = html_content
        
        # Always include text content
        if message.body:
            payload['textContent'] = message.body
        
        # Send via Brevo API
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': self.api_key,
        }
        
        response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code in (200, 201):
            logger.info(f"Email sent via Brevo to {message.to}")
            return True
        else:
            logger.error(f"Brevo API error {response.status_code}: {response.text}")
            if not self.fail_silently:
                raise Exception(f"Brevo API error: {response.status_code} - {response.text}")
            return False
