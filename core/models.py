from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from ckeditor.fields import RichTextField

class CustomUser(AbstractUser):
    pass
    # Basic user type flags
    is_hr = models.BooleanField(default=False)
    is_candidate = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True)
    
    # We can use email as the unique identifier if desired, but 
    # AbstractUser uses username by default. 
    # Let's enforce email is unique.
    email = models.EmailField(unique=True)

class CandidateProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='candidate_profile')
    profile_photo = CloudinaryField('image', blank=True, null=True)
    master_resume = CloudinaryField('resume', resource_type='raw', blank=True, null=True) 
    skills = models.TextField(help_text="Comma separated skills", blank=True)
    education = models.JSONField(default=dict, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    projects = models.JSONField(default=list, blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Profile: {self.user.username}"

    @property
    def completeness(self):
        fields = [
            self.profile_photo, self.master_resume, self.skills, 
            self.education, self.contact, self.dob, self.gender, self.projects
        ]
        filled = [f for f in fields if f]
        # Include first/last name from user
        if self.user.first_name: filled.append(True)
        if self.user.last_name: filled.append(True)
        
        total_fields = len(fields) + 2
        return int((len(filled) / total_fields) * 100)

class HRProfile(models.Model):
    INDUSTRY_CHOICES = [
        ('IT', 'Information Technology'),
        ('Finance', 'Finance & Banking'),
        ('Healthcare', 'Healthcare'),
        ('Education', 'Education'),
        ('Manufacturing', 'Manufacturing'),
        ('Retail', 'Retail & E-commerce'),
        ('Consulting', 'Consulting'),
        ('Other', 'Other'),
    ]
    
    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='hr_profile')
    profile_photo = CloudinaryField('image', blank=True, null=True)
    company_description = models.TextField(blank=True, help_text="Brief description of your company")
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, blank=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True)
    location = models.CharField(max_length=200, blank=True, help_text="Company headquarters location")
    contact = models.CharField(max_length=20, blank=True, help_text="Contact number")
    website_url = models.URLField(blank=True, null=True, help_text="Company website")
    linkedin_url = models.URLField(blank=True, null=True, help_text="Company LinkedIn page")
    founded_year = models.IntegerField(blank=True, null=True, help_text="Year company was founded")
    
    def __str__(self):
        return f"HR Profile: {self.user.username}"
    
    @property
    def completeness(self):
        fields = [
            self.profile_photo, self.company_description, self.industry,
            self.company_size, self.location, self.contact, self.website_url,
            self.linkedin_url, self.founded_year
        ]
        filled = [f for f in fields if f]
        # Include first/last name and company_name from user
        if self.user.first_name: filled.append(True)
        if self.user.last_name: filled.append(True)
        if self.user.company_name: filled.append(True)
        
        total_fields = len(fields) + 3
        return int((len(filled) / total_fields) * 100)

class JobPost(models.Model):
    recruiter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_jobs')
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, default='RecruitAICorp')
    description = RichTextField()
    location = models.CharField(max_length=100)
    eligibility = models.CharField(max_length=200, blank=True)
    required_skills = models.TextField(help_text="Comma separated required skills", blank=True)
    vacancy = models.IntegerField(default=1)
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Deadline for applications")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Eligibility Criteria (Optional)
    min_tenth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Minimum 10th percentage required")
    min_twelfth_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Minimum 12th/Diploma percentage required")
    min_degree_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Minimum degree percentage required")
    min_age = models.IntegerField(null=True, blank=True, help_text="Minimum age required")
    max_age = models.IntegerField(null=True, blank=True, help_text="Maximum age allowed")
    
    def __str__(self):
        return self.title
    
    def check_eligibility(self, candidate_profile):
        """
        Check if a candidate is eligible for this job based on academic percentages and age.
        Returns a dict with 'eligible' (bool) and 'reasons' (list of strings).
        """
        from datetime import date
        
        reasons = []
        eligible = True
        
        # Check education percentages
        education = candidate_profile.education if isinstance(candidate_profile.education, dict) else {}
        
        # Check 10th percentage
        if self.min_tenth_percentage:
            tenth_data = education.get('tenth', {})
            tenth_percentage = tenth_data.get('percentage', 0)
            try:
                tenth_percentage = float(tenth_percentage) if tenth_percentage else 0
            except (ValueError, TypeError):
                tenth_percentage = 0
            
            if tenth_percentage < float(self.min_tenth_percentage):
                eligible = False
                reasons.append(f"Requires minimum {self.min_tenth_percentage}% in 10th standard")
        
        # Check 12th percentage
        if self.min_twelfth_percentage:
            twelfth_data = education.get('twelfth', {})
            twelfth_percentage = twelfth_data.get('percentage', 0)
            try:
                twelfth_percentage = float(twelfth_percentage) if twelfth_percentage else 0
            except (ValueError, TypeError):
                twelfth_percentage = 0
            
            if twelfth_percentage < float(self.min_twelfth_percentage):
                eligible = False
                reasons.append(f"Requires minimum {self.min_twelfth_percentage}% in 12th/Diploma")
        
        # Check degree percentage
        if self.min_degree_percentage:
            degree_data = education.get('degree', {})
            degree_score = degree_data.get('score', 0)
            try:
                degree_score = float(degree_score) if degree_score else 0
            except (ValueError, TypeError):
                degree_score = 0
            
            if degree_score < float(self.min_degree_percentage):
                eligible = False
                reasons.append(f"Requires minimum {self.min_degree_percentage}% in degree")
        
        # Check age
        if self.min_age or self.max_age:
            if candidate_profile.dob:
                today = date.today()
                age = today.year - candidate_profile.dob.year - ((today.month, today.day) < (candidate_profile.dob.month, candidate_profile.dob.day))
                
                if self.min_age and age < self.min_age:
                    eligible = False
                    reasons.append(f"Minimum age requirement: {self.min_age} years")
                
                if self.max_age and age > self.max_age:
                    eligible = False
                    reasons.append(f"Maximum age limit: {self.max_age} years")
            else:
                # If DOB not provided, consider ineligible if age criteria exists
                if self.min_age or self.max_age:
                    eligible = False
                    reasons.append("Date of birth not provided in profile")
        
        return {
            'eligible': eligible,
            'reasons': reasons
        }

class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('SECOND_ROUND', 'Second Round'),
        ('REJECTED', 'Rejected'),
        ('SELECTED', 'Selected'),
    )
    
    candidate = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    score = models.FloatField(default=0.0)
    applied_at = models.DateTimeField(auto_now_add=True)
    resume = CloudinaryField('resume_snapshot', resource_type='raw', blank=True, null=True)
    
    # New fields for Second Round
    interview_name = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Technical Assessment, HR Round")
    interview_link = models.URLField(max_length=500, blank=True, null=True)
    interview_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('candidate', 'job')

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title}"
