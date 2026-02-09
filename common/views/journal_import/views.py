"""
API endpoint to import journal from Crossref metadata
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from publications.models import Journal
from users.models import Institution
from common.services.crossref import CrossrefService
from urllib.parse import unquote
from django.db import models


class ImportJournalFromCrossrefView(APIView):
    """
    Import/create a journal from Crossref metadata.
    If the journal already exists (by ISSN or title), returns the existing journal.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Crossref'],
        summary='Import Journal from Crossref',
        description='Create or retrieve a journal using Crossref metadata. Matches by ISSN or title.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'journal_name': {'type': 'string', 'description': 'Journal name from Crossref'},
                    'issn': {'type': 'array', 'items': {'type': 'string'}, 'description': 'ISSN array'},
                    'publisher': {'type': 'string', 'description': 'Publisher name'},
                },
                'required': ['journal_name']
            }
        },
        responses={
            200: OpenApiResponse(description='Journal imported or found successfully'),
            400: OpenApiResponse(description='Invalid request'),
        }
    )
    def post(self, request):
        journal_name = request.data.get('journal_name', '').strip()
        issn_list = request.data.get('issn', [])
        publisher = request.data.get('publisher', '').strip()
        
        if not journal_name:
            return Response({
                'status': 'error',
                'message': 'Journal name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to find existing journal by ISSN first
        existing_journal = None
        if issn_list:
            for issn_value in issn_list:
                existing_journal = Journal.objects.filter(
                    models.Q(issn=issn_value) | models.Q(e_issn=issn_value)
                ).first()
                if existing_journal:
                    break
        
        # If not found by ISSN, try by exact title match
        if not existing_journal:
            existing_journal = Journal.objects.filter(
                title__iexact=journal_name
            ).first()
        
        # If journal exists, return it
        if existing_journal:
            return Response({
                'status': 'success',
                'message': 'Journal already exists',
                'journal': {
                    'id': existing_journal.id,
                    'title': existing_journal.title,
                    'issn': existing_journal.issn,
                    'e_issn': existing_journal.e_issn,
                    'publisher_name': existing_journal.publisher_name,
                }
            })
        
        # Create new journal
        # Use a dedicated institution for auto-imported journals
        # Find or create "External Imports" institution
        institution, created = Institution.objects.get_or_create(
            institution_name='External Imports',
            defaults={
                'institution_type': 'university',
                'email': 'noreply@researchindex.com',
                'phone': '',
                'address': 'Auto-generated institution for externally imported journals',
                'city': '',
                'state': '',
                'country': 'Nepal',
                'postal_code': '',
            }
        )
        
        if created:
            print(f"Created new 'External Imports' institution with ID: {institution.id}")
        
        # Create the journal with proper field truncation
        # Truncate title to fit max_length=300
        truncated_title = journal_name[:300] if len(journal_name) > 300 else journal_name
        
        # Create short title (max 100 chars) from the full title
        short_title = journal_name[:100] if len(journal_name) > 100 else journal_name
        if len(journal_name) > 100:
            # Find last space before 97 chars to avoid cutting words
            last_space = journal_name[:97].rfind(' ')
            if last_space > 0:
                short_title = journal_name[:last_space] + '...'
        
        journal_data = {
            'institution': institution,
            'title': truncated_title,
            'short_title': short_title,
            'publisher_name': (publisher or '')[:200],  # max_length=200
            'description': f'Auto-imported from Crossref',
            'is_active': True,
            'peer_reviewed': True,
        }
        
        # Set ISSN values if available
        if issn_list:
            # First ISSN goes to issn field (max_length=20)
            journal_data['issn'] = issn_list[0][:20] if issn_list else ''
            # Second ISSN (if exists) goes to e_issn (max_length=20)
            if len(issn_list) > 1:
                journal_data['e_issn'] = issn_list[1][:20]
        
        try:
            new_journal = Journal.objects.create(**journal_data)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to create journal: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': 'success',
            'message': 'Journal created successfully',
            'journal': {
                'id': new_journal.id,
                'title': new_journal.title,
                'issn': new_journal.issn,
                'e_issn': new_journal.e_issn,
                'publisher_name': new_journal.publisher_name,
            }
        }, status=status.HTTP_201_CREATED)
