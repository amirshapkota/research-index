# Journal Export and Share Implementation

## Overview

This document describes the implementation of export and share functionality for journal description pages in the Research Index application.

## Backend Implementation

### 1. Export Journal Endpoint

**File**: `researchindex/publications/views/views.py`
**Class**: `ExportJournalView`

**Features**:

- Public endpoint (no authentication required)
- Supports multiple export formats:
  - **JSON**: Structured data export with proper formatting
  - **CSV**: Tabular format with field-value pairs
  - **PDF/Text**: Plain text format (can be enhanced with PDF libraries)
- Includes complete journal information:
  - Basic details (title, ISSN, DOI, etc.)
  - Institution and publisher information
  - Statistics (publications, citations, impact factor)
  - Description and scope

**API Endpoint**: `GET /api/publications/journals/public/{id}/export/?format={json|csv|pdf}`

**Example Usage**:

```bash
# Export as JSON
GET /api/publications/journals/public/13/export/?format=json

# Export as CSV
GET /api/publications/journals/public/13/export/?format=csv

# Export as Text
GET /api/publications/journals/public/13/export/?format=pdf
```

### 2. Share Journal Endpoint

**File**: `researchindex/publications/views/views.py`
**Class**: `ShareJournalView`

**Features**:

- Public endpoint (no authentication required)
- Generates shareable links and metadata
- Provides social media share URLs for:
  - Twitter
  - Facebook
  - LinkedIn
  - WhatsApp
  - Email
- Returns structured data including:
  - Shareable URL
  - Title and description
  - Cover image URL
  - Metadata (ISSN, publisher, impact factor)

**API Endpoint**: `GET /api/publications/journals/public/{id}/share/`

**Response Example**:

```json
{
  "url": "http://localhost:3000/journals/13",
  "title": "Journal of Computer Science",
  "description": "Leading journal in computer science research...",
  "image": "http://localhost:8000/media/journal_covers/cover.jpg",
  "metadata": {
    "issn": "1234-5678",
    "e_issn": "8765-4321",
    "publisher": "Academic Press",
    "institution": "MIT",
    "is_open_access": true,
    "impact_factor": "3.456"
  },
  "social_share_urls": {
    "twitter": "https://twitter.com/intent/tweet?url=...",
    "facebook": "https://www.facebook.com/sharer/sharer.php?u=...",
    "linkedin": "https://www.linkedin.com/sharing/share-offsite/?url=...",
    "whatsapp": "https://wa.me/?text=...",
    "email": "mailto:?subject=...&body=..."
  }
}
```

### 3. URL Configuration

**File**: `researchindex/publications/urls.py`

Added new routes:

- `journals/public/<int:pk>/export/` → ExportJournalView
- `journals/public/<int:pk>/share/` → ShareJournalView

## Frontend Implementation

### 1. Export Journal Button Component

**File**: `frontend/features/general/journals/components/ExportJournalButton.tsx`

**Features**:

- Dropdown menu with export format options
- Direct download functionality
- Loading state handling
- Toast notifications for success/error
- Automatic filename generation from response headers
- File blob handling for browser downloads

**Usage**:

```tsx
<ExportJournalButton journalId={journal.id} />
```

### 2. Share Journal Button Component

**File**: `frontend/features/general/journals/components/ShareJournalButton.tsx`

**Features**:

- Dropdown menu for quick social media sharing
- Modal dialog for full share options
- Copy link to clipboard functionality
- Social media integration:
  - Twitter, Facebook, LinkedIn, WhatsApp, Email
- Loading states and error handling
- Toast notifications
- Lazy loading of share data

**Usage**:

```tsx
<ShareJournalButton journalId={journal.id} journalTitle={journal.title} />
```

### 3. Integration in Journal Details

**File**: `frontend/features/general/journals/components/JournalDetails.tsx`

Updated the `moreOptions` section in the ProfileTabs component to include:

```tsx
moreOptions={
  <div className="flex items-center gap-3">
    <ExportJournalButton journalId={journal.id} />
    <ShareJournalButton journalId={journal.id} journalTitle={journal.title} />
  </div>
}
```

### 4. Component Exports

**File**: `frontend/features/general/journals/components/index.ts`

Added exports:

```typescript
export { ExportJournalButton } from "./ExportJournalButton";
export { ShareJournalButton } from "./ShareJournalButton";
```

## UI Components Used

### Export Button

- Radix UI Dropdown Menu
- Lucide React Icons (FileJson, FileText, FileSpreadsheet, ChevronDown)
- Sonner Toast notifications

### Share Button

- Radix UI Dropdown Menu
- Radix UI Dialog
- Lucide React Icons (Twitter, Facebook, Linkedin, Mail, MessageCircle, Link2, Check)
- Sonner Toast notifications

## User Experience Flow

### Export Flow

1. User clicks "Export" button
2. Dropdown menu appears with format options (JSON, CSV, Text)
3. User selects desired format
4. Frontend makes API call to export endpoint
5. File is automatically downloaded to user's device
6. Success/error toast notification appears

### Share Flow

#### Quick Share (Dropdown)

1. User clicks "Share" button
2. Dropdown menu appears with social media options
3. User selects a platform
4. New window/tab opens with pre-filled share content

#### Full Share (Modal)

1. User clicks "More Share Options" in dropdown
2. Modal dialog opens showing:
   - Input field with journal URL
   - Copy button for clipboard functionality
   - Grid of social media share buttons
3. User can:
   - Copy link to clipboard
   - Share to any social media platform
   - Share via email

## Dependencies

### Backend

- Django REST Framework (existing)
- Python standard libraries (csv, json)

### Frontend

- React 19
- Radix UI (Dialog, Dropdown Menu)
- Lucide React (Icons)
- Sonner (Toast notifications)
- All dependencies already present in package.json

## Testing Recommendations

### Backend Testing

1. Test export endpoint with different formats
2. Verify correct file downloads and content types
3. Test with journals having varying data completeness
4. Check error handling for non-existent journals

### Frontend Testing

1. Test export functionality with all format options
2. Verify share dialog opens correctly
3. Test copy to clipboard functionality
4. Verify social media links open correctly
5. Test on different browsers
6. Test responsive behavior on mobile devices

## Future Enhancements

### Backend

1. Add PDF generation using libraries like:
   - `reportlab` for programmatic PDF creation
   - `weasyprint` for HTML-to-PDF conversion
2. Add BibTeX export format for academic citations
3. Implement download analytics/tracking
4. Add rate limiting for export endpoints

### Frontend

1. Add print functionality
2. Add QR code generation for sharing
3. Implement custom share templates
4. Add share analytics tracking
5. Support for more social platforms (Reddit, Pinterest, etc.)

## Configuration

### Environment Variables

Ensure `NEXT_PUBLIC_BACKEND_URL` is set in frontend `.env.local`:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## API Documentation

The new endpoints are automatically documented in the Django REST Framework Swagger/OpenAPI documentation at:

- `/api/schema/swagger-ui/`
- `/api/schema/redoc/`

Both endpoints are tagged under `[Journals]` in the API documentation.

## Conclusion

The export and share functionality has been successfully implemented following the existing codebase patterns and conventions. The implementation is modular, reusable, and can be easily adapted for other entities (articles, institutions, authors) if needed.
