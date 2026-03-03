from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .auth_views import CustomLoginView, dashboard_redirect, hr_signup, candidate_signup

urlpatterns = [
    # Diagnostic (TEMPORARY - remove after email works)
    path('test-email/', views.test_email, name='test_email'),
    
    # Public Authentication Routes
    path('', dashboard_redirect, name='dashboard'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/hr/', hr_signup, name='hr_signup'),
    path('signup/candidate/', candidate_signup, name='candidate_signup'),
    
    # Password Reset (OTP)
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # HR Portal (Professional - NOT Admin)
    path('hr/dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/profile/', views.hr_profile_view, name='hr_profile_view'),
    path('hr/profile/edit/', views.hr_update_profile, name='hr_update_profile'),
    path('hr/jobs/create/', views.create_job, name='create_job'),
    path('hr/jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('hr/jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('hr/jobs/<int:job_id>/applicants/', views.job_applicants, name='job_applicants'),
    path('hr/applications/<int:application_id>/shortlist/', views.shortlist_candidate, name='shortlist_candidate'),
    path('hr/applications/<int:application_id>/reject/', views.reject_candidate, name='reject_candidate'),
    path('hr/jobs/<int:job_id>/next-round/', views.manage_next_round, name='manage_next_round'),
    path('hr/applications/<int:application_id>/second-round/', views.send_to_second_round, name='send_to_second_round'),
    path('hr/jobs/<int:job_id>/bulk-applicants/', views.bulk_manage_applicants, name='bulk_manage_applicants'),
    path('hr/candidate/<int:candidate_id>/profile/', views.candidate_detail_view, name='candidate_detail_view'),
    
    # Candidate Portal
    path('candidate/home/', views.candidate_dashboard, name='candidate_dashboard'),
    path('candidate/apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('candidate/profile/', views.profile_view, name='profile_view'),
    path('candidate/profile/edit/', views.update_profile, name='update_profile'),
    path('candidate/profile/password/', views.password_change, name='password_change'),
    path('candidate/applications/', views.my_applications, name='my_applications'),
    path('api/chatbot/', views.chatbot_response, name='chatbot_response'),
    
    # Footer Pages
    path('about/', views.about_us, name='about_us'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('resources/', views.career_resources, name='career_resources'),
    path('pricing/', views.pricing, name='pricing'),
]
