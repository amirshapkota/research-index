# NepJOL Publication Scraper Implementation

## Overview

This implementation allows you to scrape and import publications from Nepal Journals Online (https://nepjol.info/) into your Research Index application.

## Components Created

### 1. NepJOL Scraper Service

**File**: `researchindex/common/services/nepjol_scraper.py`

A comprehensive web scraping service that extracts publication data from NepJOL.

**Features:**

- Rate limiting (1 second delay between requests)
- Session management with persistent connections
- Comprehensive error handling and logging
- Extracts complete publication metadata

**Key Methods:**

- `get_all_journals()`: Fetches list of all 566 journals
- `get_journal_issues(journal_url)`: Gets all issues for a journal
- `get_articles_from_issue(issue_url)`: Extracts article summaries from an issue
- `get_article_details(article_url)`: Scrapes full article metadata (abstract, keywords, references)
- `scrape_journal_complete(journal_url, max_issues)`: Complete pipeline to scrape a journal
- `search_articles(query, max_results)`: Search functionality

**Data Extracted:**

```python
{
    'title': str,
    'url': str,
    'authors': [{'name': str, 'affiliation': str}],
    'abstract': str,
    'keywords': [str],
    'doi': str,
    'pdf_url': str,
    'volume': str,
    'issue': str,
    'year': str,
    'pages': str,
    'references': [str]
}
```

### 2. Django Management Command

**File**: `researchindex/common/management/commands/import_nepjol.py`

A Django management command to orchestrate the scraping and importing process.

**Usage:**

```bash
# Import all journals and all articles
python manage.py import_nepjol

# Import only first 5 journals
python manage.py import_nepjol --journals=5

# Limit to 100 articles per journal
python manage.py import_nepjol --max-articles=100

# Test mode: scrape 1 journal, 1 issue only
python manage.py import_nepjol --test

# Skip publications that already exist (default behavior)
python manage.py import_nepjol --skip-duplicates
```

### 3. REST API Endpoints

**File**: `researchindex/common/views_nepjol.py`

REST API endpoints for programmatic access to NepJOL import functionality with real-time status tracking.

**Base URL**: `/api/v1/common/nepjol/`

#### Endpoints

**1. Get Available Journals**

```http
GET /api/v1/common/nepjol/journals/
Authorization: Bearer <token>
```

Returns list of all journals available on NepJOL without importing them.

**Response**: 200 OK

```json
{
  "count": 567,
  "journals": [
    {
      "title": "Aadim Journal of Multidisciplinary Research",
      "url": "https://nepjol.info/index.php/ajmr"
    }
  ]
}
```

**2. Start Import**

```http
POST /api/v1/common/nepjol/import/start/
Authorization: Bearer <token>
Content-Type: application/json

{
  "test_mode": false,
  "max_journals": null,
  "max_articles_per_journal": null,
  "download_pdfs": false
}
```

Starts a background import process and returns immediately.

**Response**: 200 OK

```json
{
  "status": "started",
  "message": "Import started in background"
}
```

**3. Get Import Status**

```http
GET /api/v1/common/nepjol/import/status/
Authorization: Bearer <token>
```

Returns real-time status of the current or last import operation.

**Response**: 200 OK

```json
{
  "is_running": true,
  "current_journal": "Asian Journal of Medical Sciences",
  "current_issue": "Vol 16, No 1 (2025)",
  "current_article": "Impact of COVID-19 on Healthcare",
  "progress": {
    "journals_processed": 5,
    "total_journals": 567,
    "percentage": 0.88,
    "estimated_time_remaining": "15h 30m"
  },
  "statistics": {
    "journals_created": 5,
    "issues_created": 23,
    "authors_created": 145,
    "publications_created": 234,
    "publications_skipped": 12,
    "pdfs_downloaded": 0,
    "errors": 2
  },
  "started_at": "2026-02-05T10:30:00Z",
  "last_updated": "2026-02-05T10:45:00Z"
}
```

**4. Stop Import**

```http
POST /api/v1/common/nepjol/import/stop/
Authorization: Bearer <token>
```

Stops the currently running import process.

**Response**: 200 OK

```json
{
  "status": "stopped",
  "message": "Import stopped successfully"
}
```

**5. Get Import History**

```http
GET /api/v1/common/nepjol/import/history/
Authorization: Bearer <token>
```

Returns database totals and last import statistics.

**Response**: 200 OK

```json
{
  "database_totals": {
    "total_journals": 7,
    "total_issues": 4,
    "total_publications": 37
  },
  "last_import": {
    "journals_created": 5,
    "publications_created": 234,
    "completed_at": "2026-02-05T12:30:00Z"
  }
}
```

#### Authentication

All endpoints require authentication:

- `IsAuthenticated`: Regular users can view journals, status, and history
- `IsAdminUser`: Only admins can start/stop imports

#### Usage Example

```bash
# 1. Get authentication token
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# 2. Start import in test mode
curl -X POST http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'

# 3. Monitor progress
while true; do
  curl -X GET http://localhost:8000/api/v1/common/nepjol/import/status/ \
    -H "Authorization: Bearer <token>"
  sleep 5
done
```

#### Features

- **Background Processing**: Import runs in separate thread, API responds immediately
- **Real-time Status**: Monitor current journal/issue/article being processed
- **Progress Tracking**: Percentage complete and estimated time remaining
- **Statistics**: Track journals, issues, authors, publications, PDFs, and errors
- **Flexible Options**: Configure test mode, limits, PDF downloads
- **Concurrent Import Prevention**: Only one import can run at a time
- **OpenAPI/Swagger**: Full documentation at `/api/schema/swagger-ui/`

#### Documentation

For complete API reference, see:

- [docs/NEPJOL_API.md](NEPJOL_API.md) - Full API documentation
- [NEPJOL_API_IMPLEMENTATION.md](../NEPJOL_API_IMPLEMENTATION.md) - Implementation details
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/` (look for "NepJOL Import" tag)

**Features:**

- **Automatic Institution Creation**: Creates "External Imports" institution for all scraped content
- **System Author**: Creates a system author account for imported publications
- **Duplicate Detection**: Checks for existing publications by DOI before creating
- **Progress Tracking**: Shows real-time progress with statistics
- **Error Handling**: Continues processing even if individual journals/articles fail
- **Transaction Safety**: Uses database transactions to prevent partial imports

**Process Flow:**

1. Creates "External Imports" institution if it doesn't exist
2. Creates system author for imported publications
3. Fetches list of all journals from NepJOL
4. For each journal:
   - Creates/finds journal in database
   - Scrapes all issues and articles
   - For each article:
     - Checks if DOI already exists (skip if duplicate)
     - Creates Publication record
     - Creates Reference records
     - Links to journal and system author
5. Prints final statistics

**Statistics Tracked:**

- Journals processed
- Journals created (new)
- Publications created (new)
- Publications skipped (duplicates)
- Errors encountered

## Installation and Setup

### Prerequisites

```bash
# Beautiful Soup 4 for HTML parsing (already added to requirements.txt)
pip install beautifulsoup4==4.12.3
```

### Database Models Used

- `Institution`: For "External Imports" institution
- `CustomUser`: For system accounts
- `Author`: System author for imported publications
- `Journal`: For NepJOL journals
- `Publication`: For scraped articles
- `Reference`: For reference lists

## Testing

### REST API Testing

See [docs/NEPJOL_API.md](NEPJOL_API.md) for complete API testing instructions.

**Quick API Test**:

```bash
# Run all API endpoint tests
python test_nepjol_endpoints.py

# Or test with HTTP requests
python test_nepjol_api.py
```

### Management Command Testing

**Quick Test (1 Journal, 1 Issue)**:

```bash
python manage.py import_nepjol --test
```

Expected output:

```
Starting NepJOL import...
Created system author for imports
Fetching journals list from NepJOL...
Found 566 journals on NepJOL
TEST MODE: Processing only 1 journal

[1/1] Processing: Asian Journal of Medical Sciences
  ✓ Created journal: Asian Journal of Medical Sciences
  Found 25 articles
  ✓ Imported 25 new articles

============================================================
Import completed!
============================================================
Journals processed:       1
Journals created:         1
Publications created:     25
Publications skipped:     0
Errors:                   0
============================================================
```

### Small Batch Test (5 Journals)

```bash
python manage.py import_nepjol --journals=5 --max-articles=10
```

### Full Import (All 566 Journals, ~55,127 Articles)

```bash
# WARNING: This will take 15-20 hours due to rate limiting
python manage.py import_nepjol
```

**Estimated time**: With 1 second delay and ~55,000 articles:

- Time = 55,000 articles × 1 second = ~15 hours
- Plus overhead for parsing and database operations
- **Total: 15-20 hours**

## Data Mapping

### NepJOL → Publication Model

| NepJOL Field | Publication Field | Notes                                 |
| ------------ | ----------------- | ------------------------------------- |
| title        | title             | Truncated to 500 chars                |
| abstract     | abstract          | Truncated to 10,000 chars             |
| doi          | doi               | Truncated to 255 chars                |
| year         | published_date    | Converted to January 1st of that year |
| volume       | volume            | Truncated to 50 chars                 |
| issue        | issue             | Truncated to 50 chars                 |
| pages        | pages             | Truncated to 50 chars                 |
| authors      | co_authors        | Comma-separated string                |
| -            | author            | FK to system author                   |
| -            | journal           | FK to auto-created journal            |
| -            | publication_type  | 'journal_article'                     |
| -            | is_published      | True                                  |

### NepJOL → Journal Model

| NepJOL Field | Journal Field  | Notes                         |
| ------------ | -------------- | ----------------------------- |
| Journal name | title          | Truncated to 300 chars        |
| Journal URL  | website        | Direct link to NepJOL         |
| -            | institution    | FK to "External Imports"      |
| -            | publisher_name | 'NepJOL'                      |
| -            | is_open_access | True                          |
| -            | description    | "Imported from NepJOL: {url}" |

### References

Each reference string from NepJOL creates a `Reference` record:

- `reference_text`: Full citation string
- `order`: Position in reference list (1, 2, 3...)
- `publication`: FK to parent publication

## Architecture Decisions

### Why System Author?

- Publications in NepJOL may have authors not registered in your system
- Creating a system author avoids foreign key constraint issues
- Allows you to import data first, then match/claim publications later
- Real authors can later "claim" their publications

### Why "External Imports" Institution?

- Establishes a clear pattern for scraped/imported content
- Easy to filter or identify imported data
- Can be migrated to real institutions later
- Maintains referential integrity

### Duplicate Detection

- Uses DOI as unique identifier (case-insensitive)
- Skips publications that already exist
- Prevents redundant imports if command is run multiple times
- Optional: can be disabled with `--skip-duplicates=False`

## Troubleshooting

### Network Timeout

If you encounter timeout errors:

```python
# In nepjol_scraper.py, increase timeout:
response = self.session.get(url, timeout=60)  # Changed from 30 to 60
```

### HTML Structure Changes

If NepJOL updates their website structure:

1. Run the test script to inspect HTML:
   ```bash
   python test_scraper.py
   ```
2. Update selectors in `nepjol_scraper.py`:
   - Look for `soup.find_all('div', class_='journal')`
   - Update class names or HTML tags as needed

### Database Errors

- **Max length exceeded**: Check field truncation in `import_article()` method
- **Foreign key errors**: Ensure "External Imports" institution and system author exist
- **Duplicate key errors**: Check DOI uniqueness, ensure skip_duplicates is working

### Performance Issues

- **Too slow**: Reduce delay in scraper (but be respectful to server)
- **Memory errors**: Process in smaller batches using `--journals` and `--max-articles`
- **Database locks**: Use lower concurrency or increase connection pool

## Monitoring Progress

### View Logs

```bash
# In Django shell
python manage.py shell

from publications.models import Publication
from users.models import Author

# Count imported publications
system_author = Author.objects.get(full_name='NepJOL Import System')
print(f"Total imported: {system_author.publications.count()}")

# Count by journal
from publications.models import Journal
for journal in Journal.objects.filter(publisher_name='NepJOL'):
    count = journal.journal_publications.count()
    print(f"{journal.title}: {count} articles")
```

### Statistics

```python
from publications.models import Publication, Journal
from users.models import Institution

# Total NepJOL content
institution = Institution.objects.get(institution_name='External Imports')
nepjol_journals = institution.journals.filter(publisher_name='NepJOL')
print(f"Journals: {nepjol_journals.count()}")

nepjol_publications = Publication.objects.filter(journal__publisher_name='NepJOL')
print(f"Publications: {nepjol_publications.count()}")

# Publications with references
with_refs = nepjol_publications.filter(references__isnull=False).distinct()
print(f"With references: {with_refs.count()}")
```

## Next Steps

### After Import

1. **Data Quality Check**
   - Review imported publications for accuracy
   - Check for missing abstracts or metadata
   - Verify DOI links are valid

2. **Author Matching**
   - Create a system to match co_authors strings with registered Author accounts
   - Allow authors to "claim" their imported publications
   - Transfer ownership from system author to real authors

3. **Journal Enhancement**
   - Add ISSN numbers to journals (can scrape from NepJOL or Crossref)
   - Add journal cover images
   - Populate editorial board information

4. **Citation Network**
   - Use DOIs to link references to existing publications
   - Build citation graph
   - Calculate impact metrics

5. **Incremental Updates**
   - Schedule periodic imports to get new publications
   - Use `--skip-duplicates` to only import new content
   - Track last import date per journal

## Performance Optimization

### For Large Imports

```python
# Use bulk_create for better performance
publications_to_create = []
for article in articles:
    pub = Publication(
        author=system_author,
        title=article['title'],
        # ... other fields
    )
    publications_to_create.append(pub)

# Create in batches
Publication.objects.bulk_create(publications_to_create, batch_size=100)
```

### Database Indexing

Ensure these indexes exist:

- `Publication.doi` (already indexed)
- `Publication.journal` (foreign key auto-indexed)
- `Journal.title` (consider adding index)
- `Journal.publisher_name` (consider adding index)

## Legal & Ethical Considerations

1. **Respect Rate Limits**: 1 second delay is reasonable, don't reduce below 0.5s
2. **Terms of Service**: Ensure scraping complies with NepJOL's terms
3. **Attribution**: Always credit NepJOL as data source
4. **Copyright**: Only scrape metadata, not full-text PDFs (without permission)
5. **Data Updates**: Keep scraped data in sync with source
6. **Robots.txt**: Check https://nepjol.info/robots.txt before scraping

## Summary

You now have a complete system to import Nepal's research publications from NepJOL. The implementation is:

- ✅ **Complete**: All scraping and importing logic implemented
- ✅ **Robust**: Comprehensive error handling and logging
- ✅ **Scalable**: Can handle all 55,127 articles
- ✅ **Safe**: Duplicate detection and transaction safety
- ✅ **Configurable**: Multiple command-line options and API parameters
- ✅ **Monitored**: Real-time progress and statistics via API
- ✅ **API-Enabled**: Full REST API with 5 endpoints for programmatic access
- ✅ **Production-Ready**: Background processing, authentication, OpenAPI documentation

### Getting Started

**Option 1: REST API (Recommended)**

```bash
# Start Django server
python manage.py runserver

# Access Swagger UI
http://localhost:8000/api/schema/swagger-ui/

# Or use curl/HTTP client
curl -X POST http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'
```

**Option 2: Management Command**

```bash
python manage.py import_nepjol --test
```

For complete API documentation, see [docs/NEPJOL_API.md](NEPJOL_API.md).
