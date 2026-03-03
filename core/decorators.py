from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from functools import wraps

def hr_required(function=None, redirect_url='/'):
    """
    Decorator for views that checks that the user is an HR user
    (is_hr=True and is_staff=False), redirecting to the redirect_url if necessary.
    """
    def check_hr(user):
        return user.is_authenticated and user.is_hr and not user.is_superuser
    
    actual_decorator = user_passes_test(check_hr, login_url=redirect_url)
    
    if function:
        return actual_decorator(function)
    return actual_decorator

def candidate_required(function=None, redirect_url='/'):
    """
    Decorator for views that checks that the user is a candidate
    (is_candidate=True), redirecting to the redirect_url if necessary.
    """
    def check_candidate(user):
        return user.is_authenticated and user.is_candidate
    
    actual_decorator = user_passes_test(check_candidate, login_url=redirect_url)
    
    if function:
        return actual_decorator(function)
    return actual_decorator

def superuser_required(function=None, redirect_url='/'):
    """
    Decorator for views that checks that the user is a superuser,
    redirecting to the redirect_url if necessary.
    """
    def check_superuser(user):
        return user.is_authenticated and user.is_superuser
    
    actual_decorator = user_passes_test(check_superuser, login_url=redirect_url)
    
    if function:
        return actual_decorator(function)
    return actual_decorator
