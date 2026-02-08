from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Author, Institution, AuthorStats, InstitutionStats, AdminStats, Follow


class AuthorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    title = serializers.ChoiceField(choices=Author.TITLE_CHOICES)
    full_name = serializers.CharField(max_length=200)
    institute = serializers.CharField(max_length=200)
    designation = serializers.CharField(max_length=100)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirm_password', 'title', 'full_name', 'institute', 'designation']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Remove confirm_password and author-specific fields
        validated_data.pop('confirm_password')
        title = validated_data.pop('title')
        full_name = validated_data.pop('full_name')
        institute = validated_data.pop('institute')
        designation = validated_data.pop('designation')
        
        # Create user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type='author'
        )
        
        # Create author profile
        Author.objects.create(
            user=user,
            title=title,
            full_name=full_name,
            institute=institute,
            designation=designation
        )
        
        return user


class InstitutionRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    institution_name = serializers.CharField(max_length=200)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirm_password', 'institution_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Remove confirm_password and institution-specific fields
        validated_data.pop('confirm_password')
        institution_name = validated_data.pop('institution_name')
        
        # Create user
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            user_type='institution'
        )
        
        # Create institution profile
        Institution.objects.create(
            user=user,
            institution_name=institution_name
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AuthorStatsSerializer(serializers.ModelSerializer):
    """Serializer for author statistics"""
    
    class Meta:
        model = AuthorStats
        fields = [
            'h_index',
            'i10_index',
            'total_citations',
            'total_reads',
            'total_downloads',
            'recommendations_count',
            'total_publications',
            'average_citations_per_paper',
            'last_updated',
        ]
        read_only_fields = fields


class CoAuthorSerializer(serializers.Serializer):
    """Serializer for co-author information"""
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    institute = serializers.CharField(allow_null=True)
    is_registered = serializers.BooleanField()


class InstitutionStatsSerializer(serializers.ModelSerializer):
    """Serializer for institution statistics"""
    compared_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = InstitutionStats
        fields = [
            'total_publications',
            'total_citations',
            'average_citations_per_paper',
            'total_reads',
            'total_downloads',
            'recommendations_count',
            'total_authors',
            'last_updated',
            'compared_summary',
        ]
        read_only_fields = fields
    
    def get_compared_summary(self, obj):
        """
        Generate comparison summary text based on institution's percentile rank.
        Compares total_citations against all institutions.
        """
        from django.db.models import Count
        
        # Get total number of institutions with stats
        total_institutions = InstitutionStats.objects.count()
        
        if total_institutions <= 1:
            return f"{obj.institution.institution_name}'s research contribution reflects consistent dedication, impactful publications, and an influential role in advancing research and education in Nepal."
        
        # Count institutions with lower total_citations
        institutions_below = InstitutionStats.objects.filter(
            total_citations__lt=obj.total_citations
        ).count()
        
        # Calculate percentile (what percentage of institutions this institution is better than)
        percentile = round((institutions_below / (total_institutions - 1)) * 100)
        
        # Determine if higher or lower
        if percentile >= 50:
            comparison = "higher"
            # For institutions in top 50%, compare to those below
            comparison_percentile = percentile
        else:
            comparison = "lower"
            # For institutions in bottom 50%, compare to those above
            comparison_percentile = 100 - percentile
        
        # Generate dynamic text based on percentile
        if percentile >= 90:
            descriptor = "exceptional dedication, highly impactful publications, and a leading role"
        elif percentile >= 75:
            descriptor = "outstanding dedication, impactful publications, and an influential role"
        elif percentile >= 50:
            descriptor = "consistent dedication, impactful publications, and an influential role"
        elif percentile >= 25:
            descriptor = "ongoing dedication, meaningful publications, and a contributing role"
        else:
            descriptor = "growing dedication, emerging publications, and a developing role"
        
        return (
            f"{obj.institution.institution_name}'s research contribution is {comparison} than "
            f"{comparison_percentile}% of Nepal Research Index members, reflecting {descriptor} "
            f"in advancing research and education in Nepal."
        )


class AdminStatsSerializer(serializers.ModelSerializer):
    """Serializer for admin system-wide statistics"""
    
    class Meta:
        model = AdminStats
        fields = [
            'total_users',
            'total_authors',
            'total_institutions',
            'total_publications',
            'published_count',
            'draft_count',
            'total_citations',
            'total_reads',
            'total_downloads',
            'total_journals',
            'total_topics',
            'last_updated',
        ]
        read_only_fields = fields


class AuthorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    cv_url = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    coauthors = serializers.SerializerMethodField()
    collaboration_count = serializers.IntegerField(source='get_collaboration_count', read_only=True)
    
    class Meta:
        model = Author
        fields = [
            'id',
            'email',
            'user_type',
            'title',
            'full_name',
            'institute',
            'designation',
            'degree',
            'gender',
            'profile_picture',
            'profile_picture_url',
            'cv',
            'cv_url',
            'bio',
            'research_interests',
            'orcid',
            'google_scholar',
            'researchgate',
            'linkedin',
            'website',
            'stats',
            'coauthors',
            'collaboration_count',
        ]
        read_only_fields = ['id', 'email', 'user_type', 'stats', 'coauthors', 'collaboration_count']
    
    def to_representation(self, instance):
        """Convert research_interests string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_interests'):
            data['research_interests'] = [
                interest.strip() 
                for interest in data['research_interests'].split(',') 
                if interest.strip()
            ]
        else:
            data['research_interests'] = []
        return data
    
    def to_internal_value(self, data):
        """Convert research_interests array to comma-separated string"""
        if 'research_interests' in data and isinstance(data['research_interests'], list):
            data = data.copy()
            data['research_interests'] = ', '.join(filter(None, data['research_interests']))
        return super().to_internal_value(data)
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_cv_url(self, obj):
        if obj.cv:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv.url)
            return obj.cv.url
        return None
    
    def get_stats(self, obj):
        """Get or create author stats"""
        stats, created = AuthorStats.objects.get_or_create(author=obj)
        if created or not stats.last_updated:
            # Update stats if newly created or never updated
            stats.update_stats()
        return AuthorStatsSerializer(stats).data
    
    def get_coauthors(self, obj):
        """Get list of co-authors"""
        coauthors = obj.get_coauthors()
        return CoAuthorSerializer(coauthors, many=True).data


class InstitutionProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    logo_url = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'id',
            'email',
            'user_type',
            'institution_name',
            'institution_type',
            'logo',
            'logo_url',
            'description',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'phone',
            'website',
            'established_year',
            'research_areas',
            'total_researchers',
            'stats',
        ]
        read_only_fields = ['id', 'email', 'user_type', 'stats']
    
    def to_representation(self, instance):
        """Convert research_areas string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_areas'):
            data['research_areas'] = [
                area.strip() 
                for area in data['research_areas'].split(',') 
                if area.strip()
            ]
        else:
            data['research_areas'] = []
        return data
    
    def to_internal_value(self, data):
        """Convert research_areas array to comma-separated string"""
        if 'research_areas' in data and isinstance(data['research_areas'], list):
            data = data.copy()
            data['research_areas'] = ', '.join(filter(None, data['research_areas']))
        return super().to_internal_value(data)
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_stats(self, obj):
        """Get or create institution stats"""
        stats, created = InstitutionStats.objects.get_or_create(institution=obj)
        if created or not stats.last_updated:
            # Update stats if newly created or never updated
            stats.update_stats()
        return InstitutionStatsSerializer(stats).data


class InstitutionListSerializer(serializers.ModelSerializer):
    """Serializer for listing institutions publicly."""
    logo_url = serializers.SerializerMethodField()
    journals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'id',
            'institution_name',
            'institution_type',
            'logo_url',
            'description',
            'city',
            'state',
            'country',
            'website',
            'established_year',
            'research_areas',
            'journals_count',
        ]
    
    def to_representation(self, instance):
        """Convert research_areas string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_areas'):
            data['research_areas'] = [
                area.strip() 
                for area in data['research_areas'].split(',') 
                if area.strip()
            ]
        else:
            data['research_areas'] = []
        return data
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_journals_count(self, obj):
        return obj.journals.filter(is_active=True).count()


class InstitutionDetailSerializer(serializers.ModelSerializer):
    """Serializer for institution detail view (public)."""
    logo_url = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    journals_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Institution
        fields = [
            'id',
            'institution_name',
            'institution_type',
            'logo_url',
            'description',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'phone',
            'website',
            'established_year',
            'research_areas',
            'total_researchers',
            'journals_count',
            'stats',
        ]
    
    def to_representation(self, instance):
        """Convert research_areas string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_areas'):
            data['research_areas'] = [
                area.strip() 
                for area in data['research_areas'].split(',') 
                if area.strip()
            ]
        else:
            data['research_areas'] = []
        return data
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_journals_count(self, obj):
        return obj.journals.filter(is_active=True).count()
    
    def get_stats(self, obj):
        """Get institution stats if available"""
        try:
            stats = obj.stats
            return InstitutionStatsSerializer(stats).data
        except InstitutionStats.DoesNotExist:
            return None


