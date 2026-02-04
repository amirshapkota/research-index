"""
Utility functions for Crossref integration
"""

from typing import Dict, Optional, List
from publications.models import Publication
from common.services.crossref import CrossrefService
import logging

logger = logging.getLogger(__name__)


def import_publication_from_doi(doi: str, created_by=None) -> Optional[Publication]:
    """
    Import a publication from Crossref into the database using its DOI.
    
    Args:
        doi: Digital Object Identifier
        created_by: User who is importing (optional)
        
    Returns:
        Publication instance or None if import fails
    """
    service = CrossrefService()
    work = service.get_work_by_doi(doi)
    
    if not work:
        logger.error(f"DOI {doi} not found in Crossref")
        return None
    
    # Extract normalized data
    data = service.extract_publication_data(work)
    
    try:
        # Check if publication already exists
        existing = Publication.objects.filter(doi=doi).first()
        if existing:
            logger.info(f"Publication with DOI {doi} already exists")
            return existing
        
        # Create new publication
        publication = Publication.objects.create(
            title=data['title'],
            doi=data['doi'],
            abstract=data.get('abstract', ''),
            publication_date=data.get('published_date'),
            journal_name=data.get('journal', ''),
            volume=data.get('volume', ''),
            issue=data.get('issue', ''),
            pages=data.get('page', ''),
            publisher=data.get('publisher', ''),
            url=data.get('url', ''),
            citation_count=data.get('citation_count', 0),
        )
        
        logger.info(f"Successfully imported publication: {publication.title}")
        return publication
        
    except Exception as e:
        logger.error(f"Error importing publication from DOI {doi}: {str(e)}")
        return None


def enrich_publication_from_crossref(publication: Publication) -> bool:
    """
    Enrich an existing publication with data from Crossref.
    Useful for updating citation counts, references, etc.
    
    Args:
        publication: Publication instance with a DOI
        
    Returns:
        True if enrichment successful, False otherwise
    """
    if not publication.doi:
        logger.warning(f"Publication {publication.id} has no DOI")
        return False
    
    service = CrossrefService()
    work = service.get_work_by_doi(publication.doi)
    
    if not work:
        logger.error(f"DOI {publication.doi} not found in Crossref")
        return False
    
    try:
        # Extract data
        data = service.extract_publication_data(work)
        
        # Update fields
        if not publication.abstract and data.get('abstract'):
            publication.abstract = data['abstract']
        
        if not publication.journal_name and data.get('journal'):
            publication.journal_name = data['journal']
        
        if not publication.volume and data.get('volume'):
            publication.volume = data['volume']
        
        if not publication.issue and data.get('issue'):
            publication.issue = data['issue']
        
        if not publication.pages and data.get('page'):
            publication.pages = data['page']
        
        if not publication.publisher and data.get('publisher'):
            publication.publisher = data['publisher']
        
        # Always update citation count
        publication.citation_count = data.get('citation_count', 0)
        
        publication.save()
        
        logger.info(f"Successfully enriched publication: {publication.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error enriching publication {publication.id}: {str(e)}")
        return False


def bulk_import_from_dois(dois: List[str]) -> Dict[str, any]:
    """
    Import multiple publications from a list of DOIs.
    
    Args:
        dois: List of Digital Object Identifiers
        
    Returns:
        Dictionary with import results
    """
    results = {
        'success': [],
        'failed': [],
        'existing': [],
    }
    
    for doi in dois:
        # Check if exists first
        if Publication.objects.filter(doi=doi).exists():
            results['existing'].append(doi)
            continue
        
        publication = import_publication_from_doi(doi)
        if publication:
            results['success'].append(doi)
        else:
            results['failed'].append(doi)
    
    return results


def update_citation_counts():
    """
    Update citation counts for all publications with DOIs.
    Should be run periodically (e.g., weekly) via a scheduled task.
    
    Returns:
        Number of publications updated
    """
    publications = Publication.objects.exclude(doi__isnull=True).exclude(doi='')
    service = CrossrefService()
    updated_count = 0
    
    for pub in publications:
        try:
            citation_info = service.get_work_citations(pub.doi)
            if citation_info:
                pub.citation_count = citation_info.get('citation_count', 0)
                pub.save(update_fields=['citation_count'])
                updated_count += 1
        except Exception as e:
            logger.error(f"Error updating citation count for {pub.doi}: {str(e)}")
            continue
    
    logger.info(f"Updated citation counts for {updated_count} publications")
    return updated_count
