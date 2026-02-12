"""
Management command to sync citation counts from Crossref API.

Usage:
    python manage.py sync_citations
    python manage.py sync_citations --limit 10
    python manage.py sync_citations --journal-id 5
    python manage.py sync_citations --force  # Re-sync even if recently updated
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from publications.models import Publication, PublicationStats
from publications.services import CrossrefCitationAPI
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync citation counts from Crossref API for publications with DOIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of publications to sync',
        )
        parser.add_argument(
            '--journal-id',
            type=int,
            default=None,
            help='Sync citations only for publications in a specific journal',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-sync even if recently updated (within 7 days)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between API requests in seconds (default: 0.1)',
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        journal_id = options.get('journal_id')
        force = options.get('force')
        delay = options.get('delay', 0.1)

        self.stdout.write(self.style.SUCCESS('Starting citation sync from Crossref...'))

        # Build query
        query = Publication.objects.filter(
            is_published=True,
            doi__isnull=False
        ).exclude(doi='').select_related('stats', 'journal')

        if journal_id:
            query = query.filter(journal_id=journal_id)
            self.stdout.write(f'Filtering by journal ID: {journal_id}')

        # Skip recently updated unless forced
        if not force:
            cutoff_date = timezone.now() - timedelta(days=7)
            query = query.exclude(stats__last_updated__gte=cutoff_date)
            self.stdout.write('Skipping publications updated in last 7 days (use --force to override)')

        if limit:
            query = query[:limit]
            self.stdout.write(f'Limiting to {limit} publications')

        publications = list(query)
        total = len(publications)

        if total == 0:
            self.stdout.write(self.style.WARNING('No publications found to sync'))
            return

        self.stdout.write(f'Found {total} publications with DOIs to sync')

        # Initialize Crossref API
        api = CrossrefCitationAPI()

        # Process publications
        success_count = 0
        error_count = 0
        updated_count = 0
        unchanged_count = 0

        for idx, publication in enumerate(publications, 1):
            title = publication.title[:60]
            doi = publication.doi

            self.stdout.write(f'\n[{idx}/{total}] {title}...')
            self.stdout.write(f'  DOI: {doi}')

            try:
                # Fetch citation count from Crossref
                citation_count = api.get_citation_count(doi)

                if citation_count is not None:
                    # Get or create stats
                    stats, created = PublicationStats.objects.get_or_create(
                        publication=publication
                    )

                    old_count = stats.citations_count

                    # Update citation count
                    stats.citations_count = citation_count
                    stats.save()

                    success_count += 1

                    if old_count != citation_count:
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Updated: {old_count} → {citation_count} citations'
                            )
                        )
                    else:
                        unchanged_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Unchanged: {citation_count} citations')
                        )

                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.WARNING('  ⚠ Could not fetch citation count')
                    )

                # Delay to respect rate limits
                if idx < total:
                    import time
                    time.sleep(delay)

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {str(e)}')
                )
                logger.exception(f"Error syncing citations for publication {publication.id}")

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\nCitation sync completed!'))
        self.stdout.write(f'Total processed: {total}')
        self.stdout.write(self.style.SUCCESS(f'Successfully fetched: {success_count}'))
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Citations updated: {updated_count}')
            )
        if unchanged_count > 0:
            self.stdout.write(f'Citations unchanged: {unchanged_count}')
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

        # Recommend recalculating journal stats
        self.stdout.write('\n' + self.style.WARNING(
            'Tip: Run "python manage.py recalculate_journal_stats" to update journal metrics'
        ))