class AuthorListSerializer(serializers.ModelSerializer):
    """Serializer for listing authors publicly."""
    profile_picture_url = serializers.SerializerMethodField()
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id',
            'title',
            'full_name',
            'institute',
            'designation',
            'degree',
            'profile_picture_url',
            'bio',
            'research_interests',
            'orcid',
            'google_scholar',
            'publications_count',
        ]
    
    def to_representation(self, instance):
        """Convert research_interests string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_interests'):
            data['research_interests'] = [
                interest.strip() 
                for interest in data['research_interests'].split(',') 
                if interest.strip()
            ]
        else:
            data['research_interests'] = []
        return data
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_publications_count(self, obj):
        from publications.models import Publication
        return Publication.objects.filter(author=obj, is_published=True).count()


class AuthorDetailSerializer(serializers.ModelSerializer):
    """Serializer for author detail view (public)."""
    profile_picture_url = serializers.SerializerMethodField()
    cv_url = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    publications_count = serializers.SerializerMethodField()
    coauthors = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id',
            'title',
            'full_name',
            'institute',
            'designation',
            'degree',
            'gender',
            'profile_picture_url',
            'cv_url',
            'bio',
            'research_interests',
            'orcid',
            'google_scholar',
            'researchgate',
            'linkedin',
            'website',
            'publications_count',
            'stats',
            'coauthors',
        ]
    
    def to_representation(self, instance):
        """Convert research_interests string to array for frontend"""
        data = super().to_representation(instance)
        if data.get('research_interests'):
            data['research_interests'] = [
                interest.strip() 
                for interest in data['research_interests'].split(',') 
                if interest.strip()
            ]
        else:
            data['research_interests'] = []
        return data
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_cv_url(self, obj):
        if obj.cv:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv.url)
            return obj.cv.url
        return None
    
    def get_publications_count(self, obj):
        from publications.models import Publication
        return Publication.objects.filter(author=obj, is_published=True).count()
    
    def get_stats(self, obj):
        """Get author stats if available"""
        try:
            stats = obj.stats
            return AuthorStatsSerializer(stats).data
        except AuthorStats.DoesNotExist:
            return None
    
    def get_coauthors(self, obj):
        """Get list of co-authors"""
        return obj.get_coauthors()[:10]  # Limit to top 10 co-authors


# Account Settings Serializers

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class UpdateEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_new_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value


class AccountStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(read_only=True)
    email = serializers.EmailField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DeactivateAccountSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)
    confirm_deactivation = serializers.BooleanField(required=True)
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
    
    def validate_confirm_deactivation(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm account deactivation.")
        return value


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True)
    confirm_deletion = serializers.CharField(required=True, write_only=True)
    
    def validate_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value
    
    def validate_confirm_deletion(self, value):
        if value != "DELETE MY ACCOUNT":
            raise serializers.ValidationError('You must type "DELETE MY ACCOUNT" to confirm deletion.')
        return value


# ==================== FOLLOW SERIALIZERS ====================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for follow lists."""
    name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    user_profile_type = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'user_type', 'name', 'profile_picture', 'user_profile_type']
    
    def get_name(self, obj):
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            return obj.author_profile.full_name
        elif obj.user_type == 'institution' and hasattr(obj, 'institution_profile'):
            return obj.institution_profile.institution_name
        return obj.email
    
    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            if obj.author_profile.profile_picture:
                if request:
                    return request.build_absolute_uri(obj.author_profile.profile_picture.url)
                return obj.author_profile.profile_picture.url
        elif obj.user_type == 'institution' and hasattr(obj, 'institution_profile'):
            if obj.institution_profile.logo:
                if request:
                    return request.build_absolute_uri(obj.institution_profile.logo.url)
                return obj.institution_profile.logo.url
        return None
    
    def get_user_profile_type(self, obj):
        """Get additional profile info based on user type."""
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            return {
                'institute': obj.author_profile.institute,
                'designation': obj.author_profile.designation,
            }
        elif obj.user_type == 'institution' and hasattr(obj, 'institution_profile'):
            return {
                'institution_type': obj.institution_profile.institution_type,
                'city': obj.institution_profile.city,
                'country': obj.institution_profile.country,
            }
        return None


