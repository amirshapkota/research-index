"""
Crossref API Service
Handles all interactions with the Crossref REST API for fetching publication metadata,
citations, references, and journal information.
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CrossrefService:
    """
    Service class for interacting with Crossref REST API.
    
    Documentation: https://api.crossref.org/swagger-ui/index.html
    """
    
    BASE_URL = "https://api.crossref.org"
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours cache for most data
    
    # User agent for polite API usage (recommended by Crossref)
    USER_AGENT = "ResearchIndexNepal/1.0 (mailto:support@researchindex.np)"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make a request to the Crossref API with error handling and caching.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response data as dictionary or None if error
        """
        url = f"{self.BASE_URL}/{endpoint}"
        cache_key = f"crossref_{endpoint}_{str(params)}"
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {endpoint}")
            return cached_data
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            cache.set(cache_key, data, self.CACHE_TIMEOUT)
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Crossref API error for {endpoint}: {str(e)}")
            return None
    
    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Retrieve metadata for a specific DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Work metadata or None
        """
        # Clean DOI (remove https://doi.org/ prefix if present)
        doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
        
        endpoint = f"works/{requests.utils.quote(doi, safe='')}"
        response = self._make_request(endpoint)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def search_works(
        self,
        query: str,
        rows: int = 20,
        offset: int = 0,
        sort: Optional[str] = None,
        order: str = 'desc',
        filters: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Search for works using a query string.
        
        Args:
            query: Search query
            rows: Number of results to return (max 1000)
            offset: Starting position
            sort: Field to sort by (e.g., 'published', 'relevance')
            order: Sort order ('asc' or 'desc')
            filters: Dictionary of filters (e.g., {'type': 'journal-article'})
            
        Returns:
            Search results with items and metadata
        """
        params = {
            'query': query,
            'rows': min(rows, 1000),
            'offset': offset,
            'order': order,
        }
        
        if sort:
            params['sort'] = sort
        
        if filters:
            filter_strings = [f"{key}:{value}" for key, value in filters.items()]
            params['filter'] = ','.join(filter_strings)
        
        response = self._make_request('works', params=params)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def get_work_references(self, doi: str) -> List[Dict]:
        """
        Get references cited by a work.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            List of reference metadata
        """
        work = self.get_work_by_doi(doi)
        if work:
            return work.get('reference', [])
        return []
    
    def get_work_citations(self, doi: str, rows: int = 100) -> Optional[Dict]:
        """
        Get works that cite this DOI (using is-referenced-by-count).
        Note: Crossref doesn't directly provide citation lists, but we can get the count.
        
        Args:
            doi: Digital Object Identifier
            rows: Number of citing works to fetch
            
        Returns:
            Citation information
        """
        work = self.get_work_by_doi(doi)
        if work:
            citation_count = work.get('is-referenced-by-count', 0)
            return {
                'citation_count': citation_count,
                'doi': doi,
            }
        return None
    
    def get_journal_by_issn(self, issn: str) -> Optional[Dict]:
        """
        Retrieve journal metadata by ISSN.
        
        Args:
            issn: International Standard Serial Number
            
        Returns:
            Journal metadata or None
        """
        endpoint = f"journals/{issn}"
        response = self._make_request(endpoint)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def get_journal_works(
        self,
        issn: str,
        rows: int = 20,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get works published in a specific journal.
        
        Args:
            issn: International Standard Serial Number
            rows: Number of results to return
            offset: Starting position
            filters: Additional filters
            
        Returns:
            Works published in the journal
        """
        params = {
            'rows': min(rows, 1000),
            'offset': offset,
        }
        
        if filters:
            filter_strings = [f"{key}:{value}" for key, value in filters.items()]
            params['filter'] = ','.join(filter_strings)
        
        endpoint = f"journals/{issn}/works"
        response = self._make_request(endpoint, params=params)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def get_funder(self, funder_id: str) -> Optional[Dict]:
        """
        Get funder metadata by ID.
        
        Args:
            funder_id: Crossref funder ID
            
        Returns:
            Funder metadata or None
        """
        endpoint = f"funders/{funder_id}"
        response = self._make_request(endpoint)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def search_funders(self, query: str, rows: int = 20) -> Optional[Dict]:
        """
        Search for funders.
        
        Args:
            query: Search query
            rows: Number of results
            
        Returns:
            Funder search results
        """
        params = {
            'query': query,
            'rows': min(rows, 1000),
        }
        
        response = self._make_request('funders', params=params)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def get_member(self, member_id: str) -> Optional[Dict]:
        """
        Get member (publisher) metadata.
        
        Args:
            member_id: Crossref member ID
            
        Returns:
            Member metadata or None
        """
        endpoint = f"members/{member_id}"
        response = self._make_request(endpoint)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def get_work_agency(self, doi: str) -> Optional[Dict]:
        """
        Get registration agency for a DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Agency information
        """
        doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
        endpoint = f"works/{requests.utils.quote(doi, safe='')}/agency"
        response = self._make_request(endpoint)
        
        if response and response.get('status') == 'ok':
            return response.get('message')
        return None
    
    def extract_publication_data(self, work: Dict) -> Dict:
        """
        Extract and normalize publication data from Crossref work metadata.
        Useful for importing into your Publication model.
        
        Args:
            work: Crossref work metadata
            
        Returns:
            Normalized publication data
        """
        # Extract authors
        authors = []
        for author in work.get('author', []):
            author_name = f"{author.get('given', '')} {author.get('family', '')}".strip()
            if author_name:
                authors.append({
                    'name': author_name,
                    'given': author.get('given', ''),
                    'family': author.get('family', ''),
                    'orcid': author.get('ORCID', ''),
                    'affiliation': author.get('affiliation', []),
                })
        
        # Extract publication date
        published_date = None
        if 'published' in work:
            date_parts = work['published'].get('date-parts', [[]])[0]
            if len(date_parts) >= 3:
                published_date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
            elif len(date_parts) >= 2:
                published_date = f"{date_parts[0]}-{date_parts[1]:02d}-01"
            elif len(date_parts) >= 1:
                published_date = f"{date_parts[0]}-01-01"
        
        # Extract title
        title = ''
        if work.get('title'):
            title = work['title'][0] if isinstance(work['title'], list) else work['title']
        
        # Extract journal/container info
        journal_name = ''
        if work.get('container-title'):
            journal_name = work['container-title'][0] if isinstance(work['container-title'], list) else work['container-title']
        
        # Extract page/article number
        page = work.get('page', '')
        if not page and work.get('article-number'):
            page = work.get('article-number', '')
        
        # Extract abstract - Crossref may not always have it
        abstract = work.get('abstract', '')
        
        return {
            'doi': work.get('DOI', ''),
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'published_date': published_date,
            'journal': journal_name,
            'issn': work.get('ISSN', []),
            'volume': work.get('volume', ''),
            'issue': work.get('issue', ''),
            'page': page,
            'publisher': work.get('publisher', ''),
            'type': work.get('type', ''),
            'subtype': work.get('subtype', ''),
            'url': work.get('URL', ''),
            'citation_count': work.get('is-referenced-by-count', 0),
            'references': work.get('reference', []),
            'subjects': work.get('subject', []),
            'language': work.get('language', ''),
            'license': work.get('license', []),
            'funder': work.get('funder', []),
        }
    
    def validate_doi(self, doi: str) -> bool:
        """
        Check if a DOI exists in Crossref.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            True if DOI exists, False otherwise
        """
        work = self.get_work_by_doi(doi)
        return work is not None
