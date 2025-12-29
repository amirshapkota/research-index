from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id',
            'full_name',
            'email',
            'contact_number',
            'institution_name',
            'enquiry_type',
            'subject',
            'message',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_contact_number(self, value):
        """Validate contact number format"""
        if not value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise serializers.ValidationError("Please enter a valid contact number.")
        return value

