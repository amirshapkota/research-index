# Journal Filtering API Documentation

## Overview

The Journal Listing API (`/api/v1/common/journals/public/`) supports comprehensive filtering to help users find journals based on various criteria.

## Base URL

```
GET /api/publications/journals/public/
```

## Authentication

No authentication required (public endpoint).

## Available Filters

### 1. Access Type

Filter journals by access model.

**Parameters:**
- `access_type` (string): "open_access" or "subscription"
- `open_access` (boolean): true/false

**Examples:**
```bash
# Get only open access journals
curl "http://localhost:8000/api/v1/common/journals/public/?access_type=open_access"

# Get subscription-based journals
curl "http://localhost:8000/api/v1/common/journals/public/?open_access=false"
```

### 2. Category / Discipline

Filter journals by scientific discipline or subject area.

**Parameter:** `category` (string) - Partial match

**Examples:**
```bash
# Get medical journals
curl "http://localhost:8000/api/v1/common/journals/public/?category=medical"

# Get engineering journals
curl "http://localhost:8000/api/v1/common/journals/public/?category=engineering"
```

### 3. Language

Filter journals by publication language.

**Parameter:** `language` (string) - Partial match

**Examples:**
```bash
# Get English language journals
curl "http://localhost:8000/api/v1/common/journals/public/?language=English"

# Get Nepali language journals
curl "http://localhost:8000/api/v1/common/journals/public/?language=Nepali"
```

### 4. License Type

Filter journals by copyright license.

**Parameter:** `license` (string)

**Valid values:**
- `cc_by` - CC BY
- `cc_by_sa` - CC BY-SA
- `cc_by_nc` - CC BY-NC
- `cc_by_nc_sa` - CC BY-NC-SA
- `cc_by_nd` - CC BY-ND
- `cc_by_nc_nd` - CC BY-NC-ND
- `cc0` - CC0 (Public Domain)
- `other` - Other

**Examples:**
```bash
# Get CC BY licensed journals
curl "http://localhost:8000/api/v1/common/journals/public/?license=cc_by"

# Get CC BY-SA licensed journals
curl "http://localhost:8000/api/v1/common/journals/public/?license=cc_by_sa"
```

### 5. Established Year

Filter journals by the year they were established.

**Parameter:** `years` (integer) - Exact match

**Examples:**
```bash
# Get journals established in 2020
curl "http://localhost:8000/api/v1/common/journals/public/?years=2020"

# Get journals established in 1990
curl "http://localhost:8000/api/v1/common/journals/public/?years=1990"
```

### 6. Institution

Filter journals by publishing institution.

**Parameters:**
- `institution` (integer) - Institution ID (exact match)
- `institutions` (string) - Institution name (partial match)

**Examples:**
```bash
# Get journals from institution ID 5
curl "http://localhost:8000/api/v1/common/journals/public/?institution=5"

# Get journals from institutions with "University" in name
curl "http://localhost:8000/api/v1/common/journals/public/?institutions=University"
```

### 7. Country

Filter journals by the country of the publishing institution.

**Parameter:** `country` (string) - Partial match

**Examples:**
```bash
# Get journals from Nepal
curl "http://localhost:8000/api/v1/common/journals/public/?country=Nepal"

# Get journals from USA
curl "http://localhost:8000/api/v1/common/journals/public/?country=USA"
```

### 8. Peer Review

Filter journals by peer review process.

**Parameters:**
- `peer_reviewed` (boolean): true/false - Whether journal is peer-reviewed
- `peer_review` (string): Type of peer review

**Peer Review Types:**
- `single_blind` - Single-blind review
- `double_blind` - Double-blind review
- `open` - Open peer review
- `post_publication` - Post-publication review
- `other` - Other types

**Examples:**
```bash
# Get peer-reviewed journals
curl "http://localhost:8000/api/v1/common/journals/public/?peer_reviewed=true"

# Get double-blind peer review journals
curl "http://localhost:8000/api/v1/common/journals/public/?peer_review=double_blind"
```

### 9. Impact Factor

Filter journals by minimum Impact Factor.

**Parameter:** `impact_factor` (float) - Minimum threshold

**Examples:**
```bash
# Get journals with Impact Factor >= 1.5
curl "http://localhost:8000/api/v1/common/journals/public/?impact_factor=1.5"

# Get journals with Impact Factor >= 3.0
curl "http://localhost:8000/api/v1/common/journals/public/?impact_factor=3.0"
```

### 10. CiteScore

Filter journals by minimum CiteScore.

**Parameter:** `cite_score` (float) - Minimum threshold

**Examples:**
```bash
# Get journals with CiteScore >= 2.0
curl "http://localhost:8000/api/v1/common/journals/public/?cite_score=2.0"

# Get journals with CiteScore >= 5.0
curl "http://localhost:8000/api/v1/common/journals/public/?cite_score=5.0"
```

