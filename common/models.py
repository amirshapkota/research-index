from django.db import models


class Contact(models.Model):
    ENQUIRY_TYPE_CHOICES = [
        ('general', 'General Enquiry'),
        ('technical', 'Technical Support'),
        ('partnership', 'Partnership Opportunity'),
        ('feedback', 'Feedback'),
        ('complaint', 'Complaint'),
        ('other', 'Other'),
    ]
    
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    contact_number = models.CharField(max_length=20)
    institution_name = models.CharField(max_length=200)
    enquiry_type = models.CharField(max_length=20, choices=ENQUIRY_TYPE_CHOICES)
    subject = models.CharField(max_length=300)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Enquiry'
        verbose_name_plural = 'Contact Enquiries'
    
    def __str__(self):
        return f"{self.full_name} - {self.subject}"

