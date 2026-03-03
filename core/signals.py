from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Application, JobPost, CustomUser
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

SITE_URL = 'https://jobportal-1268.onrender.com'


def send_html_email(subject, template_name, context, recipient_list):
    """Send HTML email via configured backend (Brevo HTTP API)."""
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Email sent: '{subject}' to {recipient_list}")
    except Exception as e:
        logger.error(f"Email FAILED: '{subject}' to {recipient_list} - {e}")


@receiver(post_save, sender=Application)
def handle_application_email(sender, instance, created, **kwargs):
    context = {
        'candidate_name': instance.candidate.get_full_name() or instance.candidate.username,
        'job_title': instance.job.title,
        'company_name': instance.job.company_name,
        'dashboard_url': f'{SITE_URL}/candidate/home/',
        'banner_url': f'{SITE_URL}/static/images/email_banner.png',
        'score': instance.score,
    }

    if created:
        send_html_email(
            subject=f"Application Received: {instance.job.title}",
            template_name='emails/application_received.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )
        
    elif instance.status == 'SHORTLISTED':
        send_html_email(
            subject=f"Exciting News: You are shortlisted for {instance.job.title}!",
            template_name='emails/shortlisted.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )
        
    elif instance.status == 'REJECTED':
        send_html_email(
            subject=f"Update on your application for {instance.job.title}",
            template_name='emails/rejected.html',
            context=context,
            recipient_list=[instance.candidate.email]
        )


@receiver(post_save, sender=JobPost)
def handle_new_job_email(sender, instance, created, **kwargs):
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
            
            try:
                html_content = render_to_string('emails/new_job.html', context)
                text_content = strip_tags(html_content)
                
                msg = EmailMultiAlternatives(
                    subject=f"New Job Opportunity: {instance.title}",
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    bcc=recipient_list,
                    to=[settings.DEFAULT_FROM_EMAIL],  # Brevo requires at least one 'to'
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)
                logger.info(f"New job email sent to {len(recipient_list)} candidates")
            except Exception as e:
                logger.error(f"New job email FAILED: {e}")
