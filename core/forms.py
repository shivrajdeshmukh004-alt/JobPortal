from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import JobPost, Application, CandidateProfile, CustomUser, HRProfile
from ckeditor.widgets import CKEditorWidget

class HRSignupForm(UserCreationForm):
    """Registration form for HR users"""
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    company_name = forms.CharField(max_length=200, required=True, help_text="Your company or organization name")
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'company_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_hr = True
        user.is_candidate = False
        user.company_name = self.cleaned_data['company_name']
        user.is_staff = False  # CRITICAL: HR users are NOT staff
        if commit:
            user.save()
        return user

class CandidateSignupForm(UserCreationForm):
    """Registration form for Candidate users"""
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_candidate = True
        user.is_hr = False
        user.is_staff = False
        if commit:
            user.save()
        return user

class JobPostForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = JobPost
        fields = [
            'title', 'company_name', 'description', 'location', 'eligibility', 
            'required_skills', 'vacancy', 'expiry_date',
            'min_tenth_percentage', 'min_twelfth_percentage', 'min_degree_percentage',
            'min_age', 'max_age'
        ]
        widgets = {
            'required_skills': forms.HiddenInput(),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'min_tenth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': 'e.g., 60'}),
            'min_twelfth_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': 'e.g., 70'}),
            'min_degree_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'placeholder': 'e.g., 75'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '18', 'max': '100', 'placeholder': 'e.g., 21'}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '18', 'max': '100', 'placeholder': 'e.g., 35'}),
        }
        help_texts = {
            'min_tenth_percentage': 'Minimum percentage required in 10th standard (optional)',
            'min_twelfth_percentage': 'Minimum percentage required in 12th/Diploma (optional)',
            'min_degree_percentage': 'Minimum percentage required in degree (optional)',
            'min_age': 'Minimum age requirement in years (optional)',
            'max_age': 'Maximum age limit in years (optional)',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        
        # Validate that min_age < max_age if both are provided
        if min_age and max_age and min_age >= max_age:
            raise forms.ValidationError("Minimum age must be less than maximum age.")
        
        return cleaned_data

class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = [
            'profile_photo', 'master_resume', 'skills', 'education', 
            'contact', 'dob', 'gender', 'projects', 'linkedin_url', 'github_url'
        ]
        widgets = {
            'skills': forms.HiddenInput(),  # We will use a custom UI for skills
            'education': forms.HiddenInput(),  # We will use a custom UI for education
            'projects': forms.HiddenInput(),  # We will use a custom UI for projects
            'linkedin_url': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github_url': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
        }

class HRProfileForm(forms.ModelForm):
    class Meta:
        model = HRProfile
        fields = [
            'profile_photo', 'company_description', 'industry', 'company_size',
            'location', 'contact', 'website_url', 'linkedin_url', 'founded_year'
        ]
        widgets = {
            'company_description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Tell us about your company, its mission, and what makes it unique...'
            }),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mumbai, Maharashtra'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 99999-99999'
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.yourcompany.com'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/company/yourcompany'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2010',
                'min': '1800',
                'max': '2026'
            }),
        }

