"""
Serializers for imported user account claiming functionality.
Allows imported authors and institutions to claim their accounts.
"""

from rest_framework import serializers
from ....models import CustomUser, Author, Institution
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


class SearchImportedAuthorsSerializer(serializers.Serializer):
    """
    Serializer for searching imported author profiles.
    Only authors are imported and need account claiming.
    Institutions are created via journal claiming.
    """
    search_query = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Search by name, ORCID, or institution name"
    )


class ImportedAuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying imported author profiles.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    
    class Meta:
        model = Author
        fields = [
            'id', 'user_id', 'email', 'title', 'full_name', 
            'institute', 'designation', 'orcid', 'is_active'
        ]
        read_only_fields = fields


# Institution account claiming removed - institutions are NOT imported
# Institutions are created through journal claiming instead
        read_only_fields = fields


class ClaimAuthorAccountSerializer(serializers.Serializer):
    """
    Serializer for claiming an imported author account.
    """
    author_id = serializers.IntegerField(
        required=True,
        help_text="ID of the imported author profile to claim"
    )
    new_email = serializers.EmailField(
        required=True,
        help_text="New email address for the account"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="New password for the account"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm password"
    )
    
    # Optional fields to update profile
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    research_interests = serializers.CharField(required=False, allow_blank=True)
    google_scholar = serializers.URLField(required=False, allow_blank=True)
    researchgate = serializers.URLField(required=False, allow_blank=True)
    linkedin = serializers.URLField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    
    def validate(self, data):
        """
        Validate the claim request.
        """
        # Verify passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        
        # Validate password strength
        try:
            validate_password(data['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        # Check if author exists and is inactive (imported)
        try:
            author = Author.objects.select_related('user').get(id=data['author_id'])
            if author.user.is_active:
                raise serializers.ValidationError({
                    'author_id': 'This account has already been claimed'
                })
            data['author'] = author
        except Author.DoesNotExist:
            raise serializers.ValidationError({
                'author_id': 'Author not found'
            })
        
        # Check if new email is already in use
        if CustomUser.objects.filter(email=data['new_email']).exclude(id=author.user.id).exists():
            raise serializers.ValidationError({
                'new_email': 'This email is already registered'
            })
        
        return data
    
    def save(self):
        """
        Claim the imported author account.
        """
        author = self.validated_data['author']
        user = author.user
        
        # Update user credentials
        user.email = self.validated_data['new_email']
        user.set_password(self.validated_data['password'])
        user.is_active = True
        user.save()
        
        # Update author profile with optional fields
        if 'bio' in self.validated_data:
            author.bio = self.validated_data['bio']
        if 'research_interests' in self.validated_data:
            author.research_interests = self.validated_data['research_interests']
        if 'google_scholar' in self.validated_data:
            author.google_scholar = self.validated_data['google_scholar']
        if 'researchgate' in self.validated_data:
            author.researchgate = self.validated_data['researchgate']
        if 'linkedin' in self.validated_data:
            author.linkedin = self.validated_data['linkedin']
        if 'website' in self.validated_data:
            author.website = self.validated_data['website']
        
        author.save()
        
        return user


# ClaimInstitutionAccountSerializer REMOVED
# Institutions are NOT imported - they are created via journal claiming instead
# See users/serializers_journal_claim.py for journal claiming with institution creation