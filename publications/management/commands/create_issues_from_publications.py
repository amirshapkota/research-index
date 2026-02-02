"""
Management command to create Issue objects from existing Publications.
Useful when publications have volume/issue data but Issues weren't created.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from publications.models import Publication, Journal, Issue, IssueArticle


class Command(BaseCommand):
    help = 'Create Issue objects and IssueArticle links from existing Publications with volume/issue data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--journal-id',
            type=int,
            help='Only process publications for specific journal ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        journal_id = options.get('journal_id')
        dry_run = options.get('dry_run', False)

        # Get publications with volume/issue data
        publications = Publication.objects.exclude(volume='').exclude(issue='')
        
        if journal_id:
            publications = publications.filter(journal_id=journal_id)

        total_pubs = publications.count()
        self.stdout.write(self.style.WARNING(
            f"\nFound {total_pubs} publications with volume/issue data"
        ))

        if total_pubs == 0:
            self.stdout.write(self.style.ERROR(
                "\nNo publications found with volume/issue data."
            ))
            self.stdout.write(
                "Publications need non-empty 'volume' and 'issue' fields to create Issues."
            )
            return

        # Group by journal, volume, issue
        issues_to_create = {}
        articles_to_create = []

        for pub in publications:
            journal = pub.journal
            volume = pub.volume.strip()
            issue_num = pub.issue.strip()

            if not volume or not issue_num:
                continue

            # Convert to int if possible
            try:
                volume_int = int(volume)
                issue_int = int(issue_num)
            except ValueError:
                self.stdout.write(self.style.WARNING(
                    f"Skipping publication {pub.id}: volume='{volume}', issue='{issue_num}' (not numeric)"
                ))
                continue

            key = (journal.id, volume_int, issue_int)
            
            if key not in issues_to_create:
                issues_to_create[key] = {
                    'journal': journal,
                    'volume': volume_int,
                    'issue_number': issue_int,
                    'publications': []
                }
            
            issues_to_create[key]['publications'].append(pub)

        self.stdout.write(self.style.WARNING(
            f"\nWill create {len(issues_to_create)} Issue objects"
        ))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n--- DRY RUN MODE ---"))
            for key, data in issues_to_create.items():
                journal_id, volume, issue_num = key
                self.stdout.write(
                    f"\nIssue: {data['journal'].title} - Vol. {volume}, Issue {issue_num}"
                )
                self.stdout.write(f"  Articles: {len(data['publications'])}")
                for pub in data['publications'][:3]:
                    self.stdout.write(f"    - {pub.title[:60]}...")
                if len(data['publications']) > 3:
                    self.stdout.write(f"    ... and {len(data['publications']) - 3} more")
            
            self.stdout.write(self.style.SUCCESS(
                f"\nDRY RUN: Would create {len(issues_to_create)} issues"
            ))
            return

        # Actually create issues and links
        created_issues = 0
        created_links = 0

        with transaction.atomic():
            for key, data in issues_to_create.items():
                journal = data['journal']
                volume = data['volume']
                issue_num = data['issue_number']

                # Check if issue already exists
                issue, created = Issue.objects.get_or_create(
                    journal=journal,
                    volume=volume,
                    issue_number=issue_num,
                    defaults={
                        'title': f"Volume {volume}, Issue {issue_num}",
                        'publication_date': data['publications'][0].published_date or journal.created_at.date(),
                        'status': 'published',
                    }
                )

                if created:
                    created_issues += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Created: {issue}"
                    ))

                # Create IssueArticle links
                for pub in data['publications']:
                    link, link_created = IssueArticle.objects.get_or_create(
                        issue=issue,
                        publication=pub
                    )
                    if link_created:
                        created_links += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Created {created_issues} Issue objects"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✓ Created {created_links} IssueArticle links"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Now test the volumes endpoint."
        ))
