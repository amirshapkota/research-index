"""
Data mapper for transforming external API data to internal models.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify

from publications.models import Publication, Journal, Issue, PublicationStats
from users.models import Author, Institution

logger = logging.getLogger(__name__)


class ExternalDataMapper:
    """
    Maps external journal API data to internal research index models.
    """
    
    def __init__(self):
        self.journals_cache = {}
        self.authors_cache = {}
        self.issues_cache = {}
    
    def map_and_create_publication(self, external_data: Dict) -> Optional[Publication]:
        """
        Map external publication data and create/update internal publication.
        
        Args:
            external_data: Publication data from external API
            
        Returns:
            Created or updated Publication instance, or None if error
        """
        try:
            with transaction.atomic():
                # Get or create journal
                journal = self._get_or_create_journal(external_data.get('journal', {}))
                if not journal:
                    logger.warning(f"Could not create journal for publication: {external_data.get('title')}")
                    return None
                
                # Get or create author
                author = self._get_or_create_author(external_data)
                if not author:
                    logger.warning(f"Could not create author for publication: {external_data.get('title')}")
                    return None
                
                # Get or create issue if volume/issue exists
                issue = self._get_or_create_issue(journal, external_data.get('publication_details', {}))
                
                # Check if publication already exists (by external ID or DOI)
                external_id = external_data.get('id')
                doi = external_data.get('doi')
                
                publication = None
                if doi:
                    publication = Publication.objects.filter(doi=doi).first()
                
                # Create or update publication
                pub_details = external_data.get('publication_details', {})
                
                publication_data = {
                    'title': external_data.get('title', ''),
                    'abstract': self._clean_html(external_data.get('abstract', '')),
                    'author': author,
                    'journal': journal,
                    'doi': doi or '',
                    'volume': pub_details.get('volume', ''),
                    'issue': pub_details.get('issue', ''),
                    'pages': pub_details.get('pages', ''),
                    'is_published': True,
                    'published_date': self._parse_date(pub_details.get('published_date')),
                    'co_authors': self._format_coauthors(external_data.get('authors', [])),
                }
                
                if publication:
                    # Update existing
                    for key, value in publication_data.items():
                        setattr(publication, key, value)
                    publication.save()
                    logger.info(f"Updated publication: {publication.title}")
                else:
                    # Create new
                    publication = Publication.objects.create(**publication_data)
                    logger.info(f"Created publication: {publication.title}")
                
                # Add to issue if exists
                if issue and publication:
                    from publications.models import IssueArticle
                    IssueArticle.objects.get_or_create(
                        issue=issue,
                        publication=publication,
                    )
                
                # Download and attach document
                self._download_and_attach_document(publication, external_data.get('documents', []))
                
                return publication
                
        except Exception as e:
            logger.error(f"Error mapping publication '{external_data.get('title')}': {e}")
            return None
    
    def _get_or_create_journal(self, journal_data: Dict) -> Optional[Journal]:
        """Get or create journal from external data."""
        if not journal_data:
            return None
        
        journal_id = journal_data.get('id')
        if journal_id in self.journals_cache:
            return self.journals_cache[journal_id]
        
        issn = journal_data.get('issn_online') or journal_data.get('issn_print')
        
        # Try to find existing journal by ISSN or title
        journal = None
        if issn:
            journal = Journal.objects.filter(e_issn=issn).first()
            if not journal:
                journal = Journal.objects.filter(issn=issn).first()
        
        if not journal:
            # Try by title
            title = journal_data.get('title', '')
            journal = Journal.objects.filter(title__iexact=title).first()
        
        if not journal:
            # Create new journal - need an institution
            # For now, create a default institution or use existing one
            institution = self._get_default_institution()
            
            journal = Journal.objects.create(
                title=journal_data.get('title', ''),
                short_title=journal_data.get('short_name', ''),
                issn=journal_data.get('issn_print', ''),
                e_issn=journal_data.get('issn_online', ''),
                publisher_name=journal_data.get('publisher', ''),
                website=journal_data.get('website_url', ''),
                institution=institution,
                is_active=True,
            )
            logger.info(f"Created new journal: {journal.title}")
        
        self.journals_cache[journal_id] = journal
        return journal
    
    def _get_or_create_author(self, publication_data: Dict) -> Optional[Author]:
        """Get or create author from external data."""
        # Use corresponding author as primary author
        corresponding_author = publication_data.get('corresponding_author', {})
        if not corresponding_author and publication_data.get('authors'):
            # Use first author
            corresponding_author = publication_data['authors'][0]
        
        if not corresponding_author:
            return self._get_default_author()
        
        author_id = corresponding_author.get('id')
        if author_id in self.authors_cache:
            return self.authors_cache[author_id]
        
        # Try to find author by name
        display_name = corresponding_author.get('display_name', '')
        author = Author.objects.filter(full_name__iexact=display_name).first()
        
        if not author:
            # Create new author - need a user
            from users.models import CustomUser
            
            # Create user for author
            email = f"{slugify(display_name)}@external.import"
            user = CustomUser.objects.filter(email=email).first()
            
            if not user:
                import secrets
                random_password = secrets.token_urlsafe(16)
                user = CustomUser.objects.create_user(
                    email=email,
                    password=random_password,
                    user_type='author',
                    is_active=False  # Mark as inactive since it's an import
                )
            
            author = Author.objects.create(
                user=user,
                full_name=display_name,
                institute=corresponding_author.get('affiliation_name', ''),
            )
            logger.info(f"Created new author: {author.full_name}")
        
        self.authors_cache[author_id] = author
        return author
    
    def _get_or_create_issue(self, journal: Journal, pub_details: Dict) -> Optional[Issue]:
        """Get or create issue from publication details."""
        volume = pub_details.get('volume', '').strip()
        issue_number = pub_details.get('issue', '').strip()
        
        if not volume or not issue_number:
            return None
        
        cache_key = f"{journal.id}-{volume}-{issue_number}"
        if cache_key in self.issues_cache:
            return self.issues_cache[cache_key]
        
        # Try to find existing issue
        issue = Issue.objects.filter(
            journal=journal,
            volume=int(volume) if volume.isdigit() else 1,
            issue_number=int(issue_number) if issue_number.isdigit() else 1,
        ).first()
        
        if not issue:
            # Create new issue
            year = pub_details.get('year')
            publication_date = self._parse_date(pub_details.get('published_date'))
            
            issue = Issue.objects.create(
                journal=journal,
                volume=int(volume) if volume.isdigit() else 1,
                issue_number=int(issue_number) if issue_number.isdigit() else 1,
                title=f"Volume {volume}, Issue {issue_number}",
                publication_date=publication_date,
                status='published',
            )
            logger.info(f"Created new issue: {issue.title} for {journal.title}")
        
        self.issues_cache[cache_key] = issue
        return issue
    
    def _download_and_attach_document(self, publication: Publication, documents: List[Dict]):
        """Download and attach documents to publication."""
        if not documents:
            return
        
        from publications.services.external_api import ExternalJournalAPI
        api = ExternalJournalAPI()
        
        for doc in documents:
            if doc.get('document_type') == 'MANUSCRIPT':
                document_id = doc.get('id')
                file_name = doc.get('file_name', 'document.pdf')
                
                # Download document
                content = api.download_document(document_id)
                if content:
                    # Save to publication pdf_file
                    publication.pdf_file.save(
                        file_name,
                        ContentFile(content),
                        save=True
                    )
                    logger.info(f"Attached document {file_name} to publication {publication.title}")
                    break  # Only attach first manuscript
    
    def _get_default_institution(self) -> Institution:
        """Get or create default institution for external imports."""
        institution, created = Institution.objects.get_or_create(
            institution_name='External Imports',
            defaults={
                'user': self._get_or_create_system_user('institution'),
                'institution_type': 'other',
                'description': 'Default institution for externally imported publications',
            }
        )
        return institution
    
    def _get_default_author(self) -> Author:
        """Get or create default author for external imports."""
        author, created = Author.objects.get_or_create(
            full_name='Unknown Author',
            defaults={
                'user': self._get_or_create_system_user('author'),
            }
        )
        return author
    
    def _get_or_create_system_user(self, user_type: str):
        """Get or create system user for imports."""
        from users.models import CustomUser
        
        email = f'system.{user_type}@researchindex.import'
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'user_type': user_type,
                'is_active': False,
            }
        )
        return user
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_text)
    
    def _parse_date(self, date_str: Optional[str]):
        """Parse ISO date string to date object."""
        if not date_str:
            return None
        
        try:
            # Try parsing ISO format and extract date
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except:
            return None
    
    def _extract_page_start(self, pages: str) -> Optional[int]:
        """Extract starting page from page range string like '121-124'."""
        if not pages or '-' not in pages:
            return None
        
        try:
            return int(pages.split('-')[0].strip())
        except:
            return None
    
    def _extract_page_end(self, pages: str) -> Optional[int]:
        """Extract ending page from page range string like '121-124'."""
        if not pages or '-' not in pages:
            return None
        
        try:
            return int(pages.split('-')[1].strip())
        except:
            return None
    
    def _format_coauthors(self, authors: List[Dict]) -> str:
        """Format coauthors list into comma-separated string."""
        if not authors or len(authors) <= 1:
            return ''
        
        # Skip first author (already set as main author), get the rest
        coauthor_names = [
            author.get('display_name', '')
            for author in authors[1:]
            if author.get('display_name')
        ]
        
        return ', '.join(coauthor_names)