### 11. Time to First Decision

Filter journals by maximum time to first editorial decision.

**Parameter:** `time_to_decision` (integer) - Maximum weeks

**Examples:**
```bash
# Get journals with decision time <= 4 weeks
curl "http://localhost:8000/api/v1/common/journals/public/?time_to_decision=4"

# Get journals with decision time <= 8 weeks
curl "http://localhost:8000/api/v1/common/journals/public/?time_to_decision=8"
```

### 12. Time to Acceptance

Filter journals by maximum time from submission to acceptance.

**Parameter:** `time_to_acceptance` (integer) - Maximum days

**Examples:**
```bash
# Get journals with acceptance time <= 30 days
curl "http://localhost:8000/api/v1/common/journals/public/?time_to_acceptance=30"

# Get journals with acceptance time <= 60 days
curl "http://localhost:8000/api/v1/common/journals/public/?time_to_acceptance=60"
```

### 13. Search

Full-text search across journal title, description, and publisher name.

**Parameter:** `search` (string) - Search query

**Examples:**
```bash
# Search for "medical" journals
curl "http://localhost:8000/api/v1/common/journals/public/?search=medical"

# Search for "engineering" journals
curl "http://localhost:8000/api/v1/common/journals/public/?search=engineering"
```

## Combining Filters

You can combine multiple filters to narrow down results.

**Examples:**

```bash
# Open access medical journals in Nepal
curl "http://localhost:8000/api/v1/common/journals/public/?access_type=open_access&category=medical&country=Nepal"

# Journals with high impact (IF >= 2.0) and fast review (< 4 weeks)
curl "http://localhost:8000/api/v1/common/journals/public/?impact_factor=2.0&time_to_decision=4"

# English peer-reviewed journals with CC BY license
curl "http://localhost:8000/api/v1/common/journals/public/?language=English&peer_reviewed=true&license=cc_by"

# Search for "science" journals established after 2010 with open access
curl "http://localhost:8000/api/v1/common/journals/public/?search=science&years=2010&access_type=open_access"
```

## Response Format

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/common/journals/public/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Journal of Medical Sciences",
      "short_title": "JMS",
      "issn": "1234-5678",
      "e_issn": "8765-4321",
      "description": "Leading medical journal...",
      "publisher_name": "Medical Publishers Inc.",
      "language": "English",
      "established_year": 2010,
      "is_open_access": true,
      "peer_reviewed": true,
      "institution": {
        "id": 5,
        "name": "Nepal Medical Institute",
        "country": "Nepal"
      },
      "stats": {
        "impact_factor": "2.45",
        "cite_score": "3.12",
        "total_articles": 250,
        "total_issues": 20
      }
    }
  ]
}
```

## Filter Summary

| Filter | Parameter | Type | Description |
|--------|-----------|------|-------------|
| Access Type | `access_type` | string | open_access, subscription |
| Open Access | `open_access` | boolean | true/false |
| Category | `category` | string | Discipline/subject area |
| Language | `language` | string | Publication language |
| License | `license` | string | cc_by, cc_by_sa, etc. |
| Year | `years` | integer | Established year |
| Institution (ID) | `institution` | integer | Institution ID |
| Institution (Name) | `institutions` | string | Institution name |
| Country | `country` | string | Publisher country |
| Peer Reviewed | `peer_reviewed` | boolean | true/false |
| Peer Review Type | `peer_review` | string | single_blind, double_blind, open |
| Impact Factor | `impact_factor` | float | Minimum IF |
| CiteScore | `cite_score` | float | Minimum CiteScore |
| Decision Time | `time_to_decision` | integer | Max weeks to decision |
| Acceptance Time | `time_to_acceptance` | integer | Max days to acceptance |
| Search | `search` | string | Text search |

## Notes

- All text filters (category, language, institutions, country, peer_review) support **partial matching** (case-insensitive)
- Numeric filters (impact_factor, cite_score) filter for **minimum values** (>=)
- Time filters (time_to_decision, time_to_acceptance) filter for **maximum values** (<=)
- Multiple filters are combined with **AND** logic
- Empty or invalid filter values are ignored
- The API supports pagination (use `?page=2` for next page)

## Testing

To view all available filters in Swagger UI:
```
http://localhost:8000/api/schema/swagger-ui/
```

Look for the "Public Journals" section → "List All Journals (Public)" endpoint.

## Implementation Status

✅ All 15 filter parameters implemented and tested
✅ OpenAPI/Swagger documentation complete
✅ Partial matching for text fields
✅ Range filtering for numeric fields
✅ Combine filter support
✅ Performance optimized with select_related and prefetch_related

## Support

For issues or questions, contact the development team.
