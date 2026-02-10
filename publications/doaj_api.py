"""
DOAJ (Directory of Open Access Journals) API Integration
API Documentation: https://doaj.org/api/v4/docs
"""

import requests
from typing import Dict, List, Optional, Any
from django.conf import settings
from urllib.parse import quote


class DOAJAPIError(Exception):
    """Custom exception for DOAJ API errors"""
    pass


class DOAJAPI:
    """
    Client for interacting with DOAJ API
    """
    BASE_URL = "https://doaj.org/api/"
    
    @staticmethod
    def search_journals(query: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        Search for journals in DOAJ using API v4
        
        Args:
            query: Search query (journal title, ISSN, etc.)
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict containing search results and pagination info
        """
        try:
            # Encode the search query for URL
            encoded_query = quote(query)
            
            # Build URL with pagination parameters
            params = {
                'page': page,
                'pageSize': page_size,
            }
            
            response = requests.get(
                f"{DOAJAPI.BASE_URL}search/journals/{encoded_query}",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'total': data.get('total', 0),
                'page': page,
                'page_size': page_size,
                'results': [DOAJAPI._format_journal(journal) for journal in data.get('results', [])]
            }
            
        except requests.exceptions.RequestException as e:
            raise DOAJAPIError(f"Failed to search DOAJ: {str(e)}")
    
    @staticmethod
    def get_journal_by_issn(issn: str) -> Optional[Dict[str, Any]]:
        """
        Get journal details by ISSN using API v4
        
        Args:
            issn: Journal ISSN (print or electronic) in format XXXX-XXXX
            
        Returns:
            Dict containing journal details or None if not found
        """
        try:
            # Format ISSN for search (DOAJ expects XXXX-XXXX format with hyphen)
            # If hyphen is missing, add it
            formatted_issn = issn
            if '-' not in issn and len(issn) == 8:
                formatted_issn = f"{issn[:4]}-{issn[4:]}"
            
            # Use the search endpoint with issn: prefix
            search_query = f"issn:{formatted_issn}"
            encoded_query = quote(search_query)
            
            response = requests.get(
                f"{DOAJAPI.BASE_URL}search/journals/{encoded_query}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if results:
                return DOAJAPI._format_journal(results[0])
            return None
            
        except requests.exceptions.RequestException as e:
            raise DOAJAPIError(f"Failed to fetch journal from DOAJ: {str(e)}")
    
    @staticmethod
    def _format_journal(raw_data: Dict) -> Dict[str, Any]:
        """
        Format DOAJ journal data to match our Journal model
        
        Args:
            raw_data: Raw journal data from DOAJ API
            
        Returns:
            Formatted journal data
        """
        bibjson = raw_data.get('bibjson', {})
        
        # Extract ISSNs (v4 API has them as direct fields)
        issn_print = bibjson.get('pissn', '')
        issn_electronic = bibjson.get('eissn', '')
        
        # Extract subjects/keywords
        subjects = []
        for subject in bibjson.get('subject', []):
            if 'term' in subject:
                subjects.append(subject['term'])
        
        # Extract languages
        languages = bibjson.get('language', [])
        primary_language = languages[0] if languages else 'English'
        
        # Extract publisher
        publisher = bibjson.get('publisher', {}).get('name', '')
        
        # Extract contact info
        editorial_contact = bibjson.get('editorial', {})
        contact_email = editorial_contact.get('contact_email', '') or \
                       bibjson.get('publisher', {}).get('contact_email', '')
        
        # Extract URLs
        journal_url = bibjson.get('ref', {}).get('journal', '')
        if not journal_url:
            for link in bibjson.get('link', []):
                if link.get('type') == 'homepage':
                    journal_url = link.get('url', '')
                    break
        
        # Extract licenses
        license_info = bibjson.get('license', [])
        license_type = license_info[0].get('type', '') if license_info else ''
        
        # Extract APC (Article Processing Charges) info
        apc = bibjson.get('apc', {})
        has_apc = apc.get('has_apc', False)
        apc_amount = None
        apc_currency = None
        if has_apc:
            apc_amount = apc.get('max', [{}])[0].get('price') if apc.get('max') else None
            apc_currency = apc.get('max', [{}])[0].get('currency') if apc.get('max') else None
        
        # Extract plagiarism detection
        plagiarism = bibjson.get('plagiarism', {})
        has_plagiarism_detection = plagiarism.get('detection', False)
        
        # Extract peer review info
        editorial_review = bibjson.get('editorial', {})
        review_process = editorial_review.get('review_process', [])
        peer_review_type = ', '.join(review_process) if review_process else ''
        
        # Extract publication time and OA start
        oa_start = bibjson.get('oa_start')
        # oa_start can be either an int (year) or dict with 'year' key
        if isinstance(oa_start, dict):
            oa_start_year = oa_start.get('year')
        elif isinstance(oa_start, int):
            oa_start_year = oa_start
        else:
            oa_start_year = None
        publication_time_weeks = bibjson.get('publication_time_weeks')
        
        return {
            # Basic Info
            'doaj_id': raw_data.get('id', ''),
            'title': bibjson.get('title', ''),
            'alternative_title': bibjson.get('alternative_title', ''),
            'issn': issn_print or '',
            'e_issn': issn_electronic or '',
            
            # Publication Info
            'publisher_name': publisher,
            'language': primary_language,
            'languages': languages,
            'subjects': subjects,
            
            # Open Access Info
            'is_open_access': True,  # All DOAJ journals are OA
            'license': license_type,
            'has_apc': has_apc,
            'apc_amount': apc_amount,
            'apc_currency': apc_currency,
            
            # Contact Info
            'contact_email': contact_email,
            'website': journal_url,
            
            # Review Info
            'peer_reviewed': True,  # All DOAJ journals are peer-reviewed
            'peer_review_type': peer_review_type,
            'has_plagiarism_detection': has_plagiarism_detection,
            'publication_time_weeks': publication_time_weeks,
            
            # Additional metadata
            'keywords': ', '.join(subjects[:10]),  # First 10 subjects as keywords
            'country': bibjson.get('publisher', {}).get('country', ''),
            'oa_start_year': oa_start_year,
            
            # Raw data for reference
            'doaj_raw_data': raw_data,
        }
