from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'institution_name', 'enquiry_type', 'subject', 'created_at', 'is_resolved']
    list_filter = ['enquiry_type', 'is_resolved', 'created_at']
    search_fields = ['full_name', 'email', 'institution_name', 'subject', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_resolved']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'contact_number', 'institution_name')
        }),
        ('Enquiry Details', {
            'fields': ('enquiry_type', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('is_resolved', 'created_at')
        }),
    )

