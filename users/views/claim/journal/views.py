"""
Views for journal claiming functionality.
Allows creating institution accounts OR claiming additional journals for existing institutions.

IMPORTANT: Institutions are created through journal claiming, not through separate
account claiming. This is because institutions are not imported - only journals are imported.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.db import transaction

from publications.models import Journal
from ....models import Institution
from ....serializers.claim.journal.serializers import (
    SearchClaimableJournalsSerializer,
    ClaimableJournalSerializer,
    ClaimJournalSerializer,
    ClaimJournalsWithInstitutionSerializer,
)
from ...views import set_auth_cookies


class SearchClaimableJournalsView(APIView):
    """
    Search for journals that can be claimed by institutions.
    These are journals owned by inactive system institutions (import placeholders).
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Journal Claiming'],
        summary='Search Claimable Journals',
        description='Search for imported journals that can be claimed by institutions. These journals are currently owned by system placeholders and waiting for the actual publishers to claim them.',
        parameters=[
            OpenApiParameter(
                name='search_query',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search by journal title, ISSN, or publisher name',
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Search results',
                response={
                    'type': 'object',
                    'properties': {
                        'results': {'type': 'array'},
                        'count': {'type': 'integer'},
                    }
                }
            ),
            400: OpenApiResponse(description='Invalid search parameters'),
        }
    )
    def get(self, request):
        serializer = SearchClaimableJournalsSerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        search_query = serializer.validated_data['search_query']
        
        # Search for journals owned by inactive system institutions
        journals = Journal.objects.filter(
            institution__user__is_active=False,
            institution__user__email__icontains='system.institution'
        ).filter(
            Q(title__icontains=search_query) |
            Q(issn__icontains=search_query) |
            Q(e_issn__icontains=search_query) |
            Q(publisher_name__icontains=search_query)
        ).select_related('institution', 'institution__user')[:20]
        
        results = ClaimableJournalSerializer(journals, many=True).data
        
        return Response({
            'results': results,
            'count': len(results),
            'search_query': search_query
        }, status=status.HTTP_200_OK)


