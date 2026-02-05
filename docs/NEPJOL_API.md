# NepJOL Import API Documentation

## Overview

API endpoints for importing journals and publications from NepJOL (Nepal Journals Online) with real-time status tracking.

## Base URL

```
/api/v1/common/nepjol/
```

## Authentication

All endpoints require authentication. Admin endpoints require admin/superuser privileges.

## Endpoints

### 1. Get Available Journals

Fetch list of all journals available on NepJOL without importing.

**Endpoint:** `GET /nepjol/journals/`  
**Authentication:** Required  
**Permissions:** Any authenticated user

**Response:**

```json
{
  "total": 567,
  "journals": [
    {
      "name": "Journal of Institute of Engineering",
      "url": "https://nepjol.info/index.php/jie",
      "short_name": "jie"
    }
  ]
}
```

**Example:**

```bash
curl -X GET \
  http://localhost:8000/api/v1/common/nepjol/journals/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. Start Import

Start importing journals and publications from NepJOL.

**Endpoint:** `POST /nepjol/import/start/`  
**Authentication:** Required  
**Permissions:** Admin only

**Request Body:**

```json
{
  "max_journals": 5, // Optional: limit number of journals (null for all)
  "max_articles_per_journal": 10, // Optional: limit articles per journal
  "skip_duplicates": true, // Skip existing publications (default: true)
  "download_pdfs": true, // Download PDF files (default: true)
  "test_mode": false // Test mode: 1 journal, 1 issue (default: false)
}
```

**Response:**

```json
{
  "message": "NepJOL import started successfully",
  "status": "running",
  "started_at": "2026-02-05T10:30:00Z"
}
```

**Examples:**

1. **Test Import (1 journal, 1 issue):**

```bash
curl -X POST \
  http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_mode": true,
    "download_pdfs": true
  }'
```

2. **Limited Import (5 journals):**

```bash
curl -X POST \
  http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_journals": 5,
    "max_articles_per_journal": 10,
    "download_pdfs": false
  }'
```

3. **Full Import (all journals):**

```bash
curl -X POST \
  http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skip_duplicates": true,
    "download_pdfs": true
  }'
```

---

### 3. Get Import Status

Get real-time status of ongoing or last import operation.

**Endpoint:** `GET /nepjol/import/status/`  
**Authentication:** Required  
**Permissions:** Any authenticated user

**Response:**

```json
{
  "is_running": true,
  "started_at": "2026-02-05T10:30:00Z",
  "current_journal": "Journal of Institute of Engineering",
  "current_journal_index": 3,
  "total_journals": 567,
  "current_issue": "Vol. 10, No. 1 (2025)",
  "current_article": "Machine Learning Applications in Healthcare",
  "progress_percentage": 45.5,
  "stats": {
    "journals_processed": 3,
    "journals_created": 2,
    "issues_created": 8,
    "authors_created": 45,
    "authors_matched": 12,
    "publications_created": 67,
    "publications_skipped": 5,
    "pdfs_downloaded": 62,
    "errors": 3
  },
  "last_update": "2026-02-05T10:35:22Z",
  "estimated_time_remaining": "2:15:30"
}
```

**Example:**

```bash
curl -X GET \
  http://localhost:8000/api/v1/common/nepjol/import/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Status Fields:**

- `is_running`: Whether import is currently active
- `current_journal`: Name of journal being processed
- `current_issue`: Current issue being processed
- `current_article`: Current article being imported
- `progress_percentage`: Overall progress (0-100)
- `estimated_time_remaining`: Estimated time to completion (HH:MM:SS)

**Stats Fields:**

- `journals_processed`: Total journals processed
- `journals_created`: New journals created
- `issues_created`: New issues created
- `authors_created`: New authors created
- `authors_matched`: Existing authors matched
- `publications_created`: New publications imported
- `publications_skipped`: Duplicate publications skipped
- `pdfs_downloaded`: PDF files downloaded
- `errors`: Number of errors encountered

---

