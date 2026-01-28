from django.apps import AppConfig


class PublicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'publications'
    
    def ready(self):
        """
        Initialize the app and start scheduled tasks.
        """
        import sys
        
        # Only start scheduler if running the server (not during migrations, etc.)
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            try:
                from publications.scheduler import start_scheduler
                start_scheduler()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not start scheduler: {e}")
