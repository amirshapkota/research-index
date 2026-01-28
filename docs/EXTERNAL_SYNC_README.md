# External Publication Sync Integration

This module provides automatic synchronization of publications from an external journal management system API.

## Features

- **Automatic Data Mapping**: Transforms external API data to internal Research Index models
- **Journal Matching**: Intelligently matches or creates journals based on ISSN/title
- **Author Management**: Creates author profiles from external data
- **Issue Creation**: Automatically creates journal issues based on volume/issue numbers
- **Document Download**: Downloads and attaches PDF documents to publications
- **Scheduled Sync**: Daily automatic synchronization (configurable)
- **Manual Sync**: Management command for on-demand syncing

## Configuration

Add to your `.env` file or settings:

```env
# External API URL (default: http://localhost:8001)
EXTERNAL_JOURNAL_API_URL=http://localhost:8001

# Enable/disable automatic sync (default: True)
PUBLICATION_SYNC_ENABLED=True

# Schedule time for daily sync (default: 2:00 AM)
PUBLICATION_SYNC_SCHEDULE_HOUR=2
PUBLICATION_SYNC_SCHEDULE_MINUTE=0
```

## Installation

1. Install required packages:

```bash
pip install django-apscheduler requests
```

2. Run migrations:

```bash
python manage.py migrate
```

## Usage

### Manual Sync

Sync all publications:

```bash
python manage.py sync_external_publications --full-sync
```

Sync with limit (for testing):

```bash
python manage.py sync_external_publications --limit 10
```

Sync from custom API URL:

```bash
python manage.py sync_external_publications --api-url http://custom-api.com
```

### Automatic Sync

Automatic sync runs daily at the configured time (default 2:00 AM).

To disable automatic sync:

```env
PUBLICATION_SYNC_ENABLED=False
```

## Data Mapping

### External API → Internal Models

- **Journal**: Matched by ISSN or title, created if not found
- **Author**: Matched by name, created with inactive user account if not found
- **Issue**: Created based on volume + issue number
- **Publication**: Created with all metadata
- **Documents**: Downloaded and attached as PDF files

### Field Mapping

| External API                 | Internal Model                 | Notes                        |
| ---------------------------- | ------------------------------ | ---------------------------- |
| `title`                      | `Publication.title`            | Direct mapping               |
| `abstract`                   | `Publication.abstract`         | HTML stripped                |
| `doi`                        | `Publication.doi`              | Used for duplicate detection |
| `publication_details.year`   | `Publication.publication_year` |                              |
| `publication_details.volume` | `Publication.volume`           | Also creates Issue           |
| `publication_details.issue`  | `Publication.issue_number`     | Also creates Issue           |
| `publication_details.pages`  | `Publication.pages`            | Format: "121-124"            |
| `keywords[]`                 | `Publication.keywords`         | Joined with commas           |
| `corresponding_author`       | `Publication.author`           | Primary author               |
| `journal`                    | `Publication.journal`          | Matched/created              |
| `documents[].MANUSCRIPT`     | `Publication.pdf_file`         | Downloaded                   |

## Default Entities

For publications without matching journals/authors:

- **Default Institution**: "External Imports"
- **Default Author**: "Unknown Author"
- **System Users**: Created with email `system.{type}@researchindex.import` (inactive)

## Logging

All sync operations are logged. View logs:

```bash
# Check Django logs for sync activity
tail -f /path/to/django.log
```

## Scheduled Jobs

View scheduled jobs in Django admin:

- Admin → Django APScheduler → Jobs
- Admin → Django APScheduler → Job Executions

## API Endpoints

External API endpoints used:

- `GET /api/common/publications/` - List publications (paginated)
- `GET /api/v1/publications/documents/{uuid}/download/` - Download document

## Troubleshooting

### Sync not running automatically

1. Check if `PUBLICATION_SYNC_ENABLED=True` in settings
2. Verify scheduler started: Check logs for "APScheduler started successfully"
3. Ensure running with `python manage.py runserver` or gunicorn

### Publications not importing

1. Check external API is accessible
2. Review Django logs for specific errors
3. Test with manual sync: `python manage.py sync_external_publications --limit 1`

### Duplicate publications

Publications are matched by DOI if available. If DOI changes or is missing, duplicates may occur.

## Performance

- Fetches publications in pages (default 10 per page)
- Uses transaction batching for database operations
- Caches journals, authors, and issues during sync to reduce queries
- Downloads documents asynchronously

## Future Enhancements

- [ ] Incremental sync (only new publications since last sync)
- [ ] Webhook support for real-time updates
- [ ] Multi-author support (currently uses corresponding author only)
- [ ] Conflict resolution UI for duplicate detection
- [ ] Sync status dashboard