### 4. Stop Import

Stop the currently running import operation.

**Endpoint:** `POST /nepjol/import/stop/`  
**Authentication:** Required  
**Permissions:** Admin only

**Response:**

```json
{
  "message": "Import stopped successfully",
  "stats": {
    "journals_processed": 3,
    "publications_created": 67,
    ...
  }
}
```

**Example:**

```bash
curl -X POST \
  http://localhost:8000/api/v1/common/nepjol/import/stop/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 5. Get Import History

Get history of import operations and database totals.

**Endpoint:** `GET /nepjol/import/history/`  
**Authentication:** Required  
**Permissions:** Any authenticated user

**Response:**

```json
{
  "total_journals": 15,
  "total_issues": 45,
  "total_publications": 523,
  "last_import": {
    "started_at": "2026-02-05T10:30:00Z",
    "is_running": false,
    "stats": {
      "journals_created": 5,
      "publications_created": 150,
      ...
    }
  }
}
```

**Example:**

```bash
curl -X GET \
  http://localhost:8000/api/v1/common/nepjol/import/history/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Workflow Example

### 1. Check Available Journals

```bash
# Get list of journals available for import
curl -X GET http://localhost:8000/api/v1/common/nepjol/journals/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Start Test Import

```bash
# Start with test mode (1 journal, 1 issue)
curl -X POST http://localhost:8000/api/v1/common/nepjol/import/start/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'
```

### 3. Monitor Progress

```bash
# Poll status every few seconds
while true; do
  curl -X GET http://localhost:8000/api/v1/common/nepjol/import/status/ \
    -H "Authorization: Bearer YOUR_TOKEN"
  sleep 5
done
```

### 4. Check Results

```bash
# View import history and totals
curl -X GET http://localhost:8000/api/v1/common/nepjol/import/history/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Responses

### 400 Bad Request

Import already running:

```json
{
  "error": "Import is already running. Please wait for it to complete."
}
```

No import running (when trying to stop):

```json
{
  "error": "No import is currently running"
}
```

### 401 Unauthorized

Missing or invalid authentication token:

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

Insufficient permissions (admin required):

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 500 Internal Server Error

Failed to fetch journals:

```json
{
  "error": "Failed to fetch journals: Connection timeout"
}
```

---

## Implementation Details

### Background Processing

- Import runs in a background thread to avoid blocking the API
- Status is stored in Django cache (Redis recommended for production)
- Cache timeout: 24 hours

### What Gets Imported

For each journal:

1. **Journal Details**
   - Title, description, ISSN
   - Cover image
   - Publisher information

2. **Issues**
   - Volume and issue numbers
   - Publication dates
   - Issue metadata

3. **Publications**
   - Full article metadata
   - Authors with ORCID matching
   - PDF downloads (optional)
   - References
   - Keywords

4. **Relationships**
   - Journal → Issue → IssueArticle → Publication
   - Publication → Author (with ORCID matching)
   - Publication → References

### Performance Considerations

- Rate limiting: 1 second delay between requests to NepJOL
- Estimated time for full import: ~8-12 hours (567 journals)
- Network timeouts may occur - import will continue with errors logged
- PDF downloads can significantly increase import time

---

## Testing with Python

See `test_nepjol_api.py` for complete test suite.

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/common"
TOKEN = "your_token_here"

# Start test import
response = requests.post(
    f"{BASE_URL}/nepjol/import/start/",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"test_mode": True}
)

# Monitor progress
while True:
    status = requests.get(
        f"{BASE_URL}/nepjol/import/status/",
        headers={"Authorization": f"Bearer {TOKEN}"}
    ).json()

    if not status['is_running']:
        break

    print(f"Progress: {status['progress_percentage']:.1f}%")
    time.sleep(5)
```

---

## Swagger/OpenAPI Documentation

All endpoints are documented in the Swagger UI:

```
http://localhost:8000/api/schema/swagger-ui/
```

Look for the "NepJOL Import" tag in the API documentation.
