# Admin Endpoints - Quick Reference

## Created Files

1. **Backend Views**: `publications/views/views.py` (updated)
   - Added `SyncCitationsAdminView` class
   - Added `RecalculateStatsAdminView` class

2. **URL Configuration**: `publications/urls.py` (updated)
   - Added `/api/publications/admin/sync-citations/`
   - Added `/api/publications/admin/recalculate-stats/`

3. **Documentation**: `docs/ADMIN_ENDPOINTS.md`
   - Complete API documentation with examples
   - Python usage examples
   - Error handling guide

4. **Test Script**: `test_admin_endpoints.py`
   - Ready-to-use testing script
   - Demonstrates both endpoints

## Quick Start

### 1. Sync Citations

```bash
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?limit=10" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 2. Recalculate Stats

```bash
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 3. Full Workflow (Specific Journal)

```bash
# Sync citations for journal ID 5
curl -X POST "http://localhost:8000/api/publications/admin/sync-citations/?journal_id=5" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Recalculate stats for the same journal
curl -X POST "http://localhost:8000/api/publications/admin/recalculate-stats/?journal_id=5" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## API Endpoints Summary

| Endpoint                                     | Method | Permission  | Description                      |
| -------------------------------------------- | ------ | ----------- | -------------------------------- |
| `/api/publications/admin/sync-citations/`    | POST   | IsAdminUser | Sync citations from Crossref API |
| `/api/publications/admin/recalculate-stats/` | POST   | IsAdminUser | Recalculate journal statistics   |

## Query Parameters

### sync-citations

- `limit` (int): Limit number of publications to sync
- `journal_id` (int): Sync specific journal only
- `force` (bool): Re-sync recently updated publications
- `delay` (float): Delay between API requests (default: 0.1s)

### recalculate-stats

- `journal_id` (int): Recalculate specific journal only
- `create_missing` (bool): Create missing JournalStats records (default: true)

## Testing

Run the test script:

```bash
cd researchindex
python test_admin_endpoints.py
```

(Remember to update the TOKEN variable first)

## Swagger Documentation

View interactive API docs:

- http://localhost:8000/api/schema/swagger-ui/
- Look for "Admin" tag

## Features

✅ Admin-only access (requires `is_staff=True`)  
✅ Detailed response with processing results  
✅ Support for batch operations  
✅ Support for targeted operations (specific journal)  
✅ Rate limiting for Crossref API  
✅ Error handling and logging  
✅ OpenAPI/Swagger documentation

## Notes

- Citations are synced from Crossref API (publications must have DOIs)
- By default, skips publications synced within last 7 days
- NEPJOL DOIs (10.3126/\*) may not be in Crossref database
- Stats calculation includes: Impact Factor, CiteScore, H-Index
- Both operations can also run via scheduled jobs (daily at 3 AM)
