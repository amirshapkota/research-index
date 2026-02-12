"""
Crossref API service for fetching citation data.
"""
import requests
import logging
from typing import Optional, Dict, Any
from time import sleep

logger = logging.getLogger(__name__)


class CrossrefCitationAPI:
    """
    Service to fetch citation counts and data from Crossref API.
    """
    BASE_URL = "https://api.crossref.org/works"
    
    def __init__(self, email: str = None):
        """
        Initialize Crossref API client.
        
        Args:
            email: Contact email for polite pool (gets faster response)
        """
        self.email = email or "admin@researchindex.np"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'ResearchIndexBot/1.0 (mailto:{self.email})'
        })
    
    def get_citation_count(self, doi: str) -> Optional[int]:
        """
        Get citation count for a DOI from Crossref.
        
        Args:
            doi: DOI of the publication
            
        Returns:
            Citation count or None if not found/error
        """
        if not doi:
            return None
        
        try:
            url = f"{self.BASE_URL}/{doi}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                
                # Crossref provides "is-referenced-by-count"
                citation_count = message.get('is-referenced-by-count', 0)
                
                logger.info(f"DOI {doi}: {citation_count} citations")
                return citation_count
            
            elif response.status_code == 404:
                logger.warning(f"DOI not found in Crossref: {doi}")
                return None
            
            else:
                logger.error(f"Crossref API error for {doi}: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching citations for DOI: {doi}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching citations for DOI {doi}: {e}")
            return None
        
        except Exception as e:
            logger.exception(f"Unexpected error for DOI {doi}: {e}")
            return None
    
    def get_citation_details(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed citation information for a DOI.
        
        Args:
            doi: DOI of the publication
            
        Returns:
            Dictionary with citation details or None
        """
        if not doi:
            return None
        
        try:
            url = f"{self.BASE_URL}/{doi}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                
                return {
                    'citation_count': message.get('is-referenced-by-count', 0),
                    'title': message.get('title', [''])[0] if message.get('title') else '',
                    'published_date': message.get('published-print') or message.get('published-online'),
                    'publisher': message.get('publisher', ''),
                    'container_title': message.get('container-title', [''])[0] if message.get('container-title') else '',
                }
            
            return None
            
        except Exception as e:
            logger.exception(f"Error fetching citation details for DOI {doi}: {e}")
            return None
    
    def batch_get_citations(self, dois: list[str], delay: float = 0.1) -> Dict[str, int]:
        """
        Get citation counts for multiple DOIs.
        
        Args:
            dois: List of DOIs
            delay: Delay between requests to respect API rate limits (seconds)
            
        Returns:
            Dictionary mapping DOI to citation count
        """
        results = {}
        
        for idx, doi in enumerate(dois, 1):
            if not doi:
                continue
            
            logger.info(f"Fetching citations [{idx}/{len(dois)}]: {doi}")
            
            count = self.get_citation_count(doi)
            if count is not None:
                results[doi] = count
            
            # Respect rate limits
            if idx < len(dois):
                sleep(delay)
        
        return results
