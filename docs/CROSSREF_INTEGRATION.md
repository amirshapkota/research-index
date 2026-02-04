# Crossref API Integration

Complete integration with Crossref REST API for fetching publication metadata, citations, references, and journal information.

## Table of Contents

- [Overview](#overview)
- [API Endpoints](#api-endpoints)
- [Service Methods](#service-methods)
- [Utility Functions](#utility-functions)
- [Usage Examples](#usage-examples)
- [Management Commands](#management-commands)
- [Frontend Integration](#frontend-integration)

## Overview

The Crossref integration provides:

- **Metadata Retrieval**: Get complete publication details by DOI
- **Search**: Search works, funders, and journals
- **Citations & References**: Track citations and references
- **Journal Information**: Fetch journal details by ISSN
- **Data Import**: Import publications into database from DOI
- **Auto-enrichment**: Enrich existing publications with Crossref data

## API Endpoints

All endpoints are prefixed with `/api/common/crossref/`

### Works

#### Get Work by DOI

```
GET /api/common/crossref/works/{doi}/
```

**Example:**

```bash
GET /api/common/crossref/works/10.1037/0003-066X.59.1.29/
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "raw": { ... },  // Full Crossref response
    "normalized": {
      "doi": "10.1037/0003-066X.59.1.29",
      "title": "How the Mind Hurts and Heals the Body",
      "authors": [...],
      "published_date": "2004-01-01",
      "journal": "American Psychologist",
      "citation_count": 1234,
      ...
    }
  }
}
```

#### Search Works

```
GET /api/common/crossref/search/works/?query={query}&rows={rows}&offset={offset}
```

**Parameters:**

- `query` (required): Search query
- `rows` (optional): Number of results (default: 20, max: 1000)
- `offset` (optional): Starting position (default: 0)
- `sort` (optional): Sort field (e.g., "published", "relevance")
- `order` (optional): "asc" or "desc" (default: "desc")

**Example:**

```bash
GET /api/common/crossref/search/works/?query=machine+learning+climate&rows=10
```

#### Get Work References

```
GET /api/common/crossref/works/{doi}/references/
```

Returns list of references cited by the publication.

#### Get Work Citations

```
GET /api/common/crossref/works/{doi}/citations/
```

Returns citation count for the publication.

### Journals

#### Get Journal by ISSN

```
GET /api/common/crossref/journals/{issn}/
```

**Example:**

```bash
GET /api/common/crossref/journals/1476-4687/
```

#### Get Journal Works

```
GET /api/common/crossref/journals/{issn}/works/?rows={rows}&offset={offset}
```

Get publications from a specific journal.

### Validation

#### Validate DOI

```
GET /api/common/crossref/validate-doi/?doi={doi}
```

Check if a DOI exists in Crossref database.

### Funders

#### Search Funders

```
GET /api/common/crossref/search/funders/?query={query}&rows={rows}
```

Search for research funding organizations.

## Service Methods

### CrossrefService

Located in `common/services/crossref.py`

```python
from common.services.crossref import CrossrefService

service = CrossrefService()

# Get work by DOI
work = service.get_work_by_doi('10.1037/0003-066X.59.1.29')

# Search works
results = service.search_works(
    query='climate change',
    rows=20,
    sort='published',
    order='desc'
)

# Get references
references = service.get_work_references('10.1037/0003-066X.59.1.29')

# Get citation count
citations = service.get_work_citations('10.1037/0003-066X.59.1.29')

# Get journal info
journal = service.get_journal_by_issn('1476-4687')

# Validate DOI
is_valid = service.validate_doi('10.1037/0003-066X.59.1.29')

# Extract normalized data
work = service.get_work_by_doi('10.1037/0003-066X.59.1.29')
normalized = service.extract_publication_data(work)
```

## Utility Functions

### Import Publication from DOI

```python
from common.utils import import_publication_from_doi

# Import a publication
publication = import_publication_from_doi('10.1037/0003-066X.59.1.29')
if publication:
    print(f"Imported: {publication.title}")
```

### Enrich Existing Publication

```python
from common.utils import enrich_publication_from_crossref
from publications.models import Publication

publication = Publication.objects.get(id=123)
success = enrich_publication_from_crossref(publication)
if success:
    print(f"Updated citation count: {publication.citation_count}")
```

### Bulk Import

```python
from common.utils import bulk_import_from_dois

dois = [
    '10.1037/0003-066X.59.1.29',
    '10.1038/nature12373',
    '10.1126/science.1259855',
]

results = bulk_import_from_dois(dois)
print(f"Success: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")
print(f"Existing: {len(results['existing'])}")
```

### Update Citation Counts

```python
from common.utils import update_citation_counts

# Update all publications
updated = update_citation_counts()
print(f"Updated {updated} publications")
```

## Usage Examples

### Backend: Django Views

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from common.services.crossref import CrossrefService

class MyPublicationView(APIView):
    def get(self, request, doi):
        service = CrossrefService()
        work = service.get_work_by_doi(doi)

        if work:
            normalized = service.extract_publication_data(work)
            return Response(normalized)

        return Response({'error': 'Not found'}, status=404)
```

### Backend: Import on Publication Creation

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from publications.models import Publication
from common.utils import enrich_publication_from_crossref

@receiver(post_save, sender=Publication)
def enrich_from_crossref(sender, instance, created, **kwargs):
    if created and instance.doi:
        enrich_publication_from_crossref(instance)
```

### Frontend: API Calls

```typescript
// Search for works
const searchWorks = async (query: string) => {
  const response = await fetch(
    `/api/common/crossref/search/works/?query=${encodeURIComponent(query)}&rows=20`,
  );
  const data = await response.json();
  return data.data.items;
};

// Get work by DOI
const getWorkByDOI = async (doi: string) => {
  const response = await fetch(
    `/api/common/crossref/works/${encodeURIComponent(doi)}/`,
  );
  const data = await response.json();
  return data.data.normalized;
};

// Validate DOI
const validateDOI = async (doi: string) => {
  const response = await fetch(
    `/api/common/crossref/validate-doi/?doi=${encodeURIComponent(doi)}`,
  );
  const data = await response.json();
  return data.data.is_valid;
};
```

## Management Commands

### Update Citation Counts

Run periodically (e.g., weekly) to keep citation counts up to date:

```bash
python manage.py update_citation_counts
```

You can set up a scheduled task using Django APScheduler or Celery:

```python
# In your scheduler configuration
from apscheduler.schedulers.background import BackgroundScheduler
from common.utils import update_citation_counts

scheduler = BackgroundScheduler()
scheduler.add_job(
    update_citation_counts,
    'interval',
    weeks=1,
    id='update_citations',
    replace_existing=True
)
scheduler.start()
```

## Frontend Integration

### Create React Hooks

```typescript
// hooks/useCrossref.ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useWorkByDOI(doi: string) {
  return useQuery({
    queryKey: ["crossref", "work", doi],
    queryFn: async () => {
      const response = await api.get(`/common/crossref/works/${doi}/`);
      return response.data.normalized;
    },
    enabled: !!doi,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}

export function useSearchWorks(query: string, rows = 20) {
  return useQuery({
    queryKey: ["crossref", "search", query, rows],
    queryFn: async () => {
      const response = await api.get(
        `/common/crossref/search/works/?query=${encodeURIComponent(query)}&rows=${rows}`,
      );
      return response.data.items;
    },
    enabled: !!query && query.length > 2,
  });
}

export function useValidateDOI(doi: string) {
  return useQuery({
    queryKey: ["crossref", "validate", doi],
    queryFn: async () => {
      const response = await api.get(
        `/common/crossref/validate-doi/?doi=${encodeURIComponent(doi)}`,
      );
      return response.data.is_valid;
    },
    enabled: !!doi,
  });
}
```

### Example Component

```tsx
import { useWorkByDOI } from "@/hooks/useCrossref";

export function PublicationDetails({ doi }: { doi: string }) {
  const { data, isLoading, error } = useWorkByDOI(doi);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading publication</div>;

  return (
    <div>
      <h2>{data.title}</h2>
      <p>Authors: {data.authors.map((a) => a.name).join(", ")}</p>
      <p>Journal: {data.journal}</p>
      <p>Citations: {data.citation_count}</p>
      <p>Published: {data.published_date}</p>
    </div>
  );
}
```

## Caching

The service uses Django's caching framework to cache API responses for 24 hours, reducing API calls and improving performance. Make sure you have caching configured in your settings:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

Or use the simple in-memory cache for development:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## Rate Limiting

Crossref recommends:

- Including a User-Agent header (already implemented)
- Polite usage (max 50 requests per second)
- Using cursor-based pagination for large result sets

The service includes a polite User-Agent header with your contact email. Update it in `common/services/crossref.py`:

```python
USER_AGENT = "ResearchIndexNepal/1.0 (mailto:your-email@example.com)"
```

## Error Handling

All methods handle errors gracefully and return `None` or empty data on failure. Errors are logged using Django's logging framework.

## Best Practices

1. **Use DOI for Publication Lookup**: Always use DOI when available for accurate matching
2. **Cache Aggressively**: Crossref data doesn't change often, cache for 24+ hours
3. **Batch Operations**: Use bulk import for multiple DOIs
4. **Update Periodically**: Run citation count updates weekly
5. **Validate Before Import**: Check DOI validity before importing
6. **Handle Missing Data**: Not all fields are available for all works
7. **Use Normalized Data**: The `extract_publication_data()` method provides cleaned data

## Troubleshooting

### DOI Not Found

- Ensure DOI is properly formatted (without "https://doi.org/" prefix)
- Check if DOI is registered with Crossref (not all DOIs are)

### API Timeout

- Increase timeout in `CrossrefService._make_request()` method
- Check your internet connection

### Empty Results

- Some journals don't provide all metadata
- References and citations may not be available for all works
- Try alternative search queries

## Future Enhancements

- [ ] Add cursor-based pagination for large result sets
- [ ] Implement Crossref Plus API features (requires membership)
- [ ] Add support for filters (publication type, date range, etc.)
- [ ] Create admin interface for bulk imports
- [ ] Add webhook support for DOI updates
- [ ] Implement cited-by tracking using external services
