from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import CustomUser, Author, Institution
from ..serializers import (
    AdminUserListSerializer,
    AdminAuthorDetailSerializer,
    AdminInstitutionDetailSerializer
)


class IsAdminUser:
    """
    Custom permission to only allow admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.user_type == 'admin' or request.user.is_staff
        )


class AdminUserListView(generics.ListAPIView):
    """
    List all users in the system (admin only).
    
    Supports filtering by user_type and search by email/name.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminUserListSerializer
    
    def get_queryset(self):
        queryset = CustomUser.objects.select_related(
            'author_profile', 'institution_profile'
        ).all()
        
        # Filter by user type if provided
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Search by email, author name, or institution name
        search = self.request.query_params.get('search', None)
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(author_profile__full_name__icontains=search) |
                Q(institution_profile__institution_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='List All Users',
        description='Retrieve all users in the system with optional filtering (admin only).',
        responses={
            200: AdminUserListSerializer(many=True),
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def get(self, request, *args, **kwargs):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().get(request, *args, **kwargs)


class AdminAuthorDetailView(APIView):
    """
    Retrieve, update, or delete an author profile (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Get Author Details',
        description='Retrieve detailed author information (admin only).',
        responses={
            200: AdminAuthorDetailSerializer,
            403: OpenApiResponse(description='Admin permission required'),
            404: OpenApiResponse(description='Author not found')
        }
    )
    def get(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        author = get_object_or_404(
            Author.objects.select_related('user', 'stats'),
            pk=pk
        )
        serializer = AdminAuthorDetailSerializer(author)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Update Author',
        description='Update author profile information (admin only).',
        request=AdminAuthorDetailSerializer,
        responses={
            200: AdminAuthorDetailSerializer,
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def patch(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        author = get_object_or_404(
            Author.objects.select_related('user', 'stats'),
            pk=pk
        )
        serializer = AdminAuthorDetailSerializer(
            author,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Author updated successfully',
            'author': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Delete Author',
        description='Delete an author and their associated user account (admin only).',
        responses={
            200: OpenApiResponse(description='Author deleted successfully'),
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def delete(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        author = get_object_or_404(Author, pk=pk)
        full_name = author.full_name
        user = author.user
        
        # Deleting the user will cascade delete the author profile
        user.delete()
        
        return Response({
            'message': f'Author "{full_name}" has been deleted successfully'
        }, status=status.HTTP_200_OK)


class AdminInstitutionDetailView(APIView):
    """
    Retrieve, update, or delete an institution profile (admin only).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Get Institution Details',
        description='Retrieve detailed institution information (admin only).',
        responses={
            200: AdminInstitutionDetailSerializer,
            403: OpenApiResponse(description='Admin permission required'),
            404: OpenApiResponse(description='Institution not found')
        }
    )
    def get(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        institution = get_object_or_404(
            Institution.objects.select_related('user', 'stats'),
            pk=pk
        )
        serializer = AdminInstitutionDetailSerializer(institution)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Update Institution',
        description='Update institution profile information (admin only).',
        request=AdminInstitutionDetailSerializer,
        responses={
            200: AdminInstitutionDetailSerializer,
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def patch(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        institution = get_object_or_404(
            Institution.objects.select_related('user', 'stats'),
            pk=pk
        )
        serializer = AdminInstitutionDetailSerializer(
            institution,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Institution updated successfully',
            'institution': serializer.data
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Admin - User Management'],
        summary='Delete Institution',
        description='Delete an institution and their associated user account (admin only).',
        responses={
            200: OpenApiResponse(description='Institution deleted successfully'),
            403: OpenApiResponse(description='Admin permission required')
        }
    )
    def delete(self, request, pk):
        if not (request.user.user_type == 'admin' or request.user.is_staff):
            return Response(
                {'error': 'Admin permission required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        institution = get_object_or_404(Institution, pk=pk)
        institution_name = institution.institution_name
        user = institution.user
        
        # Deleting the user will cascade delete the institution profile
        user.delete()
        
        return Response({
            'message': f'Institution "{institution_name}" has been deleted successfully'
        }, status=status.HTTP_200_OK)
