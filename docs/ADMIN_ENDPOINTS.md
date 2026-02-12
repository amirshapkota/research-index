# Admin API Endpoints

This document describes admin-only API endpoints for managing citations and journal statistics.

## Authentication

All admin endpoints require:

- User must be authenticated
- User must have `is_staff=True` (admin user)

Include the authentication token in the request header:

```
Authorization: Bearer <your-token>
```

## Endpoints

### 1. Sync Citations from Crossref

**Endpoint:** `POST /api/publications/admin/sync-citations/`

**Description:** Fetches citation counts from Crossref API for publications with DOIs and updates the `PublicationStats.citations_count` field.

**Query Parameters:**

- `limit` (integer, optional): Limit number of publications to sync
- `journal_id` (integer, optional): Sync citations only for publications in a specific journal
- `force` (boolean, optional): Force re-sync even if recently updated (within 7 days). Default: `false`
- `delay` (float, optional): Delay between API requests in seconds. Default: `0.1`

**Example Requests:**

```bash
# Sync citations for all publications (respects 7-day cooldown)
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/" \
  -H "Authorization: Bearer <token>"

# Sync citations for specific journal
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?journal_id=5" \
  -H "Authorization: Bearer <token>"

# Sync limited number of publications
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?limit=10" \
  -H "Authorization: Bearer <token>"

# Force re-sync even for recently updated publications
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?force=true" \
  -H "Authorization: Bearer <token>"

# Custom rate limiting (slower)
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?limit=50&delay=0.5" \
  -H "Authorization: Bearer <token>"
```

**Response Example:**

```json
{
  "message": "Citation sync completed",
  "total_processed": 25,
  "success_count": 23,
  "updated_count": 15,
  "unchanged_count": 8,
  "error_count": 2,
  "details": [
    {
      "id": 123,
      "title": "Machine Learning Applications in Healthcare Research",
      "doi": "10.1234/example.2024.001",
      "old_citations": 45,
      "new_citations": 52,
      "status": "updated"
    },
    {
      "id": 124,
      "title": "Climate Change Impact on Agricultural Practices",
      "doi": "10.1234/example.2024.002",
      "citations": 18,
      "status": "unchanged"
    },
    {
      "id": 125,
      "title": "Novel Approaches to Quantum Computing",
      "doi": "10.3126/invalid.doi",
      "status": "error",
      "error": "DOI not found in Crossref"
    }
  ],
  "tip": "Run recalculate-stats endpoint to update journal metrics based on new citation data"
}
```

**Notes:**

- Only processes publications that are published (`is_published=True`) and have DOIs
- By default, skips publications that were synced within the last 7 days (use `force=true` to override)
- Automatically adds delay between API requests to respect Crossref rate limits
- NEPJOL DOIs (10.3126/\*) may not be found in Crossref as they use a different registration agency

---

### 2. Recalculate Journal Statistics

**Endpoint:** `POST /api/publications/admin/recalculate-stats/`

**Description:** Recalculates all journal statistics including h-index, impact factor, cite score, total citations, reads, and other metrics based on current publications data.

**Query Parameters:**

- `journal_id` (integer, optional): Recalculate stats for a specific journal ID
- `create_missing` (boolean, optional): Create JournalStats for journals that don't have them. Default: `true`

**Example Requests:**

```bash
# Recalculate stats for all journals
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/" \
  -H "Authorization: Bearer <token>"

# Recalculate stats for specific journal
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/?journal_id=5" \
  -H "Authorization: Bearer <token>"

# Recalculate without creating missing stats records
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/?create_missing=false" \
  -H "Authorization: Bearer <token>"
```

**Response Example (Single Journal):**

```json
{
  "message": "Successfully recalculated stats for journal: Journal of Research and Innovation",
  "journal": {
    "id": 5,
    "title": "Journal of Research and Innovation",
    "total_articles": 127,
    "total_issues": 12,
    "total_citations": 1453,
    "impact_factor": "2.34",
    "cite_score": "1.89",
    "h_index": 15
  },
  "created": false
}
```

**Response Example (All Journals):**

```json
{
  "message": "Stats recalculation completed",
  "total_journals": 10,
  "success_count": 10,
  "created_count": 2,
  "error_count": 0,
  "details": [
    {
      "id": 1,
      "title": "Journal of Nepal Health Research Council",
      "total_articles": 10,
      "total_issues": 0,
      "total_citations": 0,
      "impact_factor": null,
      "cite_score": null,
      "h_index": 0,
      "created": false
    },
    {
      "id": 5,
      "title": "Journal of Research and Innovation",
      "total_articles": 127,
      "total_issues": 12,
      "total_citations": 1453,
      "impact_factor": "2.34",
      "cite_score": "1.89",
      "h_index": 15,
      "created": false
    }
  ]
}
```

**Calculated Metrics:**

- **Impact Factor**: Average citations for articles published in the last 2 years
- **Cite Score**: Average citations across all published articles
- **H-Index**: Journal has h-index h if h articles have ≥h citations each
- **Total Citations**: Sum of all citation counts
- **Total Articles**: Count of published articles
- **Total Issues**: Count of published issues

---

## Workflow Example

To fully update citation data and journal statistics:

```bash
# Step 1: Sync citations from Crossref
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/" \
  -H "Authorization: Bearer <token>"

# Step 2: Recalculate journal statistics based on new citation data
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/" \
  -H "Authorization: Bearer <token>"
```

This two-step process ensures:

1. Citation counts are fetched from Crossref and stored in `PublicationStats.citations_count`
2. Journal-level metrics (impact factor, cite score, h-index) are recalculated using the updated citation data

---

## Python Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000/api/publications"
TOKEN = "your-admin-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
}

# Sync citations for journal with ID 5
response = requests.post(
    f"{BASE_URL}/admin/sync-citations/",
    params={"journal_id": 5, "limit": 50},
    headers=headers
)

print("Citation Sync Results:")
print(f"Total processed: {response.json()['total_processed']}")
print(f"Updated: {response.json()['updated_count']}")
print(f"Errors: {response.json()['error_count']}")

# Recalculate stats for the same journal
response = requests.post(
    f"{BASE_URL}/admin/recalculate-stats/",
    params={"journal_id": 5},
    headers=headers
)

print("\nStats Recalculation Results:")
print(f"Journal: {response.json()['journal']['title']}")
print(f"Total articles: {response.json()['journal']['total_articles']}")
print(f"Impact factor: {response.json()['journal']['impact_factor']}")
print(f"H-index: {response.json()['journal']['h_index']}")
```

---

## Error Responses

### 403 Forbidden (Non-admin user)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found (Invalid journal ID)

```json
{
  "error": "Journal with ID 999 does not exist"
}
```

### 401 Unauthorized (No token)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Rate Limiting

- The citation sync endpoint respects Crossref API rate limits
- Default delay: 0.1 seconds between requests
- Adjust with `delay` parameter if needed (e.g., `delay=0.5` for slower rate)
- Crossref polite pool allows higher rate limits when email contact is provided (already configured)

---

## Scheduled Jobs

Both operations are also automated via scheduled jobs:

- **Citation Sync**: Runs daily at 3:00 AM (up to 100 publications per run)
- **Stats Recalculation**: Triggered automatically via Django signals when publications/issues are modified

Manual execution via these admin endpoints is useful for:

- Immediate updates without waiting for scheduled jobs
- Syncing specific journals on demand
- Forcing re-sync of recently updated publications
- Testing and debugging

---

## Swagger/OpenAPI Documentation

These endpoints are also documented in the interactive API documentation:

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

Look for the "Admin" tag in the API documentation.
