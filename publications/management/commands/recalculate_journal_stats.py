"""
Management command to recalculate statistics for all journals.
This is useful when:
- Stats data is outdated or incorrect
- After importing publications
- After data migrations
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from publications.models import Journal, JournalStats


class Command(BaseCommand):
    help = 'Recalculate statistics for all journals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--journal-id',
            type=int,
            help='Recalculate stats for a specific journal ID',
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create JournalStats for journals that don\'t have them',
        )

    def handle(self, *args, **options):
        journal_id = options.get('journal_id')
        create_missing = options.get('create_missing', False)

        if journal_id:
            # Recalculate for specific journal
            try:
                journal = Journal.objects.get(id=journal_id)
                self.recalculate_stats(journal)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully recalculated stats for journal: {journal.title}')
                )
            except Journal.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Journal with ID {journal_id} does not exist')
                )
        else:
            # Recalculate for all journals
            journals = Journal.objects.all()
            total_journals = journals.count()
            
            self.stdout.write(f'Recalculating stats for {total_journals} journals...')
            
            success_count = 0
            created_count = 0
            error_count = 0
            
            for journal in journals:
                try:
                    # Create stats if missing and --create-missing flag is set
                    stats, created = JournalStats.objects.get_or_create(journal=journal)
                    if created:
                        created_count += 1
                        if not create_missing:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Created missing stats for: {journal.title}'
                                )
                            )
                    
                    # Recalculate stats
                    stats.update_stats()
                    success_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {journal.title}: {stats.total_articles} articles, '
                            f'{stats.total_issues} issues, {stats.total_citations} citations'
                        )
                    )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error with {journal.title}: {str(e)}')
                    )
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nCompleted! Successfully recalculated: {success_count}/{total_journals}'
                )
            )
            if created_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'Created new stats records: {created_count}')
                )
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'Errors encountered: {error_count}')
                )

    def recalculate_stats(self, journal):
        """Helper method to recalculate stats for a single journal."""
        stats, created = JournalStats.objects.get_or_create(journal=journal)
        stats.update_stats()
        return stats
