from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Application, JobPost, CustomUser
from django.conf import settings

# Helper function to send HTML email
def send_html_email(subject, template_name, context, recipient_list):
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    # Add banner URL to context if not present (although passed to render_to_string)
    # We assume the template uses 'banner_url'
    
    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=True)

@receiver(post_save, sender=Application)
def handle_application_email(sender, instance, created, **kwargs):
    # Common context
    context = {
        'candidate_name': instance.candidate.get_full_name() or instance.candidate.username,
        'job_title': instance.job.title,
        'company_name': instance.job.company_name,
        'dashboard_url': 'http://127.0.0.1:8000/candidate/home/', # Ideally use request.build_absolute_uri but signals don't have request
        'banner_url': 'http://127.0.0.1:8000/static/images/email_banner.png',
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
        # On rejected status (new)
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
                'job_url': 'http://127.0.0.1:8000/candidate/home/',
                'banner_url': 'http://127.0.0.1:8000/static/images/email_banner.png',
            }
            
            # Send in batches of 50 to avoid limits (simple implementation)
            # For now, just singular send loop or bulk bcc
            # Using loop for personalization 'Hi there' is generic so bulk is fine
            
            msg = EmailMultiAlternatives(
                subject=f"New Job Opportunity: {instance.title}",
                body="A new job has been posted.", # Fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                bcc=recipient_list # Use BCC for bulk notification
            )
            html_content = render_to_string('emails/new_job.html', context)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
