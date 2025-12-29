from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ('author', 'Author'),
        ('institution', 'Institution'),
        ('admin', 'Admin'),
    ]
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']
    
    def __str__(self):
        return self.email


class Author(models.Model):
    TITLE_CHOICES = [
        ('Dr.', 'Dr.'),
        ('Prof.', 'Prof.'),
        ('Mr.', 'Mr.'),
        ('Ms.', 'Ms.'),
        ('Mrs.', 'Mrs.'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='author_profile')
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    full_name = models.CharField(max_length=200)
    institute = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    
    degree = models.CharField(max_length=200, blank=True, help_text="Highest degree (e.g., PhD in Computer Science)")
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/authors/', blank=True, null=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True, help_text="Upload CV (PDF recommended)")
    
    # Research profile fields
    bio = models.TextField(blank=True, help_text="Short biography")
    research_interests = models.TextField(blank=True, help_text="Research areas and interests")
    orcid = models.CharField(max_length=50, blank=True, help_text="ORCID ID")
    google_scholar = models.URLField(blank=True, help_text="Google Scholar profile URL")
    researchgate = models.URLField(blank=True, help_text="ResearchGate profile URL")
    linkedin = models.URLField(blank=True, help_text="LinkedIn profile URL")
    website = models.URLField(blank=True, help_text="Personal/academic website")
    
    def __str__(self):
        return f"{self.title} {self.full_name}"


class Institution(models.Model):
    INSTITUTION_TYPE_CHOICES = [
        ('university', 'University'),
        ('research_institute', 'Research Institute'),
        ('government', 'Government Organization'),
        ('private', 'Private Research Organization'),
        ('industry', 'Industry/Corporate R&D'),
        ('hospital', 'Hospital/Medical Center'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='institution_profile')
    institution_name = models.CharField(max_length=200)
    
    # New fields
    institution_type = models.CharField(max_length=30, choices=INSTITUTION_TYPE_CHOICES, blank=True)
    logo = models.ImageField(upload_to='profiles/institutions/', blank=True, null=True)
    description = models.TextField(blank=True, help_text="About the institution")
    
    # Contact & Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Online presence
    website = models.URLField(blank=True)
    established_year = models.PositiveIntegerField(blank=True, null=True, help_text="Year established")
    
    # Research info
    research_areas = models.TextField(blank=True, help_text="Main research areas")
    total_researchers = models.PositiveIntegerField(blank=True, null=True, help_text="Number of researchers")
    
    def __str__(self):
        return self.institution_name


