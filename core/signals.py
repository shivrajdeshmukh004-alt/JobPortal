from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Application, JobPost, CustomUser
from django.conf import settings
import threading
import logging

logger = logging.getLogger(__name__)

SITE_URL = 'https://jobportal-1268.onrender.com'

# Helper function to send HTML email in a background thread
def send_html_email(subject, template_name, context, recipient_list):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    
    # Send in background thread to avoid blocking the request
    def _send():
        try:
            msg.send(fail_silently=True)
        except Exception as e:
            logger.error(f"Email send failed: {e}")
    
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

@receiver(post_save, sender=Application)
def handle_application_email(sender, instance, created, **kwargs):
    # Common context
    context = {
        'candidate_name': instance.candidate.get_full_name() or instance.candidate.username,
        'job_title': instance.job.title,
        'company_name': instance.job.company_name,
        'dashboard_url': f'{SITE_URL}/candidate/home/',
        'banner_url': f'{SITE_URL}/static/images/email_banner.png',
        'score': instance.score,
    }

    if created:
        # On successful application
        send_html_email(
            subject=f"Application Received: {instance.job.title}",
            template_name='emails/application_received.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )
        
    elif instance.status == 'SHORTLISTED':
        # On shortlist update
        send_html_email(
            subject=f"Exciting News: You are shortlisted for {instance.job.title}!",
            template_name='emails/shortlisted.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )
        
    elif instance.status == 'REJECTED':
        # On rejected status
        send_html_email(
            subject=f"Update on your application for {instance.job.title}",
            template_name='emails/rejected.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )

@receiver(post_save, sender=JobPost)
def handle_new_job_email(sender, instance, created, **kwargs):
    # Notify all candidates when a new job is posted
    if created:
        candidates = CustomUser.objects.filter(is_candidate=True)
        recipient_list = [c.email for c in candidates if c.email]
        
        if recipient_list:
            context = {
                'job_title': instance.title,
                'company_name': instance.company_name,
                'location': instance.location,
                'job_url': f'{SITE_URL}/candidate/home/',
                'banner_url': f'{SITE_URL}/static/images/email_banner.png',
            }
            
            subject = f"New Job Opportunity: {instance.title}"
            html_content = render_to_string('emails/new_job.html', context)
            text_content = strip_tags(html_content)
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                bcc=recipient_list
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send in background thread to avoid blocking the request
            def _send():
                try:
                    msg.send(fail_silently=True)
                except Exception as e:
                    logger.error(f"Bulk email send failed: {e}")
            
            thread = threading.Thread(target=_send)
            thread.daemon = True
            thread.start()
