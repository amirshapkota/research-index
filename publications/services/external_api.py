"""
Service for fetching data from external journal management API.
"""
import requests
import logging
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ExternalJournalAPI:
    """
    Client for interacting with external journal management system API.
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'EXTERNAL_JOURNAL_API_URL', 'http://localhost:8001')
        self.timeout = 30
    
    def fetch_publications(self, page: int = 1) -> Dict:
        """
        Fetch publications from external API.
        
        Args:
            page: Page number for pagination
            
        Returns:
            Dictionary containing count, next, previous, and results
        """
        try:
            url = f"{self.base_url}/api/v1/publications/"
            params = {'page': page}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Fetched {len(data.get('results', []))} publications from page {page}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching publications from external API: {e}")
            raise
    
    def fetch_all_publications(self) -> List[Dict]:
        """
        Fetch all publications from external API (handles pagination).
        
        Returns:
            List of all publication dictionaries
        """
        all_publications = []
        page = 1
        
        while True:
            try:
                data = self.fetch_publications(page=page)
                results = data.get('results', [])
                
                if not results:
                    break
                
                all_publications.extend(results)
                
                # Check if there's a next page
                if not data.get('next'):
                    break
                
                page += 1
                logger.info(f"Fetched {len(all_publications)} publications so far...")
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Total publications fetched: {len(all_publications)}")
        return all_publications
    
    def download_document(self, document_id: str) -> Optional[bytes]:
        """
        Download document file from external API.
        
        Args:
            document_id: UUID of the document to download
            
        Returns:
            Binary content of the document, or None if error
        """
        try:
            url = f"{self.base_url}/api/v1/publications/documents/{document_id}/download/"
            
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            logger.info(f"Downloaded document {document_id}")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading document {document_id}: {e}")
            return None