class FollowSerializer(serializers.ModelSerializer):
    """Detailed follow relationship with user information."""
    follower_details = UserBasicSerializer(source='follower', read_only=True)
    following_details = UserBasicSerializer(source='following', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'follower_details', 'following_details', 'created_at']
        read_only_fields = ['id', 'follower', 'created_at']


class FollowCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a follow relationship."""
    
    class Meta:
        model = Follow
        fields = ['following']
    
    def validate(self, attrs):
        follower = self.context['request'].user
        following = attrs.get('following')
        
        # Prevent self-follow
        if follower == following:
            raise serializers.ValidationError({"following": "You cannot follow yourself."})
        
        # Check if already following
        if Follow.objects.filter(follower=follower, following=following).exists():
            raise serializers.ValidationError({"following": "You are already following this user."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data['follower'] = self.context['request'].user
        return super().create(validated_data)


class FollowerListSerializer(serializers.ModelSerializer):
    """List of followers with user details."""
    user = UserBasicSerializer(source='follower', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'user', 'created_at']


class FollowingListSerializer(serializers.ModelSerializer):
    """List of users being followed with user details."""
    user = UserBasicSerializer(source='following', read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'user', 'created_at']


class FollowStatsSerializer(serializers.Serializer):
    """Statistics about follows."""
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    is_following = serializers.BooleanField(required=False)


# ==================== ADMIN USER MANAGEMENT SERIALIZERS ====================

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for listing all users (admin only)."""
    profile_name = serializers.SerializerMethodField()
    profile_info = serializers.SerializerMethodField()
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'user_type', 'is_active', 'is_staff',
            'created_at', 'updated_at', 'profile_name', 'profile_info',
            'publications_count'
        ]
        read_only_fields = fields
    
    def get_profile_name(self, obj):
        """Get the profile name based on user type."""
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            return obj.author_profile.full_name
        elif obj.user_type == 'institution' and hasattr(obj, 'institution_profile'):
            return obj.institution_profile.institution_name
        elif obj.user_type == 'admin':
            return 'Administrator'
        return obj.email
    
    def get_profile_info(self, obj):
        """Get additional profile information."""
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            return {
                'institute': obj.author_profile.institute,
                'designation': obj.author_profile.designation,
                'orcid': obj.author_profile.orcid,
            }
        elif obj.user_type == 'institution' and hasattr(obj, 'institution_profile'):
            return {
                'institution_type': obj.institution_profile.institution_type,
                'city': obj.institution_profile.city,
                'country': obj.institution_profile.country,
            }
        return None
    
    def get_publications_count(self, obj):
        """Get publication count for authors."""
        if obj.user_type == 'author' and hasattr(obj, 'author_profile'):
            from publications.models import Publication
            return Publication.objects.filter(author=obj.author_profile).count()
        return 0


