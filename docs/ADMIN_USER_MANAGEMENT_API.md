# Admin User Management API

## Overview

Admin user management endpoints allow administrators to view, edit, and delete user accounts (both authors and institutions) in the system.

## Authentication

All endpoints require admin authentication:

- User must be authenticated
- User must have `user_type = 'admin'` or `is_staff = True`

## Endpoints

### 1. List All Users

**GET** `/users/admin/users/`

List all users in the system with filtering and search capabilities.

**Query Parameters:**

- `user_type` (optional): Filter by user type (`author`, `institution`, `admin`)
- `search` (optional): Search by email, author name, or institution name

**Response:**

```json
[
  {
    "id": 1,
    "email": "author@example.com",
    "user_type": "author",
    "is_active": true,
    "is_staff": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "profile_name": "Dr. John Doe",
    "profile_info": {
      "institute": "University Example",
      "designation": "Professor",
      "orcid": "0000-0000-0000-0000"
    },
    "publications_count": 15
  }
]
```

### 2. Get Author Details

**GET** `/users/admin/authors/{id}/`

Retrieve detailed information about a specific author.

**Response:**

```json
{
  "id": 1,
  "user_id": 123,
  "email": "author@example.com",
  "is_active": true,
  "title": "Dr.",
  "full_name": "John Doe",
  "institute": "University Example",
  "designation": "Professor",
  "degree": "PhD in Computer Science",
  "gender": "male",
  "profile_picture": "url/to/picture",
  "cv": "url/to/cv",
  "bio": "Short biography",
  "research_interests": "AI, Machine Learning",
  "orcid": "0000-0000-0000-0000",
  "google_scholar": "https://scholar.google.com/...",
  "researchgate": "https://www.researchgate.net/...",
  "linkedin": "https://www.linkedin.com/...",
  "website": "https://example.com",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "stats": {
    "h_index": 10,
    "i10_index": 8,
    "total_citations": 500,
    "total_reads": 1000,
    "total_downloads": 250,
    "recommendations_count": 20,
    "total_publications": 15,
    "average_citations_per_paper": "33.33",
    "last_updated": "2024-01-01T00:00:00Z"
  },
  "publications_count": 15
}
```

### 3. Update Author

**PATCH** `/users/admin/authors/{id}/`

Update author profile information.

**Request Body:**

```json
{
  "email": "newemail@example.com",
  "is_active": true,
  "full_name": "Dr. John Smith",
  "institute": "New University",
  "designation": "Associate Professor",
  "bio": "Updated biography"
}
```

**Response:**

```json
{
  "message": "Author updated successfully",
  "author": {
    /* Author detail object */
  }
}
```

### 4. Delete Author

**DELETE** `/users/admin/authors/{id}/`

Delete an author and their associated user account (cascades).

**Response:**

```json
{
  "message": "Author \"Dr. John Doe\" has been deleted successfully"
}
```

### 5. Get Institution Details

**GET** `/users/admin/institutions/{id}/`

Retrieve detailed information about a specific institution.

**Response:**

```json
{
  "id": 1,
  "user_id": 456,
  "email": "institution@example.com",
  "is_active": true,
  "institution_name": "Example University",
  "institution_type": "university",
  "logo": "url/to/logo",
  "description": "About the institution",
  "address": "Street address",
  "city": "City",
  "state": "State",
  "country": "Country",
  "postal_code": "12345",
  "phone": "+1 234 567 8900",
  "website": "https://example.edu",
  "established_year": 2000,
  "research_areas": "Main research areas",
  "total_researchers": 100,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "stats": {
    "total_publications": 50,
    "total_citations": 1000,
    "average_citations_per_paper": "20.00",
    "total_reads": 2000,
    "total_downloads": 500,
    "recommendations_count": 30,
    "total_authors": 10,
    "last_updated": "2024-01-01T00:00:00Z",
    "compared_summary": "Institution's research contribution..."
  }
}
```

### 6. Update Institution

**PATCH** `/users/admin/institutions/{id}/`

Update institution profile information.

**Request Body:**

```json
{
  "email": "newemail@institution.com",
  "is_active": true,
  "institution_name": "New Institution Name",
  "institution_type": "research_institute",
  "city": "New City",
  "country": "New Country"
}
```

**Response:**

```json
{
  "message": "Institution updated successfully",
  "institution": {
    /* Institution detail object */
  }
}
```

### 7. Delete Institution

**DELETE** `/users/admin/institutions/{id}/`

Delete an institution and their associated user account (cascades).

**Response:**

```json
{
  "message": "Institution \"Example University\" has been deleted successfully"
}
```

## Error Responses

### 403 Forbidden

```json
{
  "error": "Admin permission required"
}
```

### 404 Not Found

```json
{
  "error": "Author/Institution not found"
}
```

### 400 Bad Request

```json
{
  "field_name": ["Error message"]
}
```

## Implementation Details

### Backend Files

- **Serializers**: `backend-research-index/users/serializers.py`
  - `AdminUserListSerializer`: For listing users
  - `AdminAuthorDetailSerializer`: For author CRUD operations
  - `AdminInstitutionDetailSerializer`: For institution CRUD operations

- **Views**: `backend-research-index/users/views/admin_views.py`
  - `AdminUserListView`: List all users with filtering
  - `AdminAuthorDetailView`: Author detail, update, delete
  - `AdminInstitutionDetailView`: Institution detail, update, delete

- **URLs**: `backend-research-index/users/urls.py`
  - `/users/admin/users/`
  - `/users/admin/authors/<int:pk>/`
  - `/users/admin/institutions/<int:pk>/`

### Frontend Implementation

- **Location**: `frontend-research-index/features/panel/admin/users/`
- **Components**:
  - `UsersList.tsx`: Main table with search and filters
  - `AuthorEditDialog.tsx`: Edit author modal
  - `InstitutionEditDialog.tsx`: Edit institution modal

- **Hooks**:
  - `useAdminUsersQuery`: Fetch users list
  - `useAdminAuthorDetailQuery`: Fetch author details
  - `useAdminInstitutionDetailQuery`: Fetch institution details
  - `useUpdateAuthorMutation`: Update author
  - `useUpdateInstitutionMutation`: Update institution
  - `useDeleteAuthorMutation`: Delete author
  - `useDeleteInstitutionMutation`: Delete institution

## Features

### User List

- View all users (authors, institutions, admins)
- Filter by user type
- Search by email, name, or institution name
- Display key information and statistics
- Quick access to edit and delete actions

### Edit Capabilities

- Update email and account status (active/inactive)
- Edit all profile fields
- Real-time validation
- Automatic cache invalidation on updates

### Delete Operations

- Confirmation dialog before deletion
- Cascading deletion (removes user account and all associated data)
- Cannot delete admin users from the interface

## Security Considerations

- All endpoints check for admin authentication
- Super admin cannot be deleted through these endpoints
- Email uniqueness is enforced
- Password changes not allowed through these endpoints (use dedicated password change endpoint)

## Usage Example

### Admin Panel Integration

Add to admin panel navigation:

```tsx
import { UsersList } from "@/features/panel/admin/users";

// In admin layout or router
<Route path="/admin/users" element={<UsersList />} />;
```

The component handles all data fetching, state management, and user interactions internally.
