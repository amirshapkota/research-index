from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
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
    API endpoint for author registration
    """
    queryset = CustomUser.objects.all()
    serializer_class = AuthorRegistrationSerializer
    permission_classes = [AllowAny]
    
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
    API endpoint for institution registration
    """
    queryset = CustomUser.objects.all()
    serializer_class = InstitutionRegistrationSerializer
    permission_classes = [AllowAny]
    
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
    API endpoint for login (both authors and institutions)
    """
    permission_classes = [AllowAny]
    
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
    API endpoint to get author profile details
    """
    permission_classes = [IsAuthenticated]
    
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
    API endpoint to get institution profile details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            institution = Institution.objects.get(user=request.user)
            serializer = InstitutionProfileSerializer(institution)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Institution.DoesNotExist:
            return Response({
                'error': 'Institution profile not found'
            }, status=status.HTTP_404_NOT_FOUND)