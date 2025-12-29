from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, Author, Institution


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


class AuthorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    cv_url = serializers.SerializerMethodField()
    
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
        ]
        read_only_fields = ['id', 'email', 'user_type']
    
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


class InstitutionProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    logo_url = serializers.SerializerMethodField()
    
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
        ]
        read_only_fields = ['id', 'email', 'user_type']
    
    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


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
