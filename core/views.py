from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import JobPost, Application, CandidateProfile, CustomUser, HRProfile
from .forms import JobPostForm, CandidateProfileForm, HRProfileForm
from .utils import calculate_similarity_score
from .decorators import hr_required, candidate_required
from .chatbot import get_sambanova_response
from django.http import JsonResponse
import json
import threading
import logging

logger = logging.getLogger(__name__)

# --- Helper: Non-blocking email sender ---
def send_mail_async(subject, message, from_email, recipient_list, html_message=None, fail_silently=True):
    """Send email in a background thread to prevent request blocking on Render."""
    def _send():
        try:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                html_message=html_message,
                fail_silently=fail_silently,
            )
        except Exception as e:
            logger.error(f"Email send failed to {recipient_list}: {e}")
    
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()

# TEMPORARY: Diagnostic endpoint to test email - remove after fixing
def test_email(request):
    """Test email configuration and show exact errors."""
    import traceback
    results = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'BREVO_API_KEY': '***' + (settings.BREVO_API_KEY[-4:] if settings.BREVO_API_KEY else 'NOT SET'),
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    }
    
    try:
        send_mail(
            'RecruitAI Test Email',
            'If you receive this, email is working on Render!',
            settings.DEFAULT_FROM_EMAIL,
            ['adityadeshmukh904@gmail.com'],
            fail_silently=False,
        )
        results['status'] = 'SUCCESS - Email sent via Brevo HTTP API!'
    except Exception as e:
        results['error'] = str(e)
        results['traceback'] = traceback.format_exc()
    
    return JsonResponse(results, json_dumps_params={'indent': 2})

@login_required
def dashboard(request):
    if request.user.is_hr:
        return redirect('hr_dashboard')
    else:
        return redirect('candidate_dashboard') # Placeholder

@hr_required
def hr_dashboard(request):
    jobs = JobPost.objects.filter(recruiter=request.user).order_by('-created_at')
    
    # Calculate stats
    total_jobs = jobs.count()
    total_applicants = Application.objects.filter(job__recruiter=request.user).count()
    shortlisted_count = Application.objects.filter(job__recruiter=request.user, status='SHORTLISTED').count()
    
    context = {
        'jobs': jobs,
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'shortlisted_count': shortlisted_count,
        'now': timezone.now()
    }
    return render(request, 'core/hr_dashboard.html', context)

