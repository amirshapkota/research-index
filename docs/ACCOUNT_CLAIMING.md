# Account Claiming System

## Overview

The account claiming system allows imported users (authors and institutions) to activate their accounts. Users can be imported from multiple external sources including:

- **NEPJOL** (Nepal Journals Online)
- **Journal Portal APIs**
- **Crossref**
- **Other external data sources**

## Import Email Patterns

All imported users have email addresses following specific patterns that identify them as claimable accounts. The system recognizes the following patterns:

### Supported Email Patterns

1. **@imported.\*** - Standard import pattern
   - Example: `author_0000-0001-2345-6789@imported.nepjol.np`
   - Used for: NEPJOL imports, Crossref, journal portals

2. **@external.\*** - External source imports
   - Example: `sapana-adhikari@external.import`
   - Used for: External data sources, manual imports

3. **@test.\*** - Test/staging imports
   - Example: `test_0009-0006-1014-5790_1@test.nepjol.np`
   - Used for: Testing, development, staging data

All these users are created with `is_active=False` status and cannot log in until they claim their accounts.

## Search Algorithm

The search functionality looks for inactive users whose emails contain any of the supported patterns (`@imported.`, `@external.`, or `@test.`):

### For Authors:

- Search by full name
- Search by ORCID
- Search by institution name
- Search by designation

### For Institutions:

- Search by institution name
- Search by country
- Search by city
- Search by institution type

## Claiming Process

1. **Search**: User searches for their imported profile
2. **Select**: User selects their profile from results
3. **Verify**: System displays profile details for confirmation
4. **Update**: User provides:
   - New email address (must be unique)
   - Password
   - Optional profile updates
5. **Activate**: System:
   - Updates email and password
   - Sets `is_active=True`
   - Logs user in automatically
   - Issues JWT tokens

## API Endpoints

### Search Imported Profiles

```http
GET /api/auth/claim/search/?user_type=author&search_query=John
```

Response:

```json
{
  "results": [
    {
      "id": 123,
      "user_id": 456,
      "email": "author_john@imported.source.com",
      "full_name": "John Doe",
      "orcid": "0000-0001-2345-6789",
      "is_active": false
    }
  ],
  "count": 1,
  "user_type": "author",
  "search_query": "John"
}
```

### Claim Author Account

```http
POST /api/auth/claim/author/
Content-Type: application/json

{
  "author_id": 123,
  "new_email": "john.doe@example.com",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "bio": "Researcher in Computer Science",
  "research_interests": "AI, Machine Learning"
}
```

### Claim Institution Account

```http
POST /api/auth/claim/institution/
Content-Type: application/json

{
  "institution_id": 456,
  "new_email": "contact@institution.edu",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "description": "Leading research university",
  "address": "123 Main St"
}
```

## Frontend Pages

- **Main Claim Page**: `/claim-account` - Form interface for searching and claiming
- **Debug Page**: `/claim-account/debug` - Diagnostic tool for testing API connectivity

## Adding New Import Sources

To add a new import source:

1. **Create Import Script**:
   - Use pattern: `management/commands/import_<source>.py`
   - Generate emails with pattern: `@imported.<source>.<domain>`

2. **Import Users**:
   - Create user with `is_active=False`
   - Set email with `@imported.` pattern
   - Create Author/Institution profile

3. **Example**:

```python
# In import script
email = f"author_{orcid}@imported.crossref.org"
user = CustomUser.objects.create_user(
    email=email,
    password=None,  # No password until claimed
    user_type='author',
    is_active=False  # Inactive until claimed
)
```

The claim system will automatically detect any user with `@imported.`, `@external.`, or `@test.` in their email as claimable.

## Security Considerations

- Only inactive users can be claimed
- Email must be unique across all users
- Password validation enforced
- User is logged in immediately after claiming (for UX)
- Original imported email is replaced with user's chosen email

## Database Queries

Check for claimable users:

```sql
-- Imported authors (all patterns)
SELECT a.*, u.email
FROM users_author a
JOIN users_customuser u ON a.user_id = u.id
WHERE u.is_active = FALSE
  AND (u.email LIKE '%@imported.%'
       OR u.email LIKE '%@external.%'
       OR u.email LIKE '%@test.%');

-- Imported institutions (all patterns)
SELECT i.*, u.email
FROM users_institution i
JOIN users_customuser u ON i.user_id = u.id
WHERE u.is_active = FALSE
  AND (u.email LIKE '%@imported.%'
       OR u.email LIKE '%@external.%'
       OR u.email LIKE '%@test.%');
```

## Testing

Run diagnostics:

```bash
# Backend check
python check_imported_users.py

# Frontend check
Visit: http://localhost:3000/claim-account/debug
```