class ClaimJournalsWithInstitutionView(APIView):
    """
    Claim journals by creating a new institution account.
    This is the PRIMARY way to create institution accounts - by claiming imported journals.
    Multiple journals can be claimed at once.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Journal Claiming'],
        summary='Create Institution + Claim Journals',
        description='Create a new institution account and claim ownership of one or more imported journals in a single operation. This is how institutions are created in the system - by claiming their imported journals.',
        request=ClaimJournalsWithInstitutionSerializer,
        examples=[
            OpenApiExample(
                'Create Institution and Claim Journals',
                value={
                    'email': 'admin@university.edu',
                    'password': 'SecurePass123!',
                    'confirm_password': 'SecurePass123!',
                    'institution_name': 'University of Research',
                    'institution_type': 'University',
                    'country': 'Nepal',
                    'city': 'Kathmandu',
                    'description': 'Leading research university',
                    'website': 'https://university.edu.np',
                    'journal_ids': [6, 7, 12]
                },
                request_only=True,
            )
        ],
        responses={
            201: OpenApiResponse(
                description='Institution created and journals claimed successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'institution': {'type': 'object'},
                        'journals_claimed': {'type': 'integer'},
                        'journal_titles': {'type': 'array'},
                    }
                }
            ),
            400: OpenApiResponse(description='Validation error or journals cannot be claimed'),
        }
    )
    def post(self, request):
        serializer = ClaimJournalsWithInstitutionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create institution and claim journals
        result = serializer.save()
        user = result['user']
        institution = result['institution']
        
        # Generate JWT tokens for auto-login
        tokens = user.tokens()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        response = Response({
            'message': f'Institution created and {result["journals_claimed"]} journal(s) claimed successfully',
            'institution': {
                'id': institution.id,
                'name': institution.institution_name,
                'email': user.email,
            },
            'journals_claimed': result['journals_claimed'],
            'journal_titles': result['journal_titles'],
            'tokens': {
                'access': access_token,
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'institution_name': institution.institution_name,
            }
        }, status=status.HTTP_201_CREATED)
        
        # Set HTTP-only cookies for auto-login
        set_auth_cookies(response, access_token, refresh_token)
        
        return response


class ClaimJournalView(APIView):
    """
    Claim ownership of an imported journal.
    Only active institutions can claim journals.
    The journal ownership will be transferred from the system institution to the claiming institution.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journal Claiming'],
        summary='Claim Journal Ownership',
        description='Claim ownership of an imported journal. This transfers the journal from the system placeholder institution to your institution. Only active institutions can claim journals.',
        request=ClaimJournalSerializer,
        responses={
            200: OpenApiResponse(
                description='Journal successfully claimed',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'journal': {'type': 'object'},
                    }
                }
            ),
            400: OpenApiResponse(description='Invalid request or journal cannot be claimed'),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Only institutions can claim journals'),
            404: OpenApiResponse(description='Journal not found'),
        }
    )
    def post(self, request):
        # Verify user is an institution
        if request.user.user_type != 'institution':
            return Response(
                {'error': 'Only institutions can claim journals'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the institution profile
        try:
            institution = Institution.objects.get(user=request.user)
        except Institution.DoesNotExist:
            return Response(
                {'error': 'Institution profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate the request
        serializer = ClaimJournalSerializer(
            data=request.data,
            context={'institution': institution}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        journal_id = serializer.validated_data['journal_id']
        
        # Transfer journal ownership
        try:
            with transaction.atomic():
                journal = Journal.objects.select_for_update().get(id=journal_id)
                old_owner = journal.institution
                journal.institution = institution
                journal.save()
                
                return Response({
                    'message': f'Successfully claimed journal "{journal.title}"',
                    'journal': {
                        'id': journal.id,
                        'title': journal.title,
                        'issn': journal.issn,
                        'new_owner': institution.institution_name,
                        'previous_owner': old_owner.institution_name,
                    }
                }, status=status.HTTP_200_OK)
        
        except Journal.DoesNotExist:
            return Response(
                {'error': 'Journal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to claim journal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListMyJournalsView(APIView):
    """
    List all journals owned by the authenticated institution.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Journal Claiming'],
        summary='List My Journals',
        description='Get a list of all journals owned by the authenticated institution.',
        responses={
            200: OpenApiResponse(
                description='List of owned journals',
                response={
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer'},
                        'journals': {'type': 'array'},
                    }
                }
            ),
            401: OpenApiResponse(description='Authentication required'),
            403: OpenApiResponse(description='Only institutions can view this'),
        }
    )
    def get(self, request):
        # Verify user is an institution
        if request.user.user_type != 'institution':
            return Response(
                {'error': 'Only institutions can view journals'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the institution profile
        try:
            institution = Institution.objects.get(user=request.user)
        except Institution.DoesNotExist:
            return Response(
                {'error': 'Institution profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all journals owned by this institution
        journals = Journal.objects.filter(institution=institution)
        results = ClaimableJournalSerializer(journals, many=True).data
        
        return Response({
            'count': journals.count(),
            'journals': results
        }, status=status.HTTP_200_OK)


class ClaimJournalsWithLoginView(APIView):
    """
    Claim journals by logging in with existing institution credentials.
    This allows existing institutions to claim additional journals without needing
    to log out and use the separate "claim additional journal" endpoint.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Journal Claiming'],
        summary='Login & Claim Journals',
        description='Claim journals by logging in with existing institution credentials. This is a convenient way for existing institutions to claim multiple journals at once without needing to be already logged in.',
        request={
            'type': 'object',
            'required': ['email', 'password', 'journal_ids'],
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'format': 'password'},
                'journal_ids': {
                    'type': 'array',
                    'items': {'type': 'integer'}
                }
            }
        },
        examples=[
            OpenApiExample(
                'Login and Claim Journals',
                value={
                    'email': 'admin@university.edu',
                    'password': 'SecurePass123!',
                    'journal_ids': [6, 7, 12]
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Journals claimed successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'institution': {'type': 'object'},
                        'journals_claimed': {'type': 'integer'},
                        'journal_titles': {'type': 'array'},
                    }
                }
            ),
            400: OpenApiResponse(description='Invalid credentials or journals cannot be claimed'),
            403: OpenApiResponse(description='Only institutions can claim journals'),
        }
    )
    def post(self, request):
        from ....serializers.claim.journal.serializers import ClaimJournalsWithLoginSerializer
        
        serializer = ClaimJournalsWithLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Claim journals
        result = serializer.save()
        user = result['user']
        institution = result['institution']
        
        # Generate JWT tokens for auto-login
        tokens = user.tokens()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        response = Response({
            'message': f'Successfully claimed {result["journals_claimed"]} journal(s)',
            'institution': {
                'id': institution.id,
                'name': institution.institution_name,
                'email': user.email,
            },
            'journals_claimed': result['journals_claimed'],
            'journal_titles': result['journal_titles'],
            'tokens': {
                'access': access_token,
            },
            'user': {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'institution_name': institution.institution_name,
            }
        }, status=status.HTTP_200_OK)
        
        # Set HTTP-only cookies for auto-login
        set_auth_cookies(response, access_token, refresh_token)
        
        return response