@hr_required
def create_job(request):
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('hr_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobPostForm()
    return render(request, 'core/job_form.html', {'form': form})

@hr_required
def edit_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, recruiter=request.user)
    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('hr_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = JobPostForm(instance=job)
    return render(request, 'core/job_form.html', {'form': form, 'edit_mode': True})

@hr_required
def delete_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, recruiter=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
    return redirect('hr_dashboard')

@hr_required
def job_applicants(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, recruiter=request.user)
    sort = request.GET.get('sort', '-score') # Default sort by highest score
    
    applicants = Application.objects.filter(job=job)
    
    if sort == 'score_asc':
        applicants = applicants.order_by('score')
    elif sort == 'score_desc':
        applicants = applicants.order_by('-score')
    elif sort == 'newest':
        applicants = applicants.order_by('-applied_at')
    else:
        applicants = applicants.order_by('-score') # Default
        
    cutoff = request.GET.get('cutoff')
    if cutoff:
        try:
            cutoff_val = float(cutoff)
            applicants = applicants.filter(score__gte=cutoff_val)
        except ValueError:
            pass
            
    context = {
        'job': job, 
        'applicants': applicants,
        'cutoff': cutoff
    }
    return render(request, 'core/job_applicants.html', context)

@hr_required
def shortlist_candidate(request, application_id):
    app = get_object_or_404(Application, id=application_id, job__recruiter=request.user)
    app.status = 'SHORTLISTED'
    app.save()
    messages.success(request, f"Candidate {app.candidate.username} shortlisted!")
    return redirect('job_applicants', job_id=app.job.id)

@hr_required
def reject_candidate(request, application_id):
    app = get_object_or_404(Application, id=application_id, job__recruiter=request.user)
    app.status = 'REJECTED'
    app.save()
    messages.success(request, f"Candidate {app.candidate.username} rejected.")
    return redirect('job_applicants', job_id=app.job.id)

@hr_required
def manage_next_round(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, recruiter=request.user)
    # Exclude REJECTED and SELECTED candidates from the list
    shortlisted_applicants = Application.objects.filter(
        job=job
    ).filter(
        Q(status='SHORTLISTED') | Q(status='SECOND_ROUND')
    ).exclude(
        status__in=['REJECTED', 'SELECTED']
    ).select_related('candidate', 'candidate__candidate_profile').order_by('id')
    
    if request.method == 'POST':
        action = request.POST.get('action')  # Determine action type
        selected_ids = request.POST.getlist('application_ids')
        
        if not selected_ids:
            messages.warning(request, "Please select at least one candidate.")
            return redirect('manage_next_round', job_id=job.id)
        
        # ACTION 1: REJECT CANDIDATES
        # Note: signals.py handles sending REJECTED emails automatically
        if action == 'reject':
            apps = Application.objects.filter(id__in=selected_ids, job=job)
            count = 0
            for app in apps:
                app.status = 'REJECTED'
                app.save()  # Signal will send rejection email
                count += 1
            messages.success(request, f"Successfully rejected {count} candidate(s).")
            return redirect('manage_next_round', job_id=job.id)
        
        # ACTION 2: FINAL SELECTION
        elif action == 'select':
            if len(selected_ids) != 1:
                messages.error(request, "Please select exactly ONE candidate for final selection.")
                return redirect('manage_next_round', job_id=job.id)
            
            app = Application.objects.get(id=selected_ids[0], job=job)
            app.status = 'SELECTED'
            app.save()
            
            # Send selection email (async)
            try:
                context = {
                    'candidate_name': app.candidate.get_full_name() or app.candidate.username,
                    'job_title': app.job.title,
                    'company_name': app.job.company_name,
                }
                html_message = render_to_string('emails/selected.html', context)
                plain_message = strip_tags(html_message)

                send_mail_async(
                    f'Congratulations! Selected for {app.job.title}',
                    plain_message,
                    settings.EMAIL_HOST_USER,
                    [app.candidate.email],
                    html_message=html_message,
                )
                messages.success(request, f"Successfully selected {app.candidate.get_full_name() or app.candidate.username} for the role!")
            except Exception as e:
                messages.warning(request, f"Candidate selected, but email failed: {str(e)}")
            
            return redirect('manage_next_round', job_id=job.id)
        
        # ACTION 3: MOVE TO NEXT ROUND (existing logic with new email)
        elif action == 'next_round':
            round_name = request.POST.get('interview_name')
            link = request.POST.get('interview_link')
            date_str = request.POST.get('interview_date')
            
            if not all([round_name, link, date_str]):
                messages.error(request, "Please fill in all round details (name, link, and date).")
                return redirect('manage_next_round', job_id=job.id)

            # Parse date
            interview_date = parse_datetime(date_str)
            if interview_date and timezone.is_naive(interview_date):
                interview_date = timezone.make_aware(interview_date)
                
            # Update/Create entries
            apps = Application.objects.filter(id__in=selected_ids, job=job)
            
            success_count = 0
            
            for app in apps:
                # Update status and interview details
                app.status = 'SECOND_ROUND'
                app.interview_name = round_name
                app.interview_link = link
                app.interview_date = interview_date
                app.save()
                
                # Send "Round Cleared" Email (async)
                try:
                    context = {
                        'candidate_name': app.candidate.get_full_name() or app.candidate.username,
                        'job_title': app.job.title,
                        'company_name': app.job.company_name,
                        'round_name': round_name,
                        'interview_date': interview_date.strftime("%d %b, %Y %I:%M %p") if interview_date else date_str,
                        'link': link
                    }
                    html_message = render_to_string('emails/round_cleared.html', context)
                    plain_message = strip_tags(html_message)

                    send_mail_async(
                        f'Congratulations! Next Round - {app.job.title}',
                        plain_message,
                        settings.EMAIL_HOST_USER,
                        [app.candidate.email],
                        html_message=html_message,
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Email error for {app.candidate.username}: {e}")
            
            messages.success(request, f"Successfully moved {success_count} candidate(s) to {round_name}!")
                
            return redirect('manage_next_round', job_id=job.id)

    return render(request, 'core/manage_next_round.html', {
        'job': job,
        'applicants': shortlisted_applicants
    })

@hr_required
def send_to_second_round(request, application_id):
    app = get_object_or_404(Application, id=application_id, job__recruiter=request.user)
    if request.method == 'POST':
        round_name = request.POST.get('interview_name')
        link = request.POST.get('interview_link')
        date_str = request.POST.get('interview_date')
        
        # Parse date
        interview_date = parse_datetime(date_str)
        if interview_date and timezone.is_naive(interview_date):
            interview_date = timezone.make_aware(interview_date)
            
        app.status = 'SECOND_ROUND'
        app.interview_name = round_name
        app.interview_link = link
        app.interview_date = interview_date
        app.save()
        
        # Send Email (async)
        try:
            context = {
                'candidate_name': app.candidate.get_full_name() or app.candidate.username,
                'job_title': app.job.title,
                'company_name': app.job.company_name,
                'round_name': round_name,
                'interview_date': interview_date.strftime("%d %b, %Y %I:%M %p") if interview_date else date_str,
                'link': link
            }
            html_message = render_to_string('emails/interview_invite.html', context)
            plain_message = strip_tags(html_message)

            send_mail_async(
                f'Invitation for {round_name} - {app.job.title}',
                plain_message,
                settings.EMAIL_HOST_USER,
                [app.candidate.email],
                html_message=html_message,
            )
            messages.success(request, f"Invitation sent to {app.candidate.username} for {round_name}!")
        except Exception as e:
            messages.warning(request, f"Status updated, but email failed: {str(e)}")
            
    return redirect('job_applicants', job_id=app.job.id)

@hr_required
def bulk_manage_applicants(request, job_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        app_ids = request.POST.getlist('application_ids')
        
        if not app_ids:
            messages.warning(request, "No candidates selected.")
            return redirect('job_applicants', job_id=job_id)
            
        apps = Application.objects.filter(id__in=app_ids, job__id=job_id, job__recruiter=request.user)
        
        # Note: signals.py handles SHORTLISTED and REJECTED emails automatically
        if action == 'shortlist':
            count = 0
            for app in apps:
                app.status = 'SHORTLISTED'
                app.save()  # Signal will send shortlist email
                count += 1
            messages.success(request, f"Shortlisted {count} candidate(s). Notification emails sent.")

        elif action == 'reject':
            count = 0
            for app in apps:
                app.status = 'REJECTED'
                app.save()  # Signal will send rejection email
                count += 1
            messages.success(request, f"Rejected {count} candidate(s). Notification emails sent.")
                
        elif action == 'second_round':
            round_name = request.POST.get('interview_name')
            link = request.POST.get('interview_link')
            date_str = request.POST.get('interview_date')
            
            # Parse date
            interview_date = parse_datetime(date_str)
            if interview_date and timezone.is_naive(interview_date):
                interview_date = timezone.make_aware(interview_date)
            
            success_count = 0
            
            for app in apps:
                app.status = 'SECOND_ROUND'
                app.interview_name = round_name
                app.interview_link = link
                app.interview_date = interview_date
                app.save()
                
                # Send interview invitation email (async)
                try:
                    context = {
                        'candidate_name': app.candidate.get_full_name() or app.candidate.username,
                        'job_title': app.job.title,
                        'company_name': app.job.company_name,
                        'round_name': round_name,
                        'interview_date': interview_date.strftime("%d %b, %Y %I:%M %p") if interview_date else date_str,
                        'link': link
                    }
                    html_message = render_to_string('emails/interview_invite.html', context)
                    plain_message = strip_tags(html_message)

                    send_mail_async(
                        f'Invitation for {round_name} - {app.job.title}',
                        plain_message,
                        settings.EMAIL_HOST_USER,
                        [app.candidate.email],
                        html_message=html_message,
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Email error for {app.candidate.username}: {e}")
            
            messages.success(request, f"Invited {success_count} candidate(s) to {round_name} and sent emails.")
            
    return redirect('job_applicants', job_id=job_id)

@login_required
def candidate_dashboard(request):
    if request.user.is_hr:
        return redirect('hr_dashboard')
        
    applied_ids = Application.objects.filter(candidate=request.user).values_list('job_id', flat=True)
    live_jobs = JobPost.objects.exclude(id__in=applied_ids).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gt=timezone.now())
    ).order_by('-created_at')

    # Filters
    locations = request.GET.getlist('location')
    roles = request.GET.getlist('role')
    
    if locations:
        q_loc = Q()
        for loc in locations:
            q_loc |= Q(location__icontains=loc)
        live_jobs = live_jobs.filter(q_loc)
        
    if roles:
        q_role = Q()
        for role in roles:
            q_role |= Q(title__icontains=role)
        live_jobs = live_jobs.filter(q_role)
    my_applications = Application.objects.filter(candidate=request.user).order_by('-applied_at')
    
    # Safe profile fetching
    try:
        profile = request.user.candidate_profile
    except CandidateProfile.DoesNotExist:
        profile = None

    from django.core.paginator import Paginator
    
    # Pagination for live_jobs
    paginator = Paginator(live_jobs, 5) # 5 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check eligibility for each job
    jobs_with_eligibility = []
    for job in page_obj:
        eligibility_info = {'eligible': True, 'reasons': []}
        if profile:
            eligibility_info = job.check_eligibility(profile)
        else:
            # If no profile, consider ineligible if job has any criteria
            if any([job.min_tenth_percentage, job.min_twelfth_percentage, job.min_degree_percentage, job.min_age, job.max_age]):
                eligibility_info = {
                    'eligible': False,
                    'reasons': ['Please complete your profile to check eligibility']
                }
        
        jobs_with_eligibility.append({
            'job': job,
            'eligibility': eligibility_info
        })

    return render(request, 'core/candidate_dashboard.html', {
        'jobs_with_eligibility': jobs_with_eligibility,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'my_applications': my_applications,
        'user_profile': profile
    })

@login_required
def apply_job(request, job_id):
    if request.user.is_hr:
        return redirect('dashboard')
        
    job = get_object_or_404(JobPost, id=job_id)
    
    # Check if job has expired
    if job.expiry_date and timezone.now() > job.expiry_date:
        from django.contrib import messages
        messages.error(request, "This job has expired and is no longer accepting applications.")
        return redirect('candidate_dashboard')

    # Check if already applied
    if Application.objects.filter(candidate=request.user, job=job).exists():
        return redirect('candidate_dashboard')
    
    # Check eligibility
    try:
        profile = request.user.candidate_profile
        eligibility_check = job.check_eligibility(profile)
        
        if not eligibility_check['eligible']:
            from django.contrib import messages
            reasons = ' '.join(eligibility_check['reasons'])
            messages.error(request, f"You are not eligible for this job. {reasons}")
            return redirect('candidate_dashboard')
    except CandidateProfile.DoesNotExist:
        # If job has eligibility criteria and user has no profile, reject
        if any([job.min_tenth_percentage, job.min_twelfth_percentage, job.min_degree_percentage, job.min_age, job.max_age]):
            from django.contrib import messages
            messages.error(request, "Please complete your profile before applying to jobs with eligibility criteria.")
            return redirect('candidate_dashboard')
        profile = None
        
    # Create application
    # Calculate score using profile match + resume extraction
    try:
        if not profile:
            profile = request.user.candidate_profile
        candidate_data = f"{profile.skills} {profile.projects}"
        
        # New: Extract text from resume if available
        resume_text = ""
        if profile.master_resume:
            from .utils import extract_text_from_pdf
            resume_text = extract_text_from_pdf(profile.master_resume.url)
            
        score = calculate_similarity_score(job.required_skills, job.description, candidate_data, resume_text)
        resume = profile.master_resume
    except CandidateProfile.DoesNotExist:
        score = 0
        resume = None
        
    Application.objects.create(
        candidate=request.user,
        job=job,
        score=score,
        resume=resume
    )
    return redirect('candidate_dashboard')

@login_required
def profile_view(request):
    if request.user.is_hr:
        return redirect('hr_dashboard')
    try:
        profile = request.user.candidate_profile
    except CandidateProfile.DoesNotExist:
        profile = CandidateProfile.objects.create(user=request.user)
    
    return render(request, 'core/profile_detail.html', {'profile': profile})

@login_required
def update_profile(request):
    if request.user.is_hr:
         return redirect('hr_dashboard')
         
    try:
        profile = request.user.candidate_profile
    except CandidateProfile.DoesNotExist:
        profile = CandidateProfile(user=request.user)
        
    if request.method == 'POST':
        form = CandidateProfileForm(request.POST, request.FILES, instance=profile)
        # Handle user name updates manually
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if form.is_valid():
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
            form.save()
            return redirect('profile_view')
    else:
        form = CandidateProfileForm(instance=profile)
        
    return render(request, 'core/profile_form.html', {
        'form': form,
        'user': request.user
    })

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile_view')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'core/password_change.html', {
        'form': form
    })