class AdminAuthorDetailSerializer(serializers.ModelSerializer):
    """Detailed author serializer for admin editing."""
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    created_at = serializers.DateTimeField(source='user.created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='user.updated_at', read_only=True)
    stats = AuthorStatsSerializer(read_only=True)
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Author
        fields = [
            'id', 'user_id', 'email', 'is_active',
            'title', 'full_name', 'institute', 'designation',
            'degree', 'gender', 'profile_picture', 'cv',
            'bio', 'research_interests', 'orcid',
            'google_scholar', 'researchgate', 'linkedin', 'website',
            'created_at', 'updated_at', 'stats', 'publications_count'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']
    
    def get_publications_count(self, obj):
        from publications.models import Publication
        return Publication.objects.filter(author=obj).count()
    
    def update(self, instance, validated_data):
        # Handle user fields separately
        user_data = validated_data.pop('user', {})
        
        # Update user fields if provided
        if 'email' in user_data:
            instance.user.email = user_data['email']
        if 'is_active' in user_data:
            instance.user.is_active = user_data['is_active']
        instance.user.save()
        
        # Update author profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class AdminInstitutionDetailSerializer(serializers.ModelSerializer):
    """Detailed institution serializer for admin editing."""
    email = serializers.EmailField(source='user.email')
    is_active = serializers.BooleanField(source='user.is_active')
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    created_at = serializers.DateTimeField(source='user.created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='user.updated_at', read_only=True)
    stats = InstitutionStatsSerializer(read_only=True)
    
    class Meta:
        model = Institution
        fields = [
            'id', 'user_id', 'email', 'is_active',
            'institution_name', 'institution_type', 'logo', 'description',
            'address', 'city', 'state', 'country', 'postal_code', 'phone',
            'website', 'established_year', 'research_areas', 'total_researchers',
            'created_at', 'updated_at', 'stats'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Handle user fields separately
        user_data = validated_data.pop('user', {})
        
        # Update user fields if provided
        if 'email' in user_data:
            instance.user.email = user_data['email']
        if 'is_active' in user_data:
            instance.user.is_active = user_data['is_active']
        instance.user.save()
        
        # Update institution profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
