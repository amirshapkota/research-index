"""
Signals for automatic statistics updates.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Publication, Issue, JournalStats


@receiver(post_save, sender=Publication)
def update_journal_stats_on_publication_save(sender, instance, created, **kwargs):
    """
    Update journal statistics when a publication is saved.
    Only update if the publication is published and belongs to a journal.
    """
    if instance.journal and instance.is_published:
        # Get or create stats for this journal
        stats, stats_created = JournalStats.objects.get_or_create(journal=instance.journal)
        
        # Update stats
        stats.update_stats()


@receiver(post_delete, sender=Publication)
def update_journal_stats_on_publication_delete(sender, instance, **kwargs):
    """
    Update journal statistics when a publication is deleted.
    """
    if instance.journal:
        try:
            stats = JournalStats.objects.get(journal=instance.journal)
            stats.update_stats()
        except JournalStats.DoesNotExist:
            pass


@receiver(post_save, sender=Issue)
def update_journal_stats_on_issue_save(sender, instance, created, **kwargs):
    """
    Update journal statistics when an issue is saved.
    """
    if instance.journal:
        # Get or create stats for this journal
        stats, stats_created = JournalStats.objects.get_or_create(journal=instance.journal)
        
        # Update stats
        stats.update_stats()


@receiver(post_delete, sender=Issue)
def update_journal_stats_on_issue_delete(sender, instance, **kwargs):
    """
    Update journal statistics when an issue is deleted.
    """
    if instance.journal:
        try:
            stats = JournalStats.objects.get(journal=instance.journal)
            stats.update_stats()
        except JournalStats.DoesNotExist:
            pass
