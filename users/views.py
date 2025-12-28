from rest_framework import generics, status
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
    InstitutionProfileSerializer
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
                    profile_data = AuthorProfileSerializer(author).data
                except Author.DoesNotExist:
                    pass
            elif user.user_type == 'institution':
                try:
                    institution = Institution.objects.get(user=user)
                    profile_data = InstitutionProfileSerializer(institution).data
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
    Get the authenticated author's profile information.
    
    Requires valid JWT token in Authorization header.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Profile'],
        summary='Get Author Profile',
        description='Retrieve the profile information for the authenticated author.',
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
            serializer = AuthorProfileSerializer(author)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Author.DoesNotExist:
            return Response({
                'error': 'Author profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class InstitutionProfileView(APIView):
    """
    Get the authenticated institution's profile information.
    
    Requires valid JWT token in Authorization header.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Profile'],
        summary='Get Institution Profile',
        description='Retrieve the profile information for the authenticated institution.',
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
            serializer = InstitutionProfileSerializer(institution)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)