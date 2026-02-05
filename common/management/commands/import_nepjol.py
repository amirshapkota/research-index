"""
Django management command to scrape and import publications from NepJOL (Nepal Journals Online).

Usage:
    python manage.py import_nepjol                    # Import all journals
    python manage.py import_nepjol --journals=5       # Import first 5 journals
    python manage.py import_nepjol --max-articles=100 # Limit to 100 articles per journal
    python manage.py import_nepjol --test             # Test mode: scrape 1 journal, 1 issue
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.files.base import ContentFile
from common.services.nepjol_scraper import NepJOLScraper
from publications.models import Publication, Journal, Reference, Issue, IssueArticle
from users.models import Institution, Author, CustomUser
import logging
from datetime import datetime
import requests
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape and import publications from NepJOL (Nepal Journals Online)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--journals',
            type=int,
            default=None,
            help='Number of journals to import (default: all)'
        )
        parser.add_argument(
            '--max-articles',
            type=int,
            default=None,
            help='Maximum articles per journal (default: all)'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode: scrape 1 journal with 1 issue'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            default=True,
            help='Skip publications that already exist by DOI (default: True)'
        )
        parser.add_argument(
            '--download-pdfs',
            action='store_true',
            default=True,
            help='Download PDFs for publications (default: True)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting NepJOL import...'))
        
        # Initialize scraper
        scraper = NepJOLScraper(delay=1.0)
        
        # Statistics
        stats = {
            'journals_processed': 0,
            'journals_created': 0,
            'authors_created': 0,
            'authors_matched': 0,
            'publications_created': 0,
            'publications_skipped': 0,
            'pdfs_downloaded': 0,
            'errors': 0,
        }
        
        # Get or create "External Imports" institution
        institution = Institution.objects.filter(institution_name='External Imports').first()
        
        if not institution:
            user = CustomUser.objects.create(
                email='external_imports@researchindex.np',
                user_type='institution',
                is_active=False,
            )
            institution = Institution.objects.create(
                user=user,
                institution_name='External Imports',
                institution_type='research_institute',
                country='Nepal',
                website='https://nepjol.info',
                description='Auto-created institution for publications imported from external sources',
            )
            self.stdout.write(self.style.SUCCESS(f'Created "External Imports" institution'))
        
        # Get journals list
        self.stdout.write('Fetching journals list from NepJOL...')
        journals = scraper.get_all_journals()
        
        if not journals:
            self.stdout.write(self.style.ERROR('Failed to fetch journals'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(journals)} journals on NepJOL'))
        
        # Limit journals if specified
        if options['test']:
            journals = journals[:1]
            self.stdout.write(self.style.WARNING('TEST MODE: Processing only 1 journal'))
        elif options['journals']:
            journals = journals[:options['journals']]
            self.stdout.write(self.style.WARNING(f'Processing only {options["journals"]} journals'))
        
        # Process each journal
        for journal_data in journals:
            try:
                stats['journals_processed'] += 1
                journal_name = journal_data['name']
                journal_url = journal_data['url']
                
                self.stdout.write(f'\n[{stats["journals_processed"]}/{len(journals)}] Processing: {journal_name}')
                
                # Get or create journal in database
                journal = self.get_or_create_journal(scraper, institution, journal_name, journal_url)
                if journal:
                    if hasattr(self, '_journal_created') and self._journal_created:
                        stats['journals_created'] += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created journal: {journal.title}'))
                    else:
                        self.stdout.write(f'  ✓ Using existing journal: {journal.title}')
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to create/find journal'))
                    stats['errors'] += 1
                    continue
                
                # Scrape issues and articles from this journal
                max_issues = 1 if options['test'] else None
                issues = scraper.get_journal_issues(journal_url)
                
                if not issues:
                    self.stdout.write(self.style.WARNING(f'  ⚠ No issues found'))
                    continue
                
                if max_issues:
                    issues = issues[:max_issues]
                
                self.stdout.write(f'  Found {len(issues)} issues')
                
                # Import each issue and its articles
                articles_imported = 0
                for issue_data in issues:
                    # Get or create issue
                    issue_instance = self.get_or_create_issue(journal, issue_data)
                    if not issue_instance:
                        continue
                    
                    # Get articles from this issue
                    articles = scraper.get_articles_from_issue(issue_data['url'])
                    
                    # Limit articles if specified
                    if options['max_articles']:
                        articles = articles[:options['max_articles']]
                    
                    # Import each article
                    for article in articles:
                        try:
                            # Get full article details
                            full_article = scraper.get_article_details(article['url'])
                            if not full_article:
                                continue
                            
                            # Merge basic and detailed data
                            article_data = {**article, **full_article}
                            
                            result = self.import_article(
                                article_data, 
                                journal,
                                issue_instance,
                                institution,
                                options['skip_duplicates'],
                                options['download_pdfs']
                            )
                            if result == 'created':
                                stats['publications_created'] += 1
                                articles_imported += 1
                                if hasattr(self, '_pdf_downloaded') and self._pdf_downloaded:
                                    stats['pdfs_downloaded'] += 1
                                if hasattr(self, '_author_created') and self._author_created:
                                    stats['authors_created'] += 1
                                if hasattr(self, '_author_matched') and self._author_matched:
                                    stats['authors_matched'] += 1
                            elif result == 'skipped':
                                stats['publications_skipped'] += 1
                        except Exception as e:
                            logger.error(f'Error importing article "{article.get("title", "Unknown")}": {str(e)}')
                            stats['errors'] += 1
                
                self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {articles_imported} new articles'))
                
            except Exception as e:
                logger.error(f'Error processing journal "{journal_data.get("name", "Unknown")}": {str(e)}')
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                stats['errors'] += 1
        
        # Print final statistics
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Import completed!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Journals processed:       {stats["journals_processed"]}')
        self.stdout.write(f'Journals created:         {stats["journals_created"]}')
        self.stdout.write(f'Authors created:          {stats["authors_created"]}')
        self.stdout.write(f'Authors matched:          {stats["authors_matched"]}')
        self.stdout.write(f'Publications created:     {stats["publications_created"]}')
        self.stdout.write(f'Publications skipped:     {stats["publications_skipped"]}')
        self.stdout.write(f'PDFs downloaded:          {stats["pdfs_downloaded"]}')
        self.stdout.write(f'Errors:                   {stats["errors"]}')
        self.stdout.write('='*60)

    def get_or_create_journal(self, scraper, institution, journal_name, journal_url):
        """
        Get or create a journal in the database with cover image, description, and ISSN.
        Returns the journal instance or None if error.
        """
        try:
            # Try to find existing journal by exact title match
            journal = Journal.objects.filter(title__iexact=journal_name).first()
            
            if journal:
                self._journal_created = False
                return journal
            
            # Get journal details (description, ISSN, cover image)
            journal_details = scraper.get_journal_details(journal_url)
            if not journal_details:
                journal_details = {}
            
            description = journal_details.get('description', '')
            if not description:
                description = f'Academic journal published on NepJOL'
            
            issn = journal_details.get('issn', '')
            cover_image_url = journal_details.get('cover_image_url', '')
            
            # Create new journal
            with transaction.atomic():
                journal = Journal.objects.create(
                    institution=institution,
                    title=journal_name[:300],
                    description=description[:5000],
                    issn=issn[:20] if issn else '',
                    website=journal_url,
                    is_active=True,
                    is_open_access=True,
                    publisher_name='NepJOL',
                    language='English',
                )
                
                # Download and save cover image
                if cover_image_url:
                    try:
                        response = requests.get(cover_image_url, timeout=30)
                        if response.status_code == 200:
                            filename = f"journal_{journal.id}_cover.jpg"
                            journal.cover_image.save(filename, ContentFile(response.content), save=True)
                            logger.info(f"Downloaded cover image for journal: {journal_name}")
                    except Exception as e:
                        logger.warning(f"Failed to download cover image: {str(e)}")
                
                self._journal_created = True
                return journal
                
        except Exception as e:
            logger.error(f'Error creating journal "{journal_name}": {str(e)}')
            return None

    def get_or_create_issue(self, journal, issue_data):
        """
        Get or create an issue for a journal.
        Returns the Issue instance or None.
        """
        try:
            volume = issue_data.get('volume')
            issue_number = issue_data.get('issue_number')
            
            # If we don't have volume/issue numbers, try to extract from title
            if not volume or not issue_number:
                import re
                title = issue_data.get('title', '')
                
                # Try to extract volume
                if not volume:
                    vol_match = re.search(r'Vol\.?\s*(\d+)', title, re.IGNORECASE)
                    if vol_match:
                        volume = int(vol_match.group(1))
                
                # Try to extract issue number
                if not issue_number:
                    issue_match = re.search(r'(?:No\.?|Issue)\s*(\d+)', title, re.IGNORECASE)
                    if issue_match:
                        issue_number = int(issue_match.group(1))
            
            # Default to 1 if still not found
            if not volume:
                volume = 1
            if not issue_number:
                issue_number = 1
            
            # Try to find existing issue
            issue = Issue.objects.filter(
                journal=journal,
                volume=volume,
                issue_number=issue_number
            ).first()
            
            if issue:
                return issue
            
            # Extract publication date
            from datetime import date
            pub_date = date.today()
            
            # Try from published_date field first (format: "2025-07-25")
            if issue_data.get('published_date'):
                try:
                    date_str = issue_data.get('published_date')
                    pub_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
            # Try from year field
            elif issue_data.get('year'):
                try:
                    year = int(issue_data.get('year'))
                    pub_date = date(year, 1, 1)
                except (ValueError, TypeError):
                    pass
            # Try from title (year in parentheses)
            else:
                import re
                year_match = re.search(r'\((\d{4})\)', issue_data.get('title', ''))
                if year_match:
                    try:
                        year = int(year_match.group(1))
                        pub_date = date(year, 1, 1)
                    except (ValueError, TypeError):
                        pass
            
            # Create new issue
            with transaction.atomic():
                issue = Issue.objects.create(
                    journal=journal,
                    volume=volume,
                    issue_number=issue_number,
                    title=issue_data.get('title', '')[:300],
                    publication_date=pub_date,
                    status='published',
                )
                logger.info(f"Created issue: Vol. {volume}, No. {issue_number} for {journal.title}")
                return issue
                
        except Exception as e:
            logger.error(f'Error creating issue: {str(e)}')
            import traceback
            traceback.print_exc()
            return None
    
    def get_or_create_author(self, author_data, institution):
        """
        Get or create an author by ORCID or name.
        Returns the author instance.
        """
        author_name = author_data.get('name', '').strip()
        orcid = author_data.get('orcid', '').strip()
        affiliation = author_data.get('affiliation', '').strip()
        
        if not author_name:
            return None
        
        # Try to match by ORCID first
        if orcid:
            author = Author.objects.filter(orcid=orcid).first()
            if author:
                self._author_matched = True
                self._author_created = False
                return author
        
        # Try to match by full name
        author = Author.objects.filter(full_name__iexact=author_name).first()
        if author:
            # Update ORCID if we have it and author doesn't
            if orcid and not author.orcid:
                author.orcid = orcid
                author.save()
            self._author_matched = True
            self._author_created = False
            return author
        
        # Create new author
        try:
            with transaction.atomic():
                # Create user for author
                email = f"author_{orcid if orcid else author_name.replace(' ', '_').lower()}@imported.nepjol.np"
                # Make email unique
                if CustomUser.objects.filter(email=email).exists():
                    email = f"author_{orcid if orcid else author_name.replace(' ', '_').lower()}_{datetime.now().timestamp()}@imported.nepjol.np"
                
                user = CustomUser.objects.create(
                    email=email,
                    user_type='author',
                    is_active=False,  # Inactive until they claim the account
                )
                
                # Determine title (default to Dr. for imported authors)
                title = 'Dr.'
                
                author = Author.objects.create(
                    user=user,
                    title=title,
                    full_name=author_name,
                    institute=affiliation if affiliation else institution.institution_name,
                    designation='Researcher',
                    orcid=orcid if orcid else '',
                )
                
                self._author_created = True
                self._author_matched = False
                return author
                
        except Exception as e:
            logger.error(f'Error creating author "{author_name}": {str(e)}')
            return None

    def import_article(self, article_data, journal, issue, institution, skip_duplicates=True, download_pdfs=True):
        """
        Import a single article into the database with real author matching, PDF download,
        and proper issue linking.
        Returns: 'created', 'skipped', or 'error'
        """
        try:
            # Check for duplicates by DOI
            doi = article_data.get('doi', '').strip()
            if skip_duplicates and doi:
                if Publication.objects.filter(doi__iexact=doi).exists():
                    return 'skipped'
            
            # Prepare publication data
            title = article_data.get('title', '').strip()
            if not title:
                logger.warning('Article has no title, skipping')
                return 'error'
            
            # Handle published date
            year = article_data.get('year')
            published_date = None
            if year:
                try:
                    published_date = datetime(int(year), 1, 1).date()
                except (ValueError, TypeError):
                    pass
            
            # Extract and process authors
            authors_list = article_data.get('authors', [])
            primary_author = None
            co_authors_str = ''
            
            if authors_list:
                # Get or create first author as primary author
                first_author_data = authors_list[0]
                primary_author = self.get_or_create_author(first_author_data, institution)
                
                # Collect all author names for co_authors field
                author_names = []
                for auth in authors_list:
                    if isinstance(auth, dict):
                        author_names.append(auth.get('name', ''))
                    else:
                        author_names.append(str(auth))
                co_authors_str = ', '.join([name for name in author_names if name])
            
            # If we couldn't create/find primary author, skip
            if not primary_author:
                logger.warning(f'Could not determine primary author for "{title[:50]}...", skipping')
                return 'error'
            
            # Create publication
            with transaction.atomic():
                publication = Publication.objects.create(
                    author=primary_author,
                    title=title[:500],
                    abstract=article_data.get('abstract', '')[:10000],
                    publication_type='journal_article',
                    doi=doi[:255] if doi else '',
                    published_date=published_date,
                    journal=journal,
                    volume=article_data.get('volume', '')[:50],
                    issue=article_data.get('issue', '')[:50],
                    pages=article_data.get('pages', '')[:50],
                    publisher=journal.publisher_name,
                    co_authors=co_authors_str[:5000],
                    is_published=True,
                )
                
                # Download PDF if available
                self._pdf_downloaded = False
                pdf_url = article_data.get('pdf_url', '')
                if download_pdfs and pdf_url:
                    try:
                        response = requests.get(pdf_url, timeout=60, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        if response.status_code == 200:
                            # Extract filename from DOI or use publication ID
                            if doi:
                                filename = f"{doi.replace('/', '_').replace('.', '_')}.pdf"
                            else:
                                filename = f"publication_{publication.id}.pdf"
                            
                            publication.pdf_file.save(filename, ContentFile(response.content), save=True)
                            self._pdf_downloaded = True
                            logger.info(f"Downloaded PDF for: {title[:50]}")
                    except Exception as e:
                        logger.warning(f"Failed to download PDF: {str(e)}")
                
                # Add references if available
                references = article_data.get('references', [])
                if references:
                    for idx, ref_text in enumerate(references):
                        if ref_text and ref_text.strip():
                            Reference.objects.create(
                                publication=publication,
                                reference_text=ref_text[:5000],
                                order=idx + 1,
                            )
                
                # Link publication to issue via IssueArticle
                if issue:
                    IssueArticle.objects.create(
                        issue=issue,
                        publication=publication,
                        section='Article',
                    )
                    logger.info(f"Linked publication to Vol. {issue.volume}, No. {issue.issue_number}")
                
                return 'created'
                
        except Exception as e:
            logger.error(f'Error importing article: {str(e)}')
            import traceback
            traceback.print_exc()
            return 'error'
