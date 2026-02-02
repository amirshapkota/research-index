# Volumes Endpoint Status and Data Requirements

## Current Status

✅ **Endpoint is WORKING CORRECTLY**

The `/api/publications/journals/public/<journal_id>/volumes/` endpoint is functional and returns proper nested data when Issues exist.

## Test Results

### Working Example (Journal ID 6)

```bash
GET /api/publications/journals/public/6/volumes/
```

Response:

```json
{
  "journal_id": 6,
  "journal_title": "New Journal",
  "total_volumes": 1,
  "volumes": [
    {
      "volume": 12,
      "year": 2025,
      "issues_count": 1,
      "articles_count": 2,
      "issues": [
        {
          "id": 4,
          "volume": 12,
          "issue_number": 2,
          "title": "Volume 12, Issue 2",
          "articles": [...]
        }
      ]
    }
  ]
}
```

### Empty Example (Journals without Issues)

```bash
GET /api/publications/journals/public/7/volumes/
```

Response:

```json
{
  "journal_id": 7,
  "journal_title": "Journal of Nepal Health Research Council",
  "total_volumes": 0,
  "volumes": []
}
```

## Why Some Journals Show Empty Volumes

### Data Requirements

For volumes to appear, the system requires:

1. **Issue Objects** must exist in the database
   - `Issue.journal` → Points to the Journal
   - `Issue.volume` → Volume number (integer)
   - `Issue.issue_number` → Issue number (integer)
   - `Issue.status` → Must be 'published'

2. **IssueArticle Links** must exist
   - Links `Issue` to `Publication`
   - Created via `IssueArticle` model

3. **Publication Fields** (optional but recommended)
   - `Publication.volume` → Should match `Issue.volume`
   - `Publication.issue` → Should match `Issue.issue_number`

### Current Database State

| Journal ID | Name                                     | Publications | Issues | IssueArticles | Volumes Display |
| ---------- | ---------------------------------------- | ------------ | ------ | ------------- | --------------- |
| 6          | New Journal                              | -            | 1      | 2             | ✅ Shows data   |
| 7          | Journal of Nepal Health Research Council | 9            | 0      | 0             | ❌ Empty        |
| 1          | Test Journal                             | -            | 0      | 0             | ❌ Empty        |
| 8          | Test Journal                             | -            | 0      | 0             | ❌ Empty        |

### Why External Sync Publications Don't Show

The external API sync creates Publications BUT:

❌ **Problem**: External API doesn't provide `volume` and `issue` data in `publication_details`

Result:

- `Publication.volume` = '' (empty)
- `Publication.issue` = '' (empty)
- No `Issue` objects created
- No `IssueArticle` links created
- **Volumes endpoint returns empty array**

## Solutions

### Option 1: Fix External API Data

Ensure external API returns volume/issue in response:

```json
{
  "publication_details": {
    "volume": "12",
    "issue": "2",
    "pages": "121-130"
  }
}
```

Then re-run sync:

```bash
python manage.py sync_external_publications
```

### Option 2: Create Issues Manually

If publications have volume/issue data, run:

```bash
# Dry run to see what would be created
python manage.py create_issues_from_publications --dry-run

# Actually create
python manage.py create_issues_from_publications
```

### Option 3: Manually Add to Database

Use Django admin or shell:

```python
from publications.models import Journal, Issue, IssueArticle, Publication

journal = Journal.objects.get(id=7)

# Create issue
issue = Issue.objects.create(
    journal=journal,
    volume=20,
    issue_number=1,
    title="Volume 20, Issue 1",
    publication_date="2025-01-01",
    status='published'
)

# Link publications
pub = Publication.objects.get(id=15)
IssueArticle.objects.create(
    issue=issue,
    publication=pub,
    order=1
)
```

## Endpoint Features

### Grouping Logic

- Groups by **volume number**
- Sorts volumes in **descending order** (newest first)
- Within each volume, issues sorted by **issue number (descending)**
- Articles within issues sorted by **order** field

### Response Structure

```
Journal
└── Volumes (grouped)
    └── Issues
        └── Articles (IssueArticle)
            └── Publication details
```

### Performance Optimizations

Uses efficient queries:

```python
.select_related('journal')
.prefetch_related(
    'articles',
    'articles__publication',
    'articles__publication__author'
)
```

### What's Included

Each article includes:

- Full publication metadata (title, abstract, DOI, pages)
- Combined authors (main author + co-authors)
- PDF download URL
- Published date
- Article order and section

## Testing Checklist

- [ ] External API provides volume/issue data
- [ ] Issue objects exist with status='published'
- [ ] IssueArticle links created
- [ ] Journal is active (`is_active=True`)
- [ ] Test endpoint: `GET /api/publications/journals/public/{id}/volumes/`

## Debugging

### Check if publications have volume/issue:

```python
from publications.models import Publication

# Count publications with volume/issue
Publication.objects.exclude(volume='').exclude(issue='').count()

# See specific publication
pub = Publication.objects.get(id=15)
print(f"Volume: '{pub.volume}', Issue: '{pub.issue}'")
```

### Check issues for a journal:

```python
from publications.models import Journal

journal = Journal.objects.get(id=7)
print(f"Total issues: {journal.issues.count()}")
print(f"Published issues: {journal.issues.filter(status='published').count()}")
```

### Check IssueArticle links:

```python
from publications.models import IssueArticle

print(f"Total article links: {IssueArticle.objects.count()}")

# For specific issue
issue = Issue.objects.first()
print(f"Articles in issue: {issue.articles.count()}")
```

## Next Steps

1. ✅ Endpoint is working - **No code changes needed**
2. ⚠️ Need proper data in database
3. Choose one solution above to populate Issue objects
4. Test with real journal that should have volumes
5. Verify response includes nested articles

## Related Files

- **View**: `publications/views.py` → `PublicJournalVolumesView`
- **Serializers**: `publications/serializers.py` → `IssueArticleDetailSerializer`, `IssueWithArticlesSerializer`
- **Models**: `publications/models.py` → `Issue`, `IssueArticle`, `Publication`
- **Sync**: `publications/services/data_mapper.py` → `_get_or_create_issue()`
- **Management Command**: `publications/management/commands/create_issues_from_publications.py`
