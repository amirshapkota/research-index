"""
Management command to sync publications from external journal management API.

Usage:
    python manage.py sync_external_publications
    python manage.py sync_external_publications --limit 10
    python manage.py sync_external_publications --full-sync
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from publications.services import ExternalJournalAPI, ExternalDataMapper
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync publications from external journal management API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of publications to sync (for testing)',
        )
        parser.add_argument(
            '--full-sync',
            action='store_true',
            help='Perform full sync of all publications (ignores limit)',
        )
        parser.add_argument(
            '--api-url',
            type=str,
            default=None,
            help='Override external API base URL',
        )
    
    def handle(self, *args, **options):
        limit = options.get('limit')
        full_sync = options.get('full_sync')
        api_url = options.get('api_url')
        
        self.stdout.write(self.style.SUCCESS('Starting publication sync...'))
        
        try:
            # Initialize API client
            api = ExternalJournalAPI(base_url=api_url) if api_url else ExternalJournalAPI()
            mapper = ExternalDataMapper()
            
            # Fetch publications
            if full_sync:
                self.stdout.write('Fetching all publications...')
                publications = api.fetch_all_publications()
            else:
                self.stdout.write(f'Fetching publications (limit: {limit or "all"})...')
                data = api.fetch_publications(page=1)
                publications = data.get('results', [])
                
                if limit:
                    publications = publications[:limit]
            
            total = len(publications)
            self.stdout.write(f'Found {total} publications to sync')
            
            # Process publications
            success_count = 0
            error_count = 0
            
            for idx, pub_data in enumerate(publications, 1):
                title = pub_data.get('title', 'Unknown')
                self.stdout.write(f'[{idx}/{total}] Processing: {title[:50]}...')
                
                try:
                    publication = mapper.map_and_create_publication(pub_data)
                    if publication:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Synced: {publication.title}')
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  ✗ Failed to create publication')
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Error: {str(e)}')
                    )
                    logger.exception(f"Error processing publication '{title}'")
            
            # Summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS(f'Sync completed!'))
            self.stdout.write(f'Total processed: {total}')
            self.stdout.write(self.style.SUCCESS(f'Success: {success_count}'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
            self.stdout.write('='*50)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Fatal error during sync: {str(e)}')
            )
            logger.exception("Fatal error during publication sync")
            raise
