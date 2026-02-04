"""
Management command to update citation counts from Crossref
"""

from django.core.management.base import BaseCommand
from common.utils.crossref_utils import update_citation_counts


class Command(BaseCommand):
    help = 'Update citation counts for all publications from Crossref API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting citation count update...'))
        
        updated_count = update_citation_counts()
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully updated {updated_count} publications')
        )
