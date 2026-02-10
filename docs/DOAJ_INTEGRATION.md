# DOAJ Integration for Journal Creation

## Overview

Successfully implemented DOAJ (Directory of Open Access Journals) API v4 integration to allow institutions to import journal data when creating new journals.

**API Reference**: [https://doaj.org/api/v4/docs](https://doaj.org/api/v4/docs)

## Backend Implementation

### 1. DOAJ API Client (`publications/doaj_api.py`)

- **Class**: `DOAJAPI`
  - `search_journals(query, page, page_size)` - Search DOAJ database
  - `get_journal_by_issn(issn)` - Fetch journal by ISSN
  - `_format_journal(raw_data)` - Transform DOAJ data to our Journal model format

**Features**:

- Extracts comprehensive journal metadata from DOAJ
- Maps DOAJ fields to our Journal model fields
- Handles both print and electronic ISSNs
- Extracts subjects, languages, licenses, APC info, peer review details
- Includes error handling with custom `DOAJAPIError` exception

### 2. Django Views (`publications/views/views.py`)

Added two new API endpoints:

**`DOAJSearchView`** (GET `/api/publications/doaj/search/`)

- **Authentication**: Required
- **Parameters**:
  - `q` (required): Search query
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Results per page (default: 10, max: 100)
- **Response**: Paginated journal search results

**`DOAJJournalByISSNView`** (GET `/api/publications/doaj/issn/<issn>/`)

- **Authentication**: Required
- **Parameters**: `issn` (path parameter)
- **Response**: Single journal details or 404 if not found

### 3. URL Routes (`publications/urls.py`)

```python
path('doaj/search/', DOAJSearchView.as_view(), name='doaj-search'),
path('doaj/issn/<str:issn>/', DOAJJournalByISSNView.as_view(), name='doaj-journal-by-issn'),
```

## Frontend Implementation

### 1. DOAJ API Client (`features/panel/institution/journals/api/doajApi.ts`)

TypeScript interfaces and functions:

- `DOAJJournal` interface - Journal data structure from DOAJ
- `DOAJSearchResponse` interface - Search results with pagination
- `searchDOAJJournals()` - Search journals
- `getDOAJJournalByISSN()` - Get journal by ISSN

### 2. DOAJ Search Dialog (`components/DOAJSearchDialog.tsx`)

**Features**:

- Search DOAJ journals by title or ISSN
- Display paginated search results (10 per page)
- Show journal details: title, ISSN, eISSN, publisher, subjects
- Select journal to import
- Pagination controls (Previous/Next)
- Loading states and error handling

**UI Components Used**:

- Dialog, Input, Button, Badge, ScrollArea
- Responsive design with max-height scrollable results
- Visual selection indicator with checkmark

### 3. Updated Journal Form (`components/JournalForm.tsx`)

**New Features**:

- "Search DOAJ" button in create mode (Database icon)
- Opens DOAJ search dialog
- `handleDOAJImport()` function populates form fields

**Auto-populated Fields from DOAJ**:

- Title
- Short Title (from alternative_title)
- ISSN
- eISSN
- Description (built from subjects)
- Scope (from keywords)
- Publisher Name
- Language
- Contact Email
- Website
- is_open_access flag
- peer_reviewed flag
- about_journal (includes license, peer review type, plagiarism detection, publication time, APC info)

## Usage Flow

1. **Institution clicks "Create Journal"** → Navigate to `/institution/journals/create`
2. **Click "Search DOAJ" button** → Opens search dialog
3. **Enter search query** → e.g., "Nature" or "2046-1402"
4. **Browse results** → View journal details with subjects, ISSNs, publisher
5. **Select journal** → Click on desired journal (shows checkmark)
6. **Click "Import Selected Journal"** → Auto-fills form fields
7. **Review and customize** → Edit imported data as needed
8. **Submit form** → Create journal with DOAJ data

## API Documentation

All endpoints are documented in OpenAPI (Swagger):

- Visit `/api/schema/swagger/` to see interactive documentation
- Tag: "DOAJ"
- Includes request/response schemas and examples

## Testing

### Test Backend API

```bash
# Search journals
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/publications/doaj/search/?q=nature&page=1&page_size=10"

# Get journal by ISSN
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/publications/doaj/issn/2046-1402/"
```

### Test Frontend

1. Login as institution user
2. Navigate to http://localhost:3000/institution/journals/create
3. Click "Search DOAJ" button
4. Search for a journal
5. Import and verify fields are populated

## Dependencies

### Backend

- `requests==2.32.5` (already in requirements.txt)

### Frontend

- No new npm packages required
- Uses existing shadcn/ui components: Dialog, Input, Button, Badge, ScrollArea

## Error Handling

**Backend**:

- `DOAJAPIError` for API failures
- 404 responses when journal not found
- 400 for missing query parameters
- 500 for DOAJ API errors

**Frontend**:

- Toast notifications for errors and success
- Loading states during API calls
- Graceful handling of empty results
- Network error handling with user-friendly messages

## Security

- All DOAJ endpoints require authentication
- Institutions can only create journals for their own account
- Data sanitization before populating form fields
- CORS and CSRF protection via Django settings

## Data Mapping

DOAJ fields → Our Journal model:

```
title → title
alternative_title → short_title
issn (pissn) → issn
issn (eissn) → e_issn
publisher.name → publisher_name
language[0] → language
editorial.contact_email → contact_email
ref.journal or link[type=homepage].url → website
license.type → (included in about_journal)
apc.has_apc, apc.max → (included in about_journal)
editorial.review_process → (included in about_journal)
plagiarism.detection → (included in about_journal)
publication_time_weeks → (included in about_journal)
subject[].term → subjects array + description
```

## Future Enhancements

Potential improvements:

1. **Auto-update from DOAJ**: Periodic sync to update journal metadata
2. **Bulk import**: Import multiple journals at once
3. **Advanced search**: Filter by subject, language, country
4. **DOAJ seal indicator**: Show which journals have DOAJ seal
5. **License display**: Show license badge/icon
6. **Comparison view**: Compare multiple journals before importing
7. **Import history**: Track which journals were imported from DOAJ

## Files Modified/Created

### Backend

- ✅ Created: `researchindex/publications/doaj_api.py`
- ✅ Modified: `researchindex/publications/views/views.py`
- ✅ Modified: `researchindex/publications/urls.py`

### Frontend

- ✅ Created: `frontend/features/panel/institution/journals/api/doajApi.ts`
- ✅ Created: `frontend/features/panel/institution/journals/components/DOAJSearchDialog.tsx`
- ✅ Modified: `frontend/features/panel/institution/journals/components/JournalForm.tsx`
- ✅ Modified: `frontend/features/panel/institution/journals/components/index.ts`
- ✅ Modified: `frontend/features/panel/institution/journals/api/index.ts`
- ✅ Modified: `frontend/features/general/journals/api/journals.server.ts` (bug fix)

## Build Status

✅ Backend: Ready
✅ Frontend: Build successful (TypeScript compiled without errors)
✅ All components exported correctly
✅ No linting errors

## Screenshots Reference

**Search DOAJ Button**: Top-right in journal creation form (Database icon)
**Search Dialog**: Full-screen modal with search bar and results list
**Results Display**: Cards showing title, ISSN, publisher, subjects, website link
**Selection**: Blue border and checkmark on selected journal
**Import**: Auto-populates all matching form fields with success toast
