"""
Views for imported author account claiming functionality.
Allows imported authors to search and claim their accounts.

Note: Institutions are NOT imported separately. Institutions are created through
journal claiming instead (see journal_claim_views.py).
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q

from ....models import Author
from ....serializers.claim.author.serializers import (
    SearchImportedAuthorsSerializer,
    ImportedAuthorSerializer,
    ClaimAuthorAccountSerializer,
)
from ...views import set_auth_cookies


class SearchImportedAuthorsView(APIView):
    """
    Search for imported author profiles that can be claimed.
    Only returns inactive (unclaimed) author profiles.
    Supports imports from NEPJOL, journal portals, Crossref, and other sources.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Account Claiming'],
        summary='Search Imported Authors',
        description='Search for imported author profiles by name, ORCID, or institution. Includes profiles imported from NEPJOL, journal portals, Crossref, and other external sources. Only inactive (unclaimed) profiles are returned.',
        parameters=[
            OpenApiParameter(
                name='search_query',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search term (name, ORCID, institution name, etc.)',
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
        serializer = SearchImportedAuthorsSerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        search_query = serializer.validated_data['search_query']
        
        # Search for inactive authors with import-related email patterns
        # Includes: @imported., @external., @test. (excludes system accounts)
        authors = Author.objects.filter(
            user__is_active=False
        ).filter(
            Q(user__email__icontains='@imported.') |
            Q(user__email__icontains='@external.') |
            Q(user__email__icontains='@test.')
        ).exclude(
            user__email__icontains='system.'  # Exclude system accounts
        ).filter(
            Q(full_name__icontains=search_query) |
            Q(orcid__icontains=search_query) |
            Q(institute__icontains=search_query)
        ).select_related('user')[:20]
        
        results = ImportedAuthorSerializer(authors, many=True).data
        
        return Response({
            'results': results,
            'count': len(results),
            'search_query': search_query
        }, status=status.HTTP_200_OK)


class ClaimAuthorAccountView(APIView):
    """
    Claim an imported author account.
    Updates credentials and activates the account.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['Account Claiming'],
        summary='Claim Author Account',
        description='Claim an imported author account by providing the author ID, new email, and password. The account will be activated and you\'ll receive authentication tokens.',
        request=ClaimAuthorAccountSerializer,
        examples=[
            OpenApiExample(
                'Claim Author Account',
                value={
                    'author_id': 123,
                    'new_email': 'john.doe@university.edu',
                    'password': 'NewSecurePass123!',
                    'confirm_password': 'NewSecurePass123!',
                    'bio': 'Professor of Computer Science',
                    'research_interests': 'AI, Machine Learning, NLP',
                    'google_scholar': 'https://scholar.google.com/...',
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Account claimed successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'user': {'type': 'object'},
                    }
                }
            ),
            400: OpenApiResponse(description='Validation error'),
            404: OpenApiResponse(description='Author not found or already claimed'),
        }
    )
    def post(self, request):
        serializer = ClaimAuthorAccountSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Claim the account
        user = serializer.save()
        
        # Generate JWT tokens
        tokens = user.tokens()
        access_token = tokens['access']
        refresh_token = tokens['refresh']
        
        response = Response({
            'message': 'Author account claimed successfully',
            'user': {
                'email': user.email,
                'user_type': user.user_type,
                'is_active': user.is_active
            }
        }, status=status.HTTP_200_OK)
        
        # Set HTTP-only cookies
        set_auth_cookies(response, access_token, refresh_token)
        
        return response


# ClaimInstitutionAccountView REMOVED
# Institutions are NOT imported - they are created via journal claiming instead.
# See users/views/journal_claim_views.py for institution creation through journal claiming.
