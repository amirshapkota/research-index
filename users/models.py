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
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='author_profile')
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    full_name = models.CharField(max_length=200)
    institute = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.title} {self.full_name}"


class Institution(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='institution_profile')
    institution_name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.institution_name

