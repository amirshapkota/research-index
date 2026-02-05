"""
Views for managing NepJOL import operations with real-time status tracking
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import threading
import json

from .services.nepjol_scraper import NepJOLScraper
from .management.commands.import_nepjol import Command as ImportCommand
from publications.models import Journal, Publication, Issue
from users.models import Institution


class NepJOLImportStatusView(APIView):
    """
    Get current status of NepJOL import operation
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['NepJOL Import'],
        summary='Get Import Status',
        description='Get real-time status of ongoing or last NepJOL import operation',
        responses={
            200: OpenApiResponse(
                description='Import status retrieved successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'is_running': {'type': 'boolean'},
                        'started_at': {'type': 'string', 'format': 'date-time', 'nullable': True},
                        'current_journal': {'type': 'string', 'nullable': True},
                        'current_journal_index': {'type': 'integer'},
                        'total_journals': {'type': 'integer'},
                        'current_issue': {'type': 'string', 'nullable': True},
                        'current_article': {'type': 'string', 'nullable': True},
                        'progress_percentage': {'type': 'number'},
                        'stats': {
                            'type': 'object',
                            'properties': {
                                'journals_processed': {'type': 'integer'},
                                'journals_created': {'type': 'integer'},
                                'issues_created': {'type': 'integer'},
                                'authors_created': {'type': 'integer'},
                                'authors_matched': {'type': 'integer'},
                                'publications_created': {'type': 'integer'},
                                'publications_skipped': {'type': 'integer'},
                                'pdfs_downloaded': {'type': 'integer'},
                                'errors': {'type': 'integer'},
                            }
                        },
                        'last_update': {'type': 'string', 'format': 'date-time', 'nullable': True},
                        'estimated_time_remaining': {'type': 'string', 'nullable': True},
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get current import status"""
        status_data = cache.get('nepjol_import_status')
        
        if not status_data:
            # Return default status
            return Response({
                'is_running': False,
                'started_at': None,
                'current_journal': None,
                'current_journal_index': 0,
                'total_journals': 0,
                'current_issue': None,
                'current_article': None,
                'progress_percentage': 0,
                'stats': {
                    'journals_processed': 0,
                    'journals_created': 0,
                    'issues_created': 0,
                    'authors_created': 0,
                    'authors_matched': 0,
                    'publications_created': 0,
                    'publications_skipped': 0,
                    'pdfs_downloaded': 0,
                    'errors': 0,
                },
                'last_update': None,
                'estimated_time_remaining': None,
            })
        
        return Response(status_data)


class NepJOLImportStartView(APIView):
    """
    Start a new NepJOL import operation
    """
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['NepJOL Import'],
        summary='Start NepJOL Import',
        description='Start importing journals and publications from NepJOL. This is a background operation.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'max_journals': {
                        'type': 'integer',
                        'description': 'Maximum number of journals to import (null for all)',
                        'nullable': True
                    },
                    'max_articles_per_journal': {
                        'type': 'integer',
                        'description': 'Maximum articles per journal (null for all)',
                        'nullable': True
                    },
                    'skip_duplicates': {
                        'type': 'boolean',
                        'description': 'Skip publications that already exist',
                        'default': True
                    },
                    'download_pdfs': {
                        'type': 'boolean',
                        'description': 'Download PDF files for publications',
                        'default': True
                    },
                    'test_mode': {
                        'type': 'boolean',
                        'description': 'Test mode: import only 1 journal with 1 issue',
                        'default': False
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                'Test Import',
                value={
                    'test_mode': True,
                    'download_pdfs': True
                },
                request_only=True,
            ),
            OpenApiExample(
                'Limited Import',
                value={
                    'max_journals': 5,
                    'max_articles_per_journal': 10,
                    'download_pdfs': False
                },
                request_only=True,
            ),
            OpenApiExample(
                'Full Import',
                value={
                    'skip_duplicates': True,
                    'download_pdfs': True
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Import started successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'status': {'type': 'string'},
                        'started_at': {'type': 'string', 'format': 'date-time'}
                    }
                }
            ),
            400: OpenApiResponse(description='Import already running'),
            500: OpenApiResponse(description='Failed to start import')
        }
    )
    def post(self, request):
        """Start import operation"""
        # Check if import is already running
        current_status = cache.get('nepjol_import_status')
        if current_status and current_status.get('is_running'):
            return Response(
                {'error': 'Import is already running. Please wait for it to complete.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get parameters
        options = {
            'max_journals': request.data.get('max_journals'),
            'max_articles_per_journal': request.data.get('max_articles_per_journal'),
            'skip_duplicates': request.data.get('skip_duplicates', True),
            'download_pdfs': request.data.get('download_pdfs', True),
            'test_mode': request.data.get('test_mode', False),
        }
        
        # Initialize status
        initial_status = {
            'is_running': True,
            'started_at': timezone.now().isoformat(),
            'current_journal': None,
            'current_journal_index': 0,
            'total_journals': 0,
            'current_issue': None,
            'current_article': None,
            'progress_percentage': 0,
            'stats': {
                'journals_processed': 0,
                'journals_created': 0,
                'issues_created': 0,
                'authors_created': 0,
                'authors_matched': 0,
                'publications_created': 0,
                'publications_skipped': 0,
                'pdfs_downloaded': 0,
                'errors': 0,
            },
            'last_update': timezone.now().isoformat(),
            'estimated_time_remaining': None,
            'options': options,
        }
        
        cache.set('nepjol_import_status', initial_status, timeout=86400)  # 24 hours
        
        # Start import in background thread
        thread = threading.Thread(
            target=self._run_import,
            args=(options,),
            daemon=True
        )
        thread.start()
        
        return Response({
            'message': 'NepJOL import started successfully',
            'status': 'running',
            'started_at': initial_status['started_at']
        })
    
    def _run_import(self, options):
        """Run import operation in background"""
        try:
            from io import StringIO
            import sys
            
            # Create custom stdout to capture output
            output = StringIO()
            
            # Initialize scraper and command
            scraper = NepJOLScraper(delay=1.0)
            cmd = ImportCommand()
            cmd.stdout = output
            
            # Get or create institution
            institution = Institution.objects.filter(institution_name='External Imports').first()
            if not institution:
                from users.models import CustomUser
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
            
            # Get journals list
            self._update_status(current_stage='Fetching journals list...')
            journals = scraper.get_all_journals()
            
            if not journals:
                self._update_status(
                    is_running=False,
                    current_stage='Failed to fetch journals',
                    error='Could not retrieve journals from NepJOL'
                )
                return
            
            # Limit journals based on options
            if options['test_mode']:
                journals = journals[:1]
            elif options['max_journals']:
                journals = journals[:options['max_journals']]
            
            self._update_status(total_journals=len(journals))
            
            # Statistics
            stats = {
                'journals_processed': 0,
                'journals_created': 0,
                'issues_created': 0,
                'authors_created': 0,
                'authors_matched': 0,
                'publications_created': 0,
                'publications_skipped': 0,
                'pdfs_downloaded': 0,
                'errors': 0,
            }
            
            start_time = timezone.now()
            
            # Process each journal
            for idx, journal_data in enumerate(journals, 1):
                try:
                    journal_name = journal_data['name']
                    journal_url = journal_data['url']
                    
                    self._update_status(
                        current_journal=journal_name,
                        current_journal_index=idx,
                        current_stage=f'Processing journal {idx}/{len(journals)}: {journal_name}',
                        progress_percentage=(idx - 1) / len(journals) * 100
                    )
                    
                    # Create journal
                    journal = cmd.get_or_create_journal(scraper, institution, journal_name, journal_url)
                    if journal:
                        if hasattr(cmd, '_journal_created') and cmd._journal_created:
                            stats['journals_created'] += 1
                    else:
                        stats['errors'] += 1
                        continue
                    
                    stats['journals_processed'] += 1
                    
                    # Get issues
                    max_issues = 1 if options['test_mode'] else None
                    issues = scraper.get_journal_issues(journal_url)
                    
                    if max_issues:
                        issues = issues[:max_issues]
                    
                    # Process each issue
                    for issue_data in issues:
                        issue_title = issue_data.get('title', 'Issue')
                        self._update_status(current_issue=issue_title)
                        
                        # Create issue
                        issue = cmd.get_or_create_issue(journal, issue_data)
                        if issue:
                            stats['issues_created'] += 1
                        else:
                            continue
                        
                        # Get articles from issue
                        articles = scraper.get_articles_from_issue(issue_data['url'])
                        
                        if options['max_articles_per_journal']:
                            articles = articles[:options['max_articles_per_journal']]
                        
                        # Import each article
                        for article in articles:
                            try:
                                article_title = article.get('title', 'Unknown')[:60]
                                self._update_status(current_article=article_title)
                                
                                # Get full details
                                full_article = scraper.get_article_details(article['url'])
                                if not full_article:
                                    stats['errors'] += 1
                                    continue
                                
                                article_data = {**article, **full_article}
                                
                                # Import article
                                result = cmd.import_article(
                                    article_data,
                                    journal,
                                    issue,
                                    institution,
                                    options['skip_duplicates'],
                                    options['download_pdfs']
                                )
                                
                                if result == 'created':
                                    stats['publications_created'] += 1
                                    if hasattr(cmd, '_pdf_downloaded') and cmd._pdf_downloaded:
                                        stats['pdfs_downloaded'] += 1
                                    if hasattr(cmd, '_author_created') and cmd._author_created:
                                        stats['authors_created'] += 1
                                    if hasattr(cmd, '_author_matched') and cmd._author_matched:
                                        stats['authors_matched'] += 1
                                elif result == 'skipped':
                                    stats['publications_skipped'] += 1
                                else:
                                    stats['errors'] += 1
                                
                                # Update stats
                                self._update_status(stats=stats)
                                
                            except Exception as e:
                                stats['errors'] += 1
                                self._update_status(stats=stats)
                    
                    # Calculate estimated time remaining
                    elapsed = (timezone.now() - start_time).total_seconds()
                    avg_time_per_journal = elapsed / idx
                    remaining_journals = len(journals) - idx
                    estimated_seconds = avg_time_per_journal * remaining_journals
                    estimated_time = str(timedelta(seconds=int(estimated_seconds)))
                    
                    self._update_status(
                        stats=stats,
                        progress_percentage=idx / len(journals) * 100,
                        estimated_time_remaining=estimated_time
                    )
                    
                except Exception as e:
                    stats['errors'] += 1
                    self._update_status(stats=stats)
            
            # Mark as complete
            self._update_status(
                is_running=False,
                current_stage='Import completed',
                current_journal=None,
                current_issue=None,
                current_article=None,
                progress_percentage=100,
                stats=stats,
                estimated_time_remaining=None
            )
            
        except Exception as e:
            self._update_status(
                is_running=False,
                current_stage='Import failed',
                error=str(e),
                progress_percentage=0
            )
    
    def _update_status(self, **kwargs):
        """Update import status in cache"""
        current_status = cache.get('nepjol_import_status', {})
        
        # Update with new values
        current_status.update(kwargs)
        current_status['last_update'] = timezone.now().isoformat()
        
        # Update stats if provided
        if 'stats' in kwargs:
            current_stats = current_status.get('stats', {})
            current_stats.update(kwargs['stats'])
            current_status['stats'] = current_stats
        
        cache.set('nepjol_import_status', current_status, timeout=86400)


class NepJOLImportStopView(APIView):
    """
    Stop ongoing NepJOL import operation
    """
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['NepJOL Import'],
        summary='Stop Import',
        description='Stop the currently running NepJOL import operation',
        responses={
            200: OpenApiResponse(
                description='Import stopped successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string'},
                        'stats': {'type': 'object'}
                    }
                }
            ),
            400: OpenApiResponse(description='No import is currently running')
        }
    )
    def post(self, request):
        """Stop import operation"""
        current_status = cache.get('nepjol_import_status')
        
        if not current_status or not current_status.get('is_running'):
            return Response(
                {'error': 'No import is currently running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as stopped
        current_status['is_running'] = False
        current_status['current_stage'] = 'Stopped by user'
        current_status['last_update'] = timezone.now().isoformat()
        cache.set('nepjol_import_status', current_status, timeout=86400)
        
        return Response({
            'message': 'Import stopped successfully',
            'stats': current_status.get('stats', {})
        })


class NepJOLImportHistoryView(APIView):
    """
    Get import history and logs
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['NepJOL Import'],
        summary='Get Import History',
        description='Get history of NepJOL import operations',
        responses={
            200: OpenApiResponse(
                description='Import history retrieved successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'total_journals': {'type': 'integer'},
                        'total_issues': {'type': 'integer'},
                        'total_publications': {'type': 'integer'},
                        'last_import': {
                            'type': 'object',
                            'properties': {
                                'started_at': {'type': 'string'},
                                'completed_at': {'type': 'string'},
                                'stats': {'type': 'object'}
                            }
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get import history"""
        # Get totals from database
        institution = Institution.objects.filter(institution_name='External Imports').first()
        
        if institution:
            total_journals = Journal.objects.filter(institution=institution).count()
            total_issues = Issue.objects.filter(journal__institution=institution).count()
            total_publications = Publication.objects.filter(journal__institution=institution).count()
        else:
            total_journals = 0
            total_issues = 0
            total_publications = 0
        
        # Get last import status
        last_status = cache.get('nepjol_import_status')
        
        return Response({
            'total_journals': total_journals,
            'total_issues': total_issues,
            'total_publications': total_publications,
            'last_import': last_status if last_status else None
        })


class NepJOLAvailableJournalsView(APIView):
    """
    Get list of available journals from NepJOL
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['NepJOL Import'],
        summary='Get Available Journals',
        description='Fetch list of all journals available on NepJOL without importing',
        responses={
            200: OpenApiResponse(
                description='Journals list retrieved successfully',
                response={
                    'type': 'object',
                    'properties': {
                        'total': {'type': 'integer'},
                        'journals': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string'},
                                    'url': {'type': 'string'},
                                    'short_name': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        """Get available journals from NepJOL"""
        try:
            scraper = NepJOLScraper(delay=0.5)
            journals = scraper.get_all_journals()
            
            return Response({
                'total': len(journals),
                'journals': journals
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch journals: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
