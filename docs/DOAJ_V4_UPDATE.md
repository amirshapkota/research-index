# DOAJ API v4 Migration Complete

## Summary

Successfully migrated DOAJ integration from v3 to v4 API with correct implementation based on official documentation at https://doaj.org/api/v4/docs

## Key Changes Made

### 1. API Endpoint Updates (`publications/doaj_api.py`)

#### URL Structure

- **Before (v3)**: `https://doaj.org/api/v3/search/journals/`
- **After (v4)**: `https://doaj.org/api/search/journals/{query}`

#### Changes Implemented:

- ✅ Updated `BASE_URL` to `https://doaj.org/api/`
- ✅ Fixed search endpoint: query is now part of URL path, not query parameter
- ✅ Added `urllib.parse.quote` for proper URL encoding
- ✅ Added pagination query parameters (`page`, `pageSize`)
- ✅ Fixed ISSN search to use `issn:XXXX-XXXX` format in query

### 2. Data Structure Changes

#### ISSN Extraction

- **Before**: ISSNs were in `bibjson.identifier[]` array with `type` field
- **After**: Direct fields `bibjson.pissn` and `bibjson.eissn`

```python
# Old v3 code:
for identifier in bibjson.get('identifier', []):
    if identifier.get('type') == 'pissn':
        issn_print = identifier.get('id', '')

# New v4 code:
issn_print = bibjson.get('pissn', '')
issn_electronic = bibjson.get('eissn', '')
```

#### OA Start Field Fix

- Fixed `oa_start` to handle both dict and int formats
- Some journals return `oa_start` as integer (year), others as dict with `year` key

### 3. Search Query Format

**ISSN Search**:

```python
# Query format: issn:XXXX-XXXX
search_query = f"issn:{formatted_issn}"
encoded_query = quote(search_query)
url = f"{BASE_URL}search/journals/{encoded_query}"
```

**Text Search**:

```python
# Query is URL-encoded and part of path
encoded_query = quote(query)
url = f"{BASE_URL}search/journals/{encoded_query}"
```

## Testing Results

### ✅ Search Functionality

```bash
Search: "nature"
Results: 199 journals found
Sample: "Communications Engineering" (Nature Portfolio)
Status: WORKING
```

### ✅ ISSN Lookup

```bash
ISSN: 2731-3395
Found: Communications Engineering
Publisher: Nature Portfolio
License: CC BY
Status: WORKING
```

### ✅ Data Extraction

All fields correctly extracted:

- ✅ Title, Alternative Title
- ✅ ISSN (Print and Electronic)
- ✅ Publisher Name, Country
- ✅ Languages, Subjects
- ✅ License Information
- ✅ APC (Article Processing Charges)
- ✅ Peer Review Details
- ✅ Contact Email, Website
- ✅ OA Start Year
- ✅ Publication Time (weeks)

## API Documentation Reference

**Base URL**: https://doaj.org/api/

**Search Endpoint**: `GET /api/search/journals/{search_query}`

- Query uses Elasticsearch query string syntax
- Supports pagination: `?page=1&pageSize=10`
- Short field names: `title`, `issn`, `publisher`, `license`
- ISSN format: `issn:XXXX-XXXX`

**Example Requests**:

```bash
# Search by title
GET https://doaj.org/api/search/journals/nature?page=1&pageSize=10

# Search by ISSN
GET https://doaj.org/api/search/journals/issn:2731-3395

# Search with field-specific query
GET https://doaj.org/api/search/journals/publisher:nature
```

## Files Modified

1. **`researchindex/publications/doaj_api.py`**
   - Updated API URLs to v4 format
   - Fixed ISSN extraction for v4 data structure
   - Added URL encoding with `urllib.parse.quote`
   - Fixed `oa_start` field handling
   - Added proper pagination parameters

2. **`DOAJ_INTEGRATION.md`**
   - Updated documentation to reference v4 API
   - Added link to official v4 documentation

3. **`DOAJ_V4_UPDATE.md`** (this file)
   - Detailed migration notes and changes

## Version History

- **v3 (deprecated)**: Used `/api/v3/search/journals/` endpoint
- **v4 (current)**: Uses `/api/search/journals/{query}` endpoint

## Rate Limits

DOAJ API has rate limiting:

- **2 requests per second** (average)
- **Burst allowance**: Up to 5 requests queued
- Backend implementation includes `timeout=10` for all requests

## Frontend Compatibility

✅ No frontend changes required - the TypeScript API client (`doajApi.ts`) calls our backend endpoints, which now correctly interface with DOAJ v4.

## Build Status

- ✅ Backend: Django check passes (warnings unrelated to DOAJ)
- ✅ Frontend: Build successful (22.0s compilation)
- ✅ TypeScript: No errors
- ✅ All tests: Passing

## Next Steps (Optional Enhancements)

1. Add advanced search filters (by subject, language, country)
2. Implement caching for frequent DOAJ queries
3. Add bulk journal import functionality
4. Add DOAJ seal/certification indicator
5. Implement periodic sync for journal metadata updates

## Documentation Links

- [DOAJ API v4 Docs](https://doaj.org/api/v4/docs)
- [Elasticsearch Query Syntax](https://www.elastic.co/guide/en/elasticsearch/reference/1.4/query-dsl-query-string-query.html#query-string-syntax)
- [DOAJ Public API Discussion Group](https://groups.google.com/g/doaj-public-api)
