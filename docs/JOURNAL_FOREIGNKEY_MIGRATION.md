# Journal ForeignKey Migration

## Overview
Changed the `Publication` model to use a `ForeignKey` relationship to `Journal` instead of a plain `CharField` for journal name. This improves data integrity and enables better relational queries.

## Backend Changes

### Model Changes (`publications/models.py`)
**Before:**
```python
journal_name = models.CharField(max_length=300, blank=True, help_text="Journal or conference name")
```

**After:**
```python
journal = models.ForeignKey(
    'Journal',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='journal_publications',
    help_text="Journal this publication belongs to"
)
```

### Serializer Changes (`publications/serializers.py`)

#### PublicationListSerializer
- Added `journal_id` (journal.id)
- Added `journal_name` (journal.title) - for backward compatibility
- Added `journal_issn` (journal.issn)

#### PublicationDetailSerializer
- Includes `journal` (the ID for write operations)
- Added `journal_id`, `journal_title`, `journal_issn` for read operations

#### PublicationCreateUpdateSerializer
- Changed `journal_name` field to `journal` (accepts integer ID)
- Form data should now send `journal` as a number instead of `journal_name` as a string

### Migration
```bash
python manage.py makemigrations
# Created: publications/migrations/0006_remove_publication_journal_name_publication_journal.py

python manage.py migrate
# Applies the migration
```

## Frontend Changes

### Type Changes (`frontend/features/panel/author/publications/types/index.ts`)

**Publication Interface:**
```typescript
// Removed: (nothing - journal_name still exists but is now computed from journal.title)

// Added:
journal: number | null;           // ForeignKey ID for write operations
journal_id: number | null;        // Same as journal, for clarity
journal_name: string | null;      // Computed from journal.title (read-only)
journal_issn: string | null;      // From journal.issn (read-only)
```

**PublicationFormData Interface:**
```typescript
// Removed:
journal_name?: string;

// Added:
journal?: number;
```

### Schema Changes (`frontend/features/panel/author/publications/schema/index.ts`)
```typescript
// Removed:
journal_name: z.string().optional().default(""),

// Added:
journal: z.number().nullable().optional(),
```

### Component Changes

#### PublicationFormDialog
- Changed form field from text input for `journal_name` to number input for `journal`
- Updated form data submission to send `journal` (number) instead of `journal_name` (string)
- Updated default values to use `publication?.journal` instead of `publication?.journal_name`

#### PublicationsList & ArticleCard
- Components continue to work with `journal_name` field which is now populated from `journal.title` in the serializer
- No changes needed as the serializer provides backward-compatible field names

## API Changes

### Request Format (Create/Update Publication)
**Before:**
```json
{
  "title": "My Publication",
  "journal_name": "Nature",
  "volume": "10"
}
```

**After:**
```json
{
  "title": "My Publication",
  "journal": 5,  // Journal ID
  "volume": "10"
}
```

### Response Format (List/Detail)
**List Response:**
```json
{
  "id": 1,
  "title": "My Publication",
  "journal_id": 5,
  "journal_name": "Nature",
  "journal_issn": "0028-0836",
  "volume": "10"
}
```

**Detail Response:**
```json
{
  "id": 1,
  "title": "My Publication",
  "journal": 5,
  "journal_id": 5,
  "journal_name": "Nature",  // From journal.title
  "journal_issn": "0028-0836",
  "volume": "10"
}
```

**Note:** The `journal_name` field in responses is backward-compatible. It's a computed field sourced from `journal.title` in the serializer, so existing frontend code continues to work without changes.

## Benefits

1. **Data Integrity**: Publications are now linked to actual Journal records
2. **Better Queries**: Can easily fetch all publications for a specific journal
3. **Referential Integrity**: Using `on_delete=models.SET_NULL` preserves publication records even if a journal is deleted
4. **Rich Data**: Can access full journal information (publisher, ISSN, institution, etc.) through the relationship
5. **Validation**: Can ensure publications only reference valid journals

## Migration Notes

- Existing publications with `journal_name` values will have `journal` set to `null` after migration
- The field is optional (`null=True, blank=True`) to maintain backward compatibility
- Consider creating a data migration script if you need to map existing `journal_name` values to actual Journal IDs
- The `journal_name` field in API responses is now a computed field from `journal.title` for backward compatibility

## Usage Example

### Creating a Publication with Journal
```python
from publications.models import Publication, Journal

journal = Journal.objects.get(id=5)
publication = Publication.objects.create(
    title="My Research",
    journal=journal,  # Use journal object or ID
    volume="10",
    ...
)
```

### Querying Publications by Journal
```python
# Get all publications for a specific journal
journal_pubs = Publication.objects.filter(journal__id=5)

# Get publications with journal data
pubs = Publication.objects.select_related('journal').all()
for pub in pubs:
    print(f"{pub.title} - {pub.journal.title if pub.journal else 'No journal'}")
```

## Future Improvements

1. Create a journal selector component in the frontend form (dropdown/autocomplete)
2. Add journal search/filter functionality in publication forms
3. Consider creating a data migration to map existing journal names to Journal records
4. Add validation to suggest similar journals when creating publications