import random
import string

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            otp = generate_otp()
            request.session['reset_otp'] = otp
            request.session['reset_email'] = email
            
            # Send OTP email (async to prevent timeout)
            send_mail_async(
                'Password Reset OTP - RecruitAI',
                f'Your OTP for password reset is: {otp}\n\nThis OTP is valid for this session only.',
                settings.EMAIL_HOST_USER,
                [email],
            )
                
            messages.success(request, 'OTP sent to your email!')
            return redirect('verify_otp')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User with this email not found.')
            
    return render(request, 'core/forgot_password.html')

def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == request.session.get('reset_otp'):
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP.')
    return render(request, 'core/verify_otp.html')

def reset_password(request):
    if not request.session.get('reset_otp'):
        return redirect('forgot_password')
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            email = request.session.get('reset_email')
            user = CustomUser.objects.get(email=email)
            user.set_password(password)
            user.save()
            
            # Clear session
            del request.session['reset_otp']
            del request.session['reset_email']
            
            messages.success(request, 'Password reset successful! Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')
            
    return render(request, 'core/reset_password.html')

@login_required
def my_applications(request):
    """View for candidates to see their applied jobs"""
    if request.user.is_hr:
        return redirect('hr_dashboard')
    
    my_applications_list = Application.objects.filter(candidate=request.user).order_by('-applied_at')
    
    from django.core.paginator import Paginator
    paginator = Paginator(my_applications_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    return render(request, 'core/my_applications.html', {
        'my_applications': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages()
    })

@hr_required
def candidate_detail_view(request, candidate_id):
    candidate = get_object_or_404(CustomUser, id=candidate_id, is_candidate=True)
    try:
        profile = candidate.candidate_profile
    except CandidateProfile.DoesNotExist:
        messages.error(request, "Candidate profile not found.")
        return redirect('hr_dashboard')

    return render(request, 'core/profile_detail.html', {
        'profile': profile,
        'user': candidate, # Override 'user' in context
        'is_hr_view': True
    })

@login_required
def chatbot_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('message')
            if prompt:
                response = get_sambanova_response(prompt)
                return JsonResponse({'response': response})
            return JsonResponse({'error': 'No message provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=405)

# Footer page views
def about_us(request):
    """About Us page"""
    return render(request, 'core/about_us.html')

def contact(request):
    """Contact page"""
    return render(request, 'core/contact.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'core/privacy_policy.html')

def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'core/terms_of_service.html')

def career_resources(request):
    """Career Resources page"""
    return render(request, 'core/career_resources.html')

def pricing(request):
    """Pricing page"""
    return render(request, 'core/pricing.html')

@hr_required
def hr_profile_view(request):
    """View HR profile details"""
    try:
        profile = request.user.hr_profile
    except HRProfile.DoesNotExist:
        profile = HRProfile.objects.create(user=request.user)
    
    return render(request, 'core/hr_profile_detail.html', {'profile': profile})

@hr_required
def hr_update_profile(request):
    """Edit HR profile"""
    try:
        profile = request.user.hr_profile
    except HRProfile.DoesNotExist:
        profile = HRProfile(user=request.user)
        
    if request.method == 'POST':
        form = HRProfileForm(request.POST, request.FILES, instance=profile)
        # Handle user name and company name updates manually
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company_name = request.POST.get('company_name')
        
        if form.is_valid():
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.company_name = company_name
            user.save()
            
            form.save()
            from django.contrib import messages
            messages.success(request, 'Profile updated successfully!')
            return redirect('hr_profile_view')
    else:
        form = HRProfileForm(instance=profile)
        
    return render(request, 'core/hr_profile_form.html', {
        'form': form,
        'user': request.user
    })
