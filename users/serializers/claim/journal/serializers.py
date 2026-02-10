"""
Serializers for journal claiming functionality.
Allows institutions to claim ownership of imported journals.
This can be done either by creating a new institution OR by an existing institution.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from publications.models import Journal
from users.models import Institution, CustomUser


class SearchClaimableJournalsSerializer(serializers.Serializer):
    """
    Serializer for searching claimable journals.
    """
    search_query = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Search by journal title, ISSN, or publisher name"
    )


class ClaimableJournalSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying claimable journals.
    """
    current_owner = serializers.CharField(source='institution.institution_name', read_only=True)
    current_owner_email = serializers.EmailField(source='institution.user.email', read_only=True)
    
    class Meta:
        model = Journal
        fields = [
            'id', 'title', 'short_title', 'issn', 'e_issn',
            'publisher_name', 'description', 'website',
            'established_year', 'frequency', 'language',
            'current_owner', 'current_owner_email'
        ]


class ClaimJournalSerializer(serializers.Serializer):
    """
    Serializer for claiming a journal.
    Requires authentication - only active institutions can claim journals.
    """
    journal_id = serializers.IntegerField(
        required=True,
        help_text="ID of the journal to claim"
    )
    
    def validate_journal_id(self, value):
        """Validate that the journal exists and can be claimed."""
        try:
            journal = Journal.objects.get(id=value)
        except Journal.DoesNotExist:
            raise serializers.ValidationError("Journal not found")
        
        # Check if journal belongs to an inactive system institution
        if journal.institution.user.is_active:
            raise serializers.ValidationError(
                "This journal is already owned by an active institution and cannot be claimed"
            )
        
        # Check if it's a system institution (import placeholder)
        if 'system.institution' not in journal.institution.user.email:
            raise serializers.ValidationError(
                "This journal cannot be claimed through this process"
            )
        
        return value
    
    def validate(self, data):
        """Additional validation at the serializer level."""
        # The institution claiming the journal is passed in context
        institution = self.context.get('institution')
        if not institution:
            raise serializers.ValidationError("No institution found in context")
        
        if not institution.user.is_active:
            raise serializers.ValidationError("Only active institutions can claim journals")
        
        journal_id = data['journal_id']
        journal = Journal.objects.get(id=journal_id)
        
        # Check if institution already owns this journal somehow
        if journal.institution == institution:
            raise serializers.ValidationError("You already own this journal")
        
        return data


class ClaimJournalsWithInstitutionSerializer(serializers.Serializer):
    """
    Serializer for claiming journals while creating a new institution account.
    This is the primary way institutions are created - by claiming imported journals.
    """
    # Institution account details
    email = serializers.EmailField(
        required=True,
        help_text="Email address for the institution account"
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password for the new account"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm password"
    )
    
    # Institution profile fields (required)
    institution_name = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Name of the institution"
    )
    institution_type = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="Type (e.g., University, Research Center)"
    )
    country = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    
    # Institution profile fields (optional)
    description = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    research_areas = serializers.CharField(required=False, allow_blank=True)
    total_researchers = serializers.IntegerField(required=False, allow_null=True)
    
    # Journals to claim (can be multiple)
    journal_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False,
        help_text="List of journal IDs to claim"
    )
    
    def validate(self, data):
        """Validate the claim request."""
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
        
        # Check if email is already in use
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'This email is already registered'
            })
        
        # Validate all journals exist and can be claimed
        journal_ids = data['journal_ids']
        journals = Journal.objects.filter(id__in=journal_ids)
        
        if journals.count() != len(journal_ids):
            found_ids = set(journals.values_list('id', flat=True))
            missing_ids = set(journal_ids) - found_ids
            raise serializers.ValidationError({
                'journal_ids': f'Journals not found: {list(missing_ids)}'
            })
        
        # Check all journals can be claimed
        for journal in journals:
            if journal.institution.user.is_active:
                raise serializers.ValidationError({
                    'journal_ids': f'Journal "{journal.title}" is already owned by an active institution'
                })
            
            if 'system.institution' not in journal.institution.user.email:
                raise serializers.ValidationError({
                    'journal_ids': f'Journal "{journal.title}" cannot be claimed through this process'
                })
        
        data['journals'] = journals
        return data
    
    def save(self):
        """Create institution account and claim journals."""
        with transaction.atomic():
            # Create user account
            user = CustomUser.objects.create_user(
                email=self.validated_data['email'],
                password=self.validated_data['password'],
                user_type='institution',
                is_active=True
            )
            
            # Create institution profile
            institution = Institution.objects.create(
                user=user,
                institution_name=self.validated_data['institution_name'],
                institution_type=self.validated_data.get('institution_type', ''),
                country=self.validated_data.get('country', ''),
                description=self.validated_data.get('description', ''),
                address=self.validated_data.get('address', ''),
                city=self.validated_data.get('city', ''),
                state=self.validated_data.get('state', ''),
                postal_code=self.validated_data.get('postal_code', ''),
                phone=self.validated_data.get('phone', ''),
                website=self.validated_data.get('website', ''),
                research_areas=self.validated_data.get('research_areas', ''),
                total_researchers=self.validated_data.get('total_researchers'),
            )
            
            # Transfer all journals to new institution
            journals = self.validated_data['journals']
            journals.update(institution=institution)
            
            return {
                'user': user,
                'institution': institution,
                'journals_claimed': journals.count(),
                'journal_titles': list(journals.values_list('title', flat=True))
            }
