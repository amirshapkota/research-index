from django.db import models
from django.contrib.auth.models import AbstractUser
    
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('author', 'Author'),
        ('institution', 'Institution'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    full_name = models.CharField(max_length=200)
    institute = models.CharField(max_length=200, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

