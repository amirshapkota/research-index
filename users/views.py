from rest_framework import generics, status, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .serializers import (
    AuthorRegistrationSerializer, 
    InstitutionRegistrationSerializer,
    LoginSerializer,
    AuthorProfileSerializer,
    InstitutionProfileSerializer,
    ChangePasswordSerializer,
    UpdateEmailSerializer,
    AccountStatusSerializer,
    DeactivateAccountSerializer,
    DeleteAccountSerializer
)
from .models import CustomUser, Author, Institution


class AuthorRegistrationView(generics.CreateAPIView):
    """
    Register a new author account with detailed profile information.
    
    Creates both a user account and an associated author profile.
    Returns JWT tokens for immediate authentication.
    """
    queryset = CustomUser.objects.all()
    serializer_class = AuthorRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Registration'],
        summary='Register as Author',
        description='Create a new author account with profile information including title, full name, institute, and designation.',
        examples=[
            OpenApiExample(
                'Author Registration Example',
                value={
                    'email': 'john.doe@university.edu',
                    'password': 'SecurePass123!',
                    'confirm_password': 'SecurePass123!',
                    'title': 'Dr.',
                    'full_name': 'John Doe',
                    'institute': 'MIT',
                    'designation': 'Associate Professor'
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(
                description='Author registered successfully',
                response=AuthorRegistrationSerializer,
            ),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Author registered successfully',
            'user': {
                'email': user.email,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class InstitutionRegistrationView(generics.CreateAPIView):
    """
    Register a new institution account.
    
    Creates both a user account and an associated institution profile.
    Returns JWT tokens for immediate authentication.
    """
    queryset = CustomUser.objects.all()
    serializer_class = InstitutionRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Registration'],
        summary='Register as Institution',
        description='Create a new institution account with basic organization information.',
        examples=[
            OpenApiExample(
                'Institution Registration Example',
                value={
                    'email': 'admin@university.edu',
                    'password': 'SecurePass123!',
                    'confirm_password': 'SecurePass123!',
                    'institution_name': 'Harvard University'
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(
                description='Institution registered successfully',
                response=InstitutionRegistrationSerializer,
            ),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Institution registered successfully',
            'user': {
                'email': user.email,
                'user_type': user.user_type
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Unified login endpoint for both authors and institutions.
    
    Authenticate with email and password, returns JWT tokens and user profile.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Authentication'],
        summary='Login',
        description='Login for both authors and institutions using email and password. Returns JWT tokens and user profile data.',
        request=LoginSerializer,
        examples=[
            OpenApiExample(
                'Login Example',
                value={
                    'email': 'user@example.com',
                    'password': 'SecurePass123!'
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Login successful',
            ),
            401: OpenApiResponse(description='Invalid credentials'),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get profile data based on user type
            profile_data = {}
            if user.user_type == 'author':
                try:
                    author = Author.objects.get(user=user)
                    profile_data = AuthorProfileSerializer(author, context={'request': request}).data
                except Author.DoesNotExist:
                    pass
            elif user.user_type == 'institution':
                try:
                    institution = Institution.objects.get(user=user)
                    profile_data = InstitutionProfileSerializer(institution, context={'request': request}).data
                except Institution.DoesNotExist:
                    pass
            
            return Response({
                'message': 'Login successful',
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'user': profile_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)


class AuthorProfileView(APIView):
    """
    Get and update the authenticated author's profile information.
    
    Supports GET, PUT, and PATCH methods.
    Handles file uploads for profile picture and CV.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    @extend_schema(
        tags=['Profile'],
        summary='Get Author Profile',
        description='Retrieve the complete profile information for the authenticated author.',
        responses={
            200: OpenApiResponse(
                description='Author profile retrieved successfully',
                response=AuthorProfileSerializer,
            ),
            404: OpenApiResponse(description='Author profile not found'),
        }
    )
    def get(self, request):
        try:
            author = Author.objects.get(user=request.user)
            serializer = AuthorProfileSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({
                'error': 'Author profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Profile'],
        summary='Update Author Profile (Full)',
        description='Update the complete author profile. Supports file uploads for profile_picture and cv.',
        request=AuthorProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='Author profile updated successfully',
                response=AuthorProfileSerializer,
            ),
            404: OpenApiResponse(description='Author profile not found'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def put(self, request):
        try:
            author = Author.objects.get(user=request.user)
            serializer = AuthorProfileSerializer(author, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({
                'error': 'Author profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Profile'],
        summary='Update Author Profile (Partial)',
        description='Partially update author profile. Only provided fields will be updated. Supports file uploads.',
        request=AuthorProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='Author profile updated successfully',
                response=AuthorProfileSerializer,
            ),
            404: OpenApiResponse(description='Author profile not found'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def patch(self, request):
        try:
            author = Author.objects.get(user=request.user)
            serializer = AuthorProfileSerializer(author, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({
                'error': 'Author profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class InstitutionProfileView(APIView):
    """
    Get and update the authenticated institution's profile information.
    
    Supports GET, PUT, and PATCH methods.
    Handles file upload for logo.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    @extend_schema(
        tags=['Profile'],
        summary='Get Institution Profile',
        description='Retrieve the complete profile information for the authenticated institution.',
        responses={
            200: OpenApiResponse(
                description='Institution profile retrieved successfully',
                response=InstitutionProfileSerializer,
            ),
            404: OpenApiResponse(description='Institution profile not found'),
        }
    )
    def get(self, request):
        try:
            institution = Institution.objects.get(user=request.user)
            serializer = InstitutionProfileSerializer(institution, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Profile'],
        summary='Update Institution Profile (Full)',
        description='Update the complete institution profile. Supports file upload for logo.',
        request=InstitutionProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='Institution profile updated successfully',
                response=InstitutionProfileSerializer,
            ),
            404: OpenApiResponse(description='Institution profile not found'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def put(self, request):
        try:
            institution = Institution.objects.get(user=request.user)
            serializer = InstitutionProfileSerializer(institution, data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        tags=['Profile'],
        summary='Update Institution Profile (Partial)',
        description='Partially update institution profile. Only provided fields will be updated. Supports file upload.',
        request=InstitutionProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='Institution profile updated successfully',
                response=InstitutionProfileSerializer,
            ),
            404: OpenApiResponse(description='Institution profile not found'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def patch(self, request):
        try:
            institution = Institution.objects.get(user=request.user)
            serializer = InstitutionProfileSerializer(institution, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'profile': serializer.data
            }, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


# Account Settings Views

class ChangePasswordView(APIView):
    """
    Change password for authenticated users (both authors and institutions).
    
    Requires old password for verification and new password with confirmation.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Change Password',
        description='Change account password. Requires old password verification.',
        request=ChangePasswordSerializer,
        examples=[
            OpenApiExample(
                'Change Password Example',
                value={
                    'old_password': 'OldPass123!',
                    'new_password': 'NewSecurePass456!',
                    'confirm_new_password': 'NewSecurePass456!'
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description='Password changed successfully'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({
            'message': 'Password changed successfully. Please login again with your new password.'
        }, status=status.HTTP_200_OK)


class UpdateEmailView(APIView):
    """
    Update email address for authenticated users.
    
    Requires password verification and new email must be unique.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Update Email',
        description='Update account email address. Requires password verification.',
        request=UpdateEmailSerializer,
        examples=[
            OpenApiExample(
                'Update Email Example',
                value={
                    'new_email': 'newemail@example.com',
                    'password': 'CurrentPass123!'
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description='Email updated successfully'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request):
        serializer = UpdateEmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Update email
        old_email = request.user.email
        request.user.email = serializer.validated_data['new_email']
        request.user.save()
        
        return Response({
            'message': 'Email updated successfully',
            'old_email': old_email,
            'new_email': request.user.email
        }, status=status.HTTP_200_OK)


class AccountStatusView(APIView):
    """
    Get current account status and information.
    
    Returns account details including creation date, status, and user type.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Get Account Status',
        description='Retrieve current account status and information.',
        responses={
            200: OpenApiResponse(
                description='Account status retrieved successfully',
                response=AccountStatusSerializer,
            ),
        }
    )
    def get(self, request):
        data = {
            'is_active': request.user.is_active,
            'email': request.user.email,
            'user_type': request.user.user_type,
            'created_at': request.user.created_at,
            'updated_at': request.user.updated_at,
        }
        
        serializer = AccountStatusSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeactivateAccountView(APIView):
    """
    Deactivate account (can be reactivated by admin).
    
    Requires password verification and confirmation.
    Sets is_active to False, user can't login but data is preserved.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Deactivate Account',
        description='Deactivate your account. Account can be reactivated by contacting support.',
        request=DeactivateAccountSerializer,
        examples=[
            OpenApiExample(
                'Deactivate Account Example',
                value={
                    'password': 'CurrentPass123!',
                    'confirm_deactivation': True
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description='Account deactivated successfully'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request):
        serializer = DeactivateAccountSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Deactivate account
        request.user.is_active = False
        request.user.save()
        
        return Response({
            'message': 'Account deactivated successfully. Contact support to reactivate your account.'
        }, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
    """
    Permanently delete account and all associated data.
    
    WARNING: This action cannot be undone!
    Requires password and explicit confirmation text.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Account Settings'],
        summary='Delete Account Permanently',
        description='Permanently delete your account and all associated data. This action cannot be undone!',
        request=DeleteAccountSerializer,
        examples=[
            OpenApiExample(
                'Delete Account Example',
                value={
                    'password': 'CurrentPass123!',
                    'confirm_deletion': 'DELETE MY ACCOUNT'
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description='Account deleted successfully'),
            400: OpenApiResponse(description='Validation error'),
        }
    )
    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Store email for response
        email = request.user.email
        
        # Delete user (will cascade delete profile due to OneToOne relationship)
        request.user.delete()
        
        return Response({
            'message': f'Account {email} has been permanently deleted. All your data has been removed.'
        }, status=status.HTTP_200_OK)
