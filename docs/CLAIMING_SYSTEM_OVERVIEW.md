# Research Index - Complete Claiming System

## Overview

The Research Index has TWO distinct claiming mechanisms for imported data:

1. **Account Claiming** - For imported authors and institutions to activate their accounts
2. **Journal Claiming** - For active institutions to claim ownership of imported journals

## 1. Account Claiming (Authors & Institutions)

### Purpose

Allow imported users to claim their profiles and create active accounts.

### Who Can Claim

- **Imported Authors**: Users with inactive accounts and import-related email patterns
- **Imported Institutions**: Users with inactive accounts and import-related email patterns

### Email Patterns Recognized

- `@imported.*` - Standard imports (e.g., `@imported.nepjol.np`)
- `@external.*` - External source imports (e.g., `@external.import`)
- `@test.*` - Test/staging imports (e.g., `@test.nepjol.np`)

### Current Status

- **23 claimable authors** across 3 import sources
- **0 claimable institutions** (institutions import journals, not themselves)

### Process

1. **No authentication required** (creating new account)
2. User searches for their profile
3. User selects their profile
4. User provides new email, password, and profile updates
5. Account is activated and user is logged in

### API Endpoints

```
Search:  GET  /api/auth/claim/search/?user_type=author&search_query=<name>
Claim:   POST /api/auth/claim/author/
         POST /api/auth/claim/institution/
```

### Documentation

See: [ACCOUNT_CLAIMING.md](./ACCOUNT_CLAIMING.md)

---

## 2. Journal Claiming (Institutions Only)

### Purpose

Transfer ownership of imported journals from system placeholders to legitimate publishers.

### How It Works

Imported journals are initially owned by a system institution:

- **Name**: "External Imports"
- **Email**: `system.institution@researchindex.import`
- **Status**: Inactive

Active institutions can claim these journals and transfer ownership to themselves.

### Who Can Claim

- **Active Institutions Only** (must be logged in)
- Authors cannot claim journals
- Inactive institutions cannot claim journals

### Current Status

- **7 claimable journals** from various publishers:
  - 3 from NepJOL
  - 1 from MDPI AG
  - 1 from Scientific Research and Community Ltd
  - 2 from other sources

### Process

1. **Authentication required** (must be logged in as institution)
2. Institution searches for journals
3. Institution selects a journal to claim
4. Ownership is transferred from system to the institution
5. Institution can now manage the journal

### API Endpoints

```
Search:     GET  /api/auth/journals/claim/search/?search_query=<name>
Claim:      POST /api/auth/journals/claim/
My Journals: GET  /api/auth/journals/my-journals/
```

### Documentation

See: [JOURNAL_CLAIMING.md](./JOURNAL_CLAIMING.md)

---

## Comparison

| Feature                | Account Claiming                   | Journal Claiming                              |
| ---------------------- | ---------------------------------- | --------------------------------------------- |
| **Purpose**            | Activate imported user accounts    | Transfer journal ownership                    |
| **User Types**         | Authors & Institutions             | Institutions only                             |
| **Authentication**     | ❌ No (creates account)            | ✅ Yes (must be logged in)                    |
| **What's Claimed**     | User profile                       | Journal ownership                             |
| **Result**             | New active account                 | Updated journal.institution                   |
| **Can Claim Multiple** | No (1 profile per user)            | Yes (institution can claim multiple journals) |
| **Email Pattern**      | `@imported.` `@external.` `@test.` | N/A (checks owner institution)                |
| **Reversible**         | No                                 | Potentially (with admin)                      |

---

## Database Structure

### Imported Authors

```sql
-- Inactive authors with import email patterns
SELECT * FROM users_author a
JOIN users_customuser u ON a.user_id = u.id
WHERE u.is_active = FALSE
  AND (u.email LIKE '%@imported.%'
       OR u.email LIKE '%@external.%'
       OR u.email LIKE '%@test.%');
```

### Claimable Journals

