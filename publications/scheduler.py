"""
Scheduler configuration for automated tasks.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)


def sync_external_publications_job():
    """
    Job to sync publications from external API.
    """
    try:
        logger.info("Starting scheduled publication sync...")
        
        from publications.services import ExternalJournalAPI, ExternalDataMapper
        
        api = ExternalJournalAPI()
        mapper = ExternalDataMapper()
        
        # Fetch all publications
        publications = api.fetch_all_publications()
        
        success_count = 0
        error_count = 0
        
        for pub_data in publications:
            try:
                publication = mapper.map_and_create_publication(pub_data)
                if publication:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing publication: {e}")
        
        logger.info(f"Scheduled sync completed. Success: {success_count}, Errors: {error_count}")
        
    except Exception as e:
        logger.exception(f"Error in scheduled publication sync: {e}")


@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    Delete old job execution records (older than max_age seconds, default 7 days).
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """
    Start the APScheduler for automated tasks.
    """
    if not getattr(settings, 'PUBLICATION_SYNC_ENABLED', True):
        logger.info("Publication sync is disabled in settings")
        return
    
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Schedule daily publication sync
    hour = getattr(settings, 'PUBLICATION_SYNC_SCHEDULE_HOUR', 2)
    minute = getattr(settings, 'PUBLICATION_SYNC_SCHEDULE_MINUTE', 0)
    
    scheduler.add_job(
        sync_external_publications_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="sync_external_publications",
        max_instances=1,
        replace_existing=True,
        name="Daily Publication Sync from External API",
    )
    logger.info(f"Scheduled publication sync daily at {hour:02d}:{minute:02d}")
    
    # Schedule cleanup of old job executions
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
        name="Cleanup old job executions weekly",
    )
    logger.info("Scheduled weekly cleanup of old job executions")
    
    try:
        scheduler.start()
        logger.info("APScheduler started successfully")
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")
