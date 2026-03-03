from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import HRSignupForm, CandidateSignupForm

class CustomLoginView(LoginView):
    """
    Custom login view that redirects users based on their role.
    This is the 'traffic cop' that routes users to their appropriate portals.
    """
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        """Redirect based on user role"""
        user = self.request.user
        
        if user.is_superuser:
            return reverse_lazy('admin:index')
        elif user.is_hr:
            return reverse_lazy('hr_dashboard')
        elif user.is_candidate:
            return reverse_lazy('candidate_dashboard')
        else:
            # Fallback for users without a role
            return reverse_lazy('dashboard')

@login_required
def dashboard_redirect(request):
    """
    Traffic cop view that redirects authenticated users to their respective portals.
    This ensures users always land on the correct dashboard.
    """
    user = request.user
    
    if user.is_superuser:
        return redirect('admin:index')
    elif user.is_hr:
        return redirect('hr_dashboard')
    elif user.is_candidate:
        return redirect('candidate_dashboard')
    else:
        # User has no role assigned - show error or setup page
        return render(request, 'auth/no_role.html')

def hr_signup(request):
    """Registration view for HR users"""
    if request.method == 'POST':
        form = HRSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('hr_dashboard')
    else:
        form = HRSignupForm()
    
    return render(request, 'auth/hr_signup.html', {'form': form})

def candidate_signup(request):
    """Registration view for Candidate users"""
    if request.method == 'POST':
        form = CandidateSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('candidate_dashboard')
    else:
        form = CandidateSignupForm()
    
    return render(request, 'auth/candidate_signup.html', {'form': form})
