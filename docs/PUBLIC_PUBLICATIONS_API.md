# Public Publications API

This document describes the public endpoints for accessing publications without authentication.

## Endpoints

### 1. List All Published Publications (Public)

**Endpoint:** `GET /api/publications/public/`

**Authentication:** Not required (AllowAny)

**Description:** Retrieve all published publications with optional filtering and search.

**Query Parameters:**

- `type` (optional): Filter by publication type
  - Values: `journal_article`, `conference_paper`, `book_chapter`, `preprint`, `thesis`, `technical_report`, `poster`, `presentation`, `book`, `review`, `other`
- `topic_branch` (optional): Filter by topic branch ID (integer)
- `author` (optional): Filter by author ID (integer)
- `search` (optional): Search in title, abstract, journal name, or co-authors (string)

**Example Requests:**

```bash
# Get all publications
GET /api/publications/public/

# Filter by publication type
GET /api/publications/public/?type=journal_article

# Filter by topic branch
GET /api/publications/public/?topic_branch=5

# Filter by author
GET /api/publications/public/?author=12

# Search publications
GET /api/publications/public/?search=machine%20learning

# Combine filters
GET /api/publications/public/?type=journal_article&topic_branch=5&search=AI
```

**Response:**

```json
[
  {
    "id": 1,
    "title": "Deep Learning Applications in Medical Imaging",
    "abstract": "This paper explores...",
    "author": {
      "id": 12,
      "name": "Dr. John Smith",
      "institution": "Medical University"
    },
    "publication_type": "journal_article",
    "published_date": "2024-01-15",
    "journal_name": "Journal of Medical AI",
    "doi": "10.1234/example.2024.001",
    "topic_branch": {
      "id": 5,
      "name": "Artificial Intelligence",
      "topic": {
        "id": 2,
        "name": "Computer Science"
      }
    },
    "stats": {
      "citations_count": 25,
      "reads_count": 150
    }
  }
]
```

---

### 2. List Journal Publications (Public)

**Endpoint:** `GET /api/publications/journals/<journal_pk>/publications/`

**Authentication:** Not required (AllowAny)

**Description:** Retrieve all published publications associated with a specific journal through its issues.

**Path Parameters:**

- `journal_pk` (required): Journal ID (integer)

**Query Parameters:**

- `type` (optional): Filter by publication type
- `issue` (optional): Filter by issue ID (integer)
- `search` (optional): Search in title, abstract, or co-authors (string)

**Example Requests:**

```bash
# Get all publications for journal with ID 3
GET /api/publications/journals/3/publications/

# Filter by publication type
GET /api/publications/journals/3/publications/?type=journal_article

# Filter by specific issue
GET /api/publications/journals/3/publications/?issue=8

# Search within journal publications
GET /api/publications/journals/3/publications/?search=neural%20networks

# Combine filters
GET /api/publications/journals/3/publications/?type=review&issue=8
```

**Response:**

```json
[
  {
    "id": 45,
    "title": "Advances in Neural Networks",
    "abstract": "This review article...",
    "author": {
      "id": 8,
      "name": "Dr. Jane Doe",
      "institution": "Tech Institute"
    },
    "publication_type": "review",
    "published_date": "2024-03-10",
    "journal_name": "AI Research Journal",
    "doi": "10.5678/example.2024.045",
    "issue_appearances": [
      {
        "issue": {
          "id": 8,
          "volume": "10",
          "issue_number": "2",
          "journal_id": 3
        },
        "section": "Review Articles",
        "order": 1
      }
    ],
    "stats": {
      "citations_count": 42,
      "reads_count": 320
    }
  }
]
```

**Error Response (404):**

```json
{
  "error": "Journal not found"
}
```

---

## Use Cases

### 1. Public Research Database

Integrate these endpoints into a public-facing website to display all research publications.

### 2. Journal Website

Use the journal-specific endpoint to power a journal's publication listing page.

### 3. Search Portal

Combine filtering and search parameters to create a comprehensive research search interface.

### 4. Topic-Based Browsing

Filter by topic branches to enable users to explore publications by research area.

### 5. Author Profiles

Filter by author ID to display all publications by a specific researcher.

---

## Notes

- Only publications with `is_published=True` are returned
- Both endpoints support pagination (if configured in REST Framework settings)
- Publications are linked to journals through the Issue -> IssueArticle -> Publication relationship
- The journal publications endpoint uses `distinct()` to avoid duplicate entries when a publication appears in multiple issues
- All responses include related data (author, stats, topic_branch) for convenience

---

## Integration with Frontend

### Example: Fetch All Publications

```typescript
const fetchPublications = async (filters?: {
  type?: string;
  topic_branch?: number;
  author?: number;
  search?: string;
}) => {
  const params = new URLSearchParams();
  if (filters?.type) params.append("type", filters.type);
  if (filters?.topic_branch)
    params.append("topic_branch", filters.topic_branch.toString());
  if (filters?.author) params.append("author", filters.author.toString());
  if (filters?.search) params.append("search", filters.search);

  const response = await fetch(
    `/api/publications/public/?${params.toString()}`,
  );
  return response.json();
};
```

### Example: Fetch Journal Publications

```typescript
const fetchJournalPublications = async (
  journalId: number,
  filters?: { type?: string; issue?: number; search?: string },
) => {
  const params = new URLSearchParams();
  if (filters?.type) params.append("type", filters.type);
  if (filters?.issue) params.append("issue", filters.issue.toString());
  if (filters?.search) params.append("search", filters.search);

  const response = await fetch(
    `/api/publications/journals/${journalId}/publications/?${params.toString()}`,
  );
  return response.json();
};
```
