# External Publication Sync - Quick Setup Guide

## Installation Steps

### 1. Install Dependencies

```bash
cd researchindex
pip install django-apscheduler requests
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

This will create the necessary database tables for APScheduler.

### 3. Configure Settings

Add to your `.env` file (or use defaults):

```env
# External Journal API URL
EXTERNAL_JOURNAL_API_URL=http://localhost:8001

# Enable automatic daily sync
PUBLICATION_SYNC_ENABLED=True

# Schedule time (24-hour format)
PUBLICATION_SYNC_SCHEDULE_HOUR=2
PUBLICATION_SYNC_SCHEDULE_MINUTE=0
```

### 4. Test Manual Sync

Test with a small batch first:

```bash
python manage.py sync_external_publications --limit 5
```

Expected output:

```
Starting publication sync...
Fetching publications (limit: 5)...
Found 5 publications to sync
[1/5] Processing: test...
  ✓ Synced: test
[2/5] Processing: Main Test...
  ✓ Synced: Main Test
...
==================================================
Sync completed!
Total processed: 5
Success: 5
Errors: 0
==================================================
```

### 5. Run Full Sync

Once tested, run a full sync:

```bash
python manage.py sync_external_publications --full-sync
```

This will fetch all publications from the external API.

### 6. Start Server with Auto-Sync

```bash
python manage.py runserver
```

The scheduler will start automatically and sync publications daily at the configured time.

## Verification

### Check Synced Publications

```bash
python manage.py shell
```

```python
from publications.models import Publication
print(f"Total publications: {Publication.objects.count()}")
print(f"Published: {Publication.objects.filter(is_published=True).count()}")

# Show recent synced publications
recent = Publication.objects.order_by('-created_at')[:5]
for pub in recent:
    print(f"- {pub.title} ({pub.publication_year})")
```

### Check Scheduled Jobs

Go to Django Admin:

1. Login to http://localhost:8000/admin/
2. Navigate to: Django APScheduler → Jobs
3. You should see: "Daily Publication Sync from External API"

### Monitor Sync Logs

Check terminal output when server is running. You'll see:

```
APScheduler started successfully
Scheduled publication sync daily at 02:00
```

## Troubleshooting

### External API Not Reachable

Ensure your external journal system is running:

```bash
# Check if accessible
curl http://localhost:8001/api/common/publications/
```

### No Jobs Appearing

1. Check migrations ran: `python manage.py migrate`
2. Check `PUBLICATION_SYNC_ENABLED=True` in settings
3. Restart server: `python manage.py runserver`

### Sync Errors

Check logs for specific errors:

```bash
python manage.py sync_external_publications --limit 1
```

Review the output for error messages.

## Data Flow

```
External API (Port 8001)
    ↓
ExternalJournalAPI.fetch_publications()
    ↓
ExternalDataMapper.map_and_create_publication()
    ↓
Internal Models (Port 8000)
    - Journal
    - Author
    - Issue
    - Publication
    - PDF Documents
```

## Sync Frequency

- **Default**: Once per day at 2:00 AM
- **Customizable**: Set `PUBLICATION_SYNC_SCHEDULE_HOUR` and `PUBLICATION_SYNC_SCHEDULE_MINUTE`
- **Manual**: Run anytime with management command

## Next Steps

1. Monitor first automatic sync (wait until scheduled time or trigger manually)
2. Verify publications appear in admin and API endpoints
3. Check journal matching is working correctly
4. Review any error logs and adjust mapping if needed
5. Set up monitoring/alerting for failed syncs (optional)

## Support

- Full documentation: See `EXTERNAL_SYNC_README.md`
- Management command help: `python manage.py sync_external_publications --help`
- Check logs for detailed error messages
