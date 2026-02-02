"""
Views for synchronizing data from external journal management system.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .services import ExternalJournalAPI, ExternalDataMapper
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def sync_external_publications(request):
    """
    Trigger synchronization of publications from external journal management API.
    
    Only accessible to admin users.
    
    Request body (optional):
        {
            "limit": 10,  # Limit number of publications to sync (for testing)
            "api_url": "http://custom-api.com"  # Override external API URL
        }
    
    Response:
        {
            "success": true,
            "message": "Sync completed successfully",
            "total_processed": 50,
            "success_count": 48,
            "error_count": 2
        }
    """
    try:
        # Get parameters from request body
        limit = request.data.get('limit')
        api_url = request.data.get('api_url')
        
        # Initialize API client and mapper
        api = ExternalJournalAPI(base_url=api_url) if api_url else ExternalJournalAPI()
        mapper = ExternalDataMapper()
        
        # Fetch publications
        logger.info(f"Starting publication sync (limit: {limit or 'all'})")
        data = api.fetch_publications(page=1)
        publications = data.get('results', [])
        
        if limit:
            publications = publications[:limit]
        
        total = len(publications)
        success_count = 0
        error_count = 0
        errors = []
        
        # Process each publication
        for pub_data in publications:
            title = pub_data.get('title', 'Unknown')
            try:
                publication = mapper.map_and_create_publication(pub_data)
                if publication:
                    success_count += 1
                    logger.info(f"Synced publication: {publication.title}")
                else:
                    error_count += 1
                    errors.append({'title': title, 'error': 'Failed to create publication'})
                    
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                errors.append({'title': title, 'error': error_msg})
                logger.exception(f"Error processing publication '{title}'")
        
        # Return summary
        response_data = {
            'success': True,
            'message': f'Sync completed. Processed: {total}, Success: {success_count}, Errors: {error_count}',
            'total_processed': total,
            'success_count': success_count,
            'error_count': error_count,
        }
        
        if errors:
            response_data['errors'] = errors[:10]  # Return first 10 errors
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception("Error during sync process")
        return Response(
            {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