```sql
-- Journals owned by system placeholder institution
SELECT * FROM publications_journal j
JOIN users_institution i ON j.institution_id = i.id
JOIN users_customuser u ON i.user_id = u.id
WHERE u.is_active = FALSE
  AND u.email LIKE '%system.institution%';
```

---

## Import Sources

### Current Import Sources

1. **NEPJOL** (Nepal Journals Online)
   - 18 authors
   - 3 journals
2. **External Import**
   - 3 authors (including Sapana Adhikari)
3. **Test Data**
   - 2 authors

4. **Other Publishers**
   - MDPI AG (1 journal)
   - Scientific Research and Community Ltd (1 journal)
   - Various (2 journals)

### Future Import Sources

- Crossref
- PubMed
- Google Scholar
- arXiv
- Institution websites
- Journal portal APIs

---

## Workflow Examples

### Example 1: Author Claims Account

```
1. Author visits claim page (no login needed)
2. Searches for "Sapana Adhikari"
3. Finds profile with email sapana-adhikari@external.import
4. Provides new email: sapana@example.com
5. Sets password
6. Account activated and logged in
```

### Example 2: Institution Claims Journal

```
1. Institution registers and activates account
2. Logs in as institution
3. Searches for "Nepal Health Research"
4. Finds "Journal of Nepal Health Research Council"
5. Claims ownership
6. Journal transferred to their institution
7. Can now manage journal publications
```

---

## Testing

### Check System Status

```bash
cd researchindex
python check_imported_users.py
```

### Test Account Claiming

```bash
# Search for authors
curl "http://localhost:8000/api/auth/claim/search/?user_type=author&search_query=Sapana"

# Claim author account (no auth)
curl -X POST http://localhost:8000/api/auth/claim/author/ \
  -H "Content-Type: application/json" \
  -d '{
    "author_id": 6,
    "new_email": "sapana@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!"
  }'
```

### Test Journal Claiming

```bash
# Search for journals (no auth)
curl "http://localhost:8000/api/auth/journals/claim/search/?search_query=Nepal"

# Claim journal (requires auth)
curl -X POST http://localhost:8000/api/auth/journals/claim/ \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=<your_token>" \
  -d '{"journal_id": 7}'

# List my journals (requires auth)
curl -H "Cookie: access_token=<your_token>" \
  http://localhost:8000/api/auth/journals/my-journals/
```

---

## Common Questions

### Q: Why are there no claimable institutions?

A: Institutions don't get imported directly. Instead, journals are imported and owned by a system placeholder. Institutions claim the journals, not their own accounts directly.

### Q: Can an author claim a journal?

A: No. Only institutions can claim journals. Authors can only claim author accounts.

### Q: Can an institution claim multiple journals?

A: Yes! An institution can claim as many journals as they legitimately publish.

### Q: What happens after claiming?

- **Account Claiming**: User gets a new active account and is logged in
- **Journal Claiming**: Journal.institution is updated, previous owner is system placeholder

### Q: Can someone else claim my journal?

A: Once an institution claims a journal, it belongs to that active institution and cannot be claimed by others. First-come, first-served.

### Q: How do I know which journals I can claim?

A: Search by your journal name, ISSN, or publisher name. You should only claim journals you actually publish.

---

## Security Notes

1. **Account Claiming**:
   - No authentication required (it creates the account)
   - Email uniqueness enforced
   - Password validation required
   - Profile can only be claimed once

2. **Journal Claiming**:
   - Authentication required
   - Must be an active institution
   - Cannot claim already-owned journals
   - Atomic database transactions

---

## Related Documentation

- [ACCOUNT_CLAIMING.md](./ACCOUNT_CLAIMING.md) - Detailed account claiming docs
- [JOURNAL_CLAIMING.md](./JOURNAL_CLAIMING.md) - Detailed journal claiming docs
- [AUTH_IMPLEMENTATION.md](../frontend/docs/AUTH_IMPLEMENTATION.md) - Authentication system
- [PUBLICATIONS_API.md](./PUBLICATIONS_API.md) - Managing publications
- [JOURNALS_API.md](./JOURNALS_API.md) - Journal CRUD operations
