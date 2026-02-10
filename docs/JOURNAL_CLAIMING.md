# Journal Claiming System

## Overview

The journal claiming system allows **active institutions** to claim ownership of imported journals. Unlike the author/institution account claiming (which is for creating new accounts), journal claiming is for transferring journal ownership from system placeholders to legitimate publisher institutions.

## How Journals Are Imported

When journals are imported from external sources (NEPJOL, Crossref, journal portals, etc.), they are initially assigned to a system placeholder institution:

- **Institution Name**: "External Imports"
- **Email**: `system.institution@researchindex.import`
- **Status**: Inactive (`is_active=False`)

This ensures that imported journals are visible in the system but clearly marked as needing legitimate ownership.

## Current Status

- **7 claimable journals** waiting for publishers to claim them
- **4 active institutions** eligible to claim journals
- Journals are from sources like NepJOL, MDPI AG, and other publishers

## Journal Claiming Process

### For Institutions

1. **Login** as an active institution
2. **Search** for claimable journals by title, ISSN, or publisher name
3. **Claim** the journal you publish
4. Journal ownership is **transferred** to your institution
5. **Manage** your claimed journals

### Search for Claimable Journals

**Endpoint**: `GET /api/auth/journals/claim/search/`

**Parameters**:

- `search_query` (required): Journal title, ISSN, or publisher name

**Example Request**:

```http
GET /api/auth/journals/claim/search/?search_query=Nepal
```

**Example Response**:

```json
{
  "results": [
    {
      "id": 7,
      "title": "Journal of Nepal Health Research Council",
      "short_title": "",
      "issn": "",
      "e_issn": "",
      "publisher_name": "Journal of Nepal Health Research Council",
      "description": "...",
      "website": "https://hgf.io/ptad",
      "established_year": null,
      "frequency": "quarterly",
      "language": "English",
      "current_owner": "External Imports",
      "current_owner_email": "system.institution@researchindex.import"
    }
  ],
  "count": 1,
  "search_query": "Nepal"
}
```

### Claim a Journal

**Endpoint**: `POST /api/auth/journals/claim/`

**Authentication**: Required (must be logged in as an institution)

**Request Body**:

```json
{
  "journal_id": 7
}
```

**Success Response** (200):

```json
{
  "message": "Successfully claimed journal \"Journal of Nepal Health Research Council\"",
  "journal": {
    "id": 7,
    "title": "Journal of Nepal Health Research Council",
    "issn": "",
    "new_owner": "Your Institution Name",
    "previous_owner": "External Imports"
  }
}
```

**Error Responses**:

- `400 Bad Request`: Invalid journal ID or journal cannot be claimed
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User is not an institution
- `404 Not Found`: Journal does not exist

### List My Journals

**Endpoint**: `GET /api/auth/journals/my-journals/`

**Authentication**: Required (must be logged in as an institution)

**Example Response**:

```json
{
  "count": 2,
  "journals": [
    {
      "id": 7,
      "title": "Journal of Nepal Health Research Council",
      "issn": "",
      "publisher_name": "Journal of Nepal Health Research Council",
      "current_owner": "Your Institution Name",
      "current_owner_email": "your@institution.edu"
    },
    {
      "id": 14,
      "title": "A Peer Reviewed Journal on Social Sciences",
      "issn": "2822-1818",
      "publisher_name": "NepJOL",
      "current_owner": "Your Institution Name",
      "current_owner_email": "your@institution.edu"
    }
  ]
}
```

## Validation Rules

### A journal can be claimed if:

✅ The journal exists in the database
✅ The journal belongs to a system placeholder institution (email contains `system.institution`)
✅ The institution is inactive
✅ The claiming institution is active
✅ The claiming institution doesn't already own this journal

### A journal CANNOT be claimed if:

❌ It's already owned by an active institution
❌ It's not a system placeholder journal
❌ The claiming user is not an institution
❌ The institution is inactive

## Database Queries

### Find all claimable journals:

```python
from publications.models import Journal

claimable_journals = Journal.objects.filter(
    institution__user__is_active=False,
    institution__user__email__icontains='system.institution'
)
```

### SQL Query:

```sql
SELECT j.*, i.institution_name, u.email
FROM publications_journal j
JOIN users_institution i ON j.institution_id = i.id
JOIN users_customuser u ON i.user_id = u.id
WHERE u.is_active = FALSE
  AND u.email LIKE '%system.institution%';
```

## Testing

### Backend Test:

```bash
cd researchindex
python test_journal_claiming.py
```

### API Test (search):

```bash
curl "http://localhost:8000/api/auth/journals/claim/search/?search_query=journal"
```

### API Test (claim - requires authentication):

```bash
# First, login as an institution to get token
# Then:
curl -X POST http://localhost:8000/api/auth/journals/claim/ \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<your_token>" \
  -d '{"journal_id": 7}'
```

## Integration with Account Claiming

The journal claiming system is separate from but complementary to the account claiming system:

| Feature              | Account Claiming                       | Journal Claiming               |
| -------------------- | -------------------------------------- | ------------------------------ |
| **Purpose**          | Create new accounts for imported users | Transfer journal ownership     |
| **User Type**        | Authors & Institutions                 | Institutions only              |
| **Authentication**   | No (creates account)                   | Yes (must be logged in)        |
| **Result**           | New active account                     | Journal ownership transfer     |
| **Endpoint Pattern** | `/api/auth/claim/...`                  | `/api/auth/journals/claim/...` |

## Future Improvements

1. **Bulk Claiming**: Allow institutions to claim multiple journals at once
2. **Ownership Verification**: Email verification before transfer
3. **Dispute Resolution**: Mechanism for handling ownership disputes
4. **Auto-Matching**: Suggest journals to institutions based on profile
5. **Notification System**: Alert institutions when journals matching their profile are imported

## Security Considerations

- Only authenticated institutions can claim journals
- Journal ownership transfers are atomic (database transactions)
- Previous ownership is logged for audit trail
- Cannot claim journals already owned by active institutions
- System institution journals cannot be deleted, only claimed

## Error Handling

### Common Errors:

**"Only institutions can claim journals"**

- User is logged in as an author, not an institution

**"This journal is already owned by an active institution"**

- Journal has been claimed by another institution

**"Journal not found"**

- Invalid journal ID or journal doesn't exist

**"Institution profile not found"**

- User account exists but institution profile is missing (data integrity issue)

## Workflow Example

1. **Institution registers** and activates account
2. **Login** to the system
3. **Search** for journals: `GET /api/auth/journals/claim/search/?search_query=Nepal`
4. **Find** their journal in the results (ID: 7)
5. **Claim** the journal: `POST /api/auth/journals/claim/` with `{"journal_id": 7}`
6. **Verify** ownership: `GET /api/auth/journals/my-journals/`
7. **Manage** the journal through the publications API

## Related Documentation

- [Account Claiming System](ACCOUNT_CLAIMING.md) - For claiming author/institution accounts
- [Publications API](PUBLICATIONS_API.md) - For managing journal content
- [Journals API](JOURNALS_API.md) - For journal CRUD operations
