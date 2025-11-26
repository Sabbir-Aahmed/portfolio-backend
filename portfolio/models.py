from django.db import models
import uuid
from cloudinary.models import CloudinaryField

class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    
    pdf_file = CloudinaryField(resource_type='raw', folder='resumes/', blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}"

class Experience(models.Model):
    resume = models.ForeignKey(Resume, related_name='experiences', on_delete=models.CASCADE)
    company = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} at {self.company}"

class Education(models.Model):
    resume = models.ForeignKey(Resume, related_name='educations', on_delete=models.CASCADE)
    institution = models.CharField(max_length=255, null=True, blank=True)
    degree = models.CharField(max_length=255, null=True, blank=True)
    field_of_study = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.degree} at {self.institution}"

class Skill(models.Model):
    SKILL_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    resume = models.ForeignKey(Resume, related_name='skills', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, default='intermediate')
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

class ResumeProject(models.Model):
    resume = models.ForeignKey(Resume, related_name='resume_projects', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    technologies = models.JSONField(default=list)
    project_url = models.URLField(blank=True, null=True)
    github_client = models.URLField(blank=True, null=True)
    github_server = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class PortfolioProject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    short_description = models.CharField(max_length=300, null=True, blank=True)
    image = CloudinaryField('image', folder='projects/', blank=True, null=True)
    technologies = models.JSONField(default=list, blank=True)
    live_link = models.URLField(blank=True, null=True)
    github_client = models.URLField(blank=True, null=True)
    github_server = models.URLField(blank=True, null=True)
    featured = models.BooleanField(default=False)
    completed_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-featured', '-completed_date']
        verbose_name = 'Portfolio Project'
        verbose_name_plural = 'Portfolio Projects'

    def __str__(self):
        return self.title

    def get_technologies_display(self):
        return ", ".join(self.technologies) if self.technologies else ""