# Journals & Issues API Documentation

This document provides comprehensive information about the Journals and Issues endpoints for institutions.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Journal Endpoints](#journal-endpoints)
- [Editorial Board Endpoints](#editorial-board-endpoints)
- [Issue Endpoints](#issue-endpoints)
- [Models Reference](#models-reference)
- [Examples](#examples)

## Overview

The Journals API allows institutions to manage their academic journals, editorial boards, issues, and related content. This includes comprehensive information sections, statistics tracking, and article management.

**Base URL**: `/api/publications/journals/`

## Authentication

All journal endpoints require authentication using JWT tokens. Only institution users can create and manage journals.

**Headers Required**:

```
Authorization: Bearer <access_token>
```

---

## Journal Endpoints

### 1. List My Journals

**GET** `/api/publications/journals/`

List all journals owned by the authenticated institution.

**Response** (200 OK):

```json
[
  {
    "id": 1,
    "title": "International Journal of Advanced Research",
    "short_title": "IJAR",
    "issn": "1234-5678",
    "e_issn": "9876-5432",
    "description": "Leading journal in advanced research",
    "scope": "Covers all aspects of advanced scientific research",
    "institution_id": 1,
    "institution_name": "Harvard University",
    "frequency": "quarterly",
    "frequency_display": "Quarterly",
    "established_year": 2020,
    "is_open_access": true,
    "peer_reviewed": true,
    "is_active": true,
    "cover_image_url": "http://localhost:8000/media/journals/covers/journal1.jpg",
    "stats": {
      "impact_factor": 3.45,
      "cite_score": 4.2,
      "h_index": 25,
      "acceptance_rate": 35.5,
      "total_articles": 150,
      "total_issues": 12,
      "recommendations": 89
    },
    "editorial_board_count": 15,
    "issues_count": 12,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 2. Create Journal

**POST** `/api/publications/journals/`

Create a new journal with full information sections and editorial board.

**Request Body**:

```json
{
  "title": "International Journal of Advanced Research",
  "short_title": "IJAR",
  "issn": "1234-5678",
  "e_issn": "9876-5432",
  "description": "Leading journal in advanced research",
  "scope": "Covers all aspects of advanced scientific research",
  "publisher_name": "Academic Press",
  "publisher_location": "New York, USA",
  "frequency": "quarterly",
  "established_year": 2020,
  "about_journal": "Comprehensive information about the journal's mission, vision, and scope...",
  "ethics_policies": "Our ethical guidelines include plagiarism policies, conflict of interest...",
  "writing_formatting": "Authors should follow APA 7th edition for citations. Manuscripts should be...",
  "submitting_manuscript": "Submit manuscripts via our online submission system. Include cover letter...",
  "help_support": "For technical support, contact support@journal.com. For editorial queries...",
  "contact_email": "editor@journal.com",
  "contact_phone": "+1-234-567-8900",
  "contact_address": "123 Academic Street, Boston, MA 02115",
  "website_url": "https://journal.example.com",
  "is_open_access": true,
  "peer_reviewed": true,
  "editorial_board_data": [
    {
      "name": "Dr. John Smith",
      "role": "editor_in_chief",
      "title": "Professor",
      "affiliation": "Harvard University",
      "email": "john.smith@harvard.edu",
      "bio": "Professor of Advanced Sciences with 20 years of experience...",
      "expertise": "Quantum Physics, Machine Learning",
      "orcid": "0000-0001-2345-6789",
      "order": 1
    },
    {
      "name": "Dr. Jane Doe",
      "role": "associate_editor",
      "affiliation": "MIT",
      "email": "jane.doe@mit.edu",
      "order": 2
    }
  ]
}
```

**Note**: `cover_image` should be uploaded as multipart/form-data when including an image file.

**Response** (201 Created):

```json
{
  "message": "Journal created successfully",
  "journal": {
    "id": 1,
    "title": "International Journal of Advanced Research",
    "institution": {
      "id": 1,
      "institution_name": "Harvard University"
    },
    "editorial_board": [
      {
        "id": 1,
        "name": "Dr. John Smith",
        "role": "editor_in_chief",
        "role_display": "Editor-in-Chief",
        "title": "Professor",
        "affiliation": "Harvard University",
        "email": "john.smith@harvard.edu",
        "bio": "Professor of Advanced Sciences...",
        "expertise": "Quantum Physics, Machine Learning",
        "orcid": "0000-0001-2345-6789",
        "photo_url": null,
        "order": 1
      }
    ],
    "stats": {
      "impact_factor": 0.0,
      "cite_score": 0.0,
      "h_index": 0,
      "acceptance_rate": 0.0,
      "total_articles": 0,
      "total_issues": 0
    }
  }
}
```

---

### 3. Get Journal Details

**GET** `/api/publications/journals/{id}/`

Retrieve complete information about a specific journal.

**Response** (200 OK):

```json
{
  "id": 1,
  "title": "International Journal of Advanced Research",
  "short_title": "IJAR",
  "issn": "1234-5678",
  "e_issn": "9876-5432",
  "description": "Leading journal in advanced research",
  "scope": "Covers all aspects of advanced scientific research",
  "cover_image_url": "http://localhost:8000/media/journals/covers/journal1.jpg",
  "institution": {
    "id": 1,
    "institution_name": "Harvard University",
    "email": "info@harvard.edu"
  },
  "publisher_name": "Academic Press",
  "publisher_location": "New York, USA",
  "frequency": "quarterly",
  "frequency_display": "Quarterly",
  "established_year": 2020,
  "about_journal": "Comprehensive information...",
  "ethics_policies": "Our ethical guidelines...",
  "writing_formatting": "Authors should follow...",
  "submitting_manuscript": "Submit manuscripts via...",
  "help_support": "For technical support...",
  "contact_email": "editor@journal.com",
  "contact_phone": "+1-234-567-8900",
  "contact_address": "123 Academic Street, Boston, MA 02115",
  "website_url": "https://journal.example.com",
  "is_open_access": true,
  "peer_reviewed": true,
  "is_active": true,
  "editorial_board": [
    {
      "id": 1,
      "name": "Dr. John Smith",
      "role": "editor_in_chief",
      "role_display": "Editor-in-Chief",
      "title": "Professor",
      "affiliation": "Harvard University",
      "email": "john.smith@harvard.edu",
      "bio": "Professor of Advanced Sciences...",
      "expertise": "Quantum Physics, Machine Learning",
      "orcid": "0000-0001-2345-6789",
      "google_scholar_profile": "https://scholar.google.com/...",
      "photo_url": "http://localhost:8000/media/editorial/john_smith.jpg",
      "order": 1,
      "is_active": true
    }
  ],
  "stats": {
    "impact_factor": 3.45,
    "cite_score": 4.2,
    "h_index": 25,
    "sjr_score": 1.8,
    "acceptance_rate": 35.5,
    "average_review_time": 45,
    "total_articles": 150,
    "total_issues": 12,
    "total_citations": 2340,
    "total_reads": 15678,
    "recommendations": 89,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:20:00Z"
}
```

---

### 4. Update Journal

**PATCH** `/api/publications/journals/{id}/`

Partially update journal information.

**Request Body** (any fields):

```json
{
  "description": "Updated description",
  "about_journal": "Updated about section",
  "is_open_access": false,
  "editorial_board_data": [
    {
      "id": 1,
      "name": "Dr. John Smith Updated",
      "role": "editor_in_chief"
    },
    {
      "name": "Dr. New Editor",
      "role": "associate_editor",
      "affiliation": "Stanford University",
      "email": "new@stanford.edu",
      "order": 3
    }
  ]
}
```

**Response** (200 OK):

```json
{
  "message": "Journal updated successfully",
  "journal": {
    /* full journal details */
  }
}
```

---

### 5. Delete Journal

**DELETE** `/api/publications/journals/{id}/`

Permanently delete a journal and all associated data.

**Response** (200 OK):

```json
{
  "message": "Journal \"International Journal of Advanced Research\" has been deleted successfully"
}
```

---

## Journal Statistics Endpoints

### 6. Get Journal Statistics

**GET** `/api/publications/journals/{id}/stats/`

Retrieve detailed statistics for a journal.

**Response** (200 OK):

```json
{
  "impact_factor": 3.45,
  "cite_score": 4.2,
  "h_index": 25,
  "sjr_score": 1.8,
  "acceptance_rate": 35.5,
  "average_review_time": 45,
  "total_articles": 150,
  "total_issues": 12,
  "total_citations": 2340,
  "total_reads": 15678,
  "recommendations": 89,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

---

### 7. Update Journal Statistics

**PATCH** `/api/publications/journals/{id}/stats/`

Update journal statistics.

**Request Body**:

```json
{
  "impact_factor": 3.55,
  "cite_score": 4.3,
  "h_index": 26,
  "acceptance_rate": 34.0
}
```

**Response** (200 OK):

```json
{
  "message": "Stats updated successfully",
  "stats": {
    /* updated stats */
  }
}
```

---

## Editorial Board Endpoints

### 8. List Editorial Board

**GET** `/api/publications/journals/{journal_id}/editorial-board/`

Get all editorial board members for a journal.

**Response** (200 OK):

```json
[
  {
    "id": 1,
    "name": "Dr. John Smith",
    "role": "editor_in_chief",
    "role_display": "Editor-in-Chief",
    "title": "Professor",
    "affiliation": "Harvard University",
    "email": "john.smith@harvard.edu",
    "bio": "Professor of Advanced Sciences with 20 years of experience...",
    "expertise": "Quantum Physics, Machine Learning",
    "photo_url": "http://localhost:8000/media/editorial/john_smith.jpg",
    "orcid": "0000-0001-2345-6789",
    "google_scholar_profile": "https://scholar.google.com/...",
    "order": 1,
    "is_active": true,
    "joined_date": "2020-01-15",
    "left_date": null
  }
]
```

---

### 9. Add Editorial Board Member

**POST** `/api/publications/journals/{journal_id}/editorial-board/`

Add a new editorial board member.

**Request Body**:

```json
{
  "name": "Dr. Sarah Johnson",
  "role": "managing_editor",
  "title": "Associate Professor",
  "affiliation": "Stanford University",
  "email": "sarah.j@stanford.edu",
  "bio": "Expert in computational biology...",
  "expertise": "Bioinformatics, Computational Biology",
  "orcid": "0000-0002-3456-7890",
  "order": 4
}
```

**Response** (201 Created):

```json
{
  "message": "Editorial board member added successfully",
  "member": {
    /* member details */
  }
}
```

---

## Issue Endpoints

### 10. List Journal Issues

**GET** `/api/publications/journals/{journal_id}/issues/`

List all issues for a specific journal.

**Response** (200 OK):

```json
[
  {
    "id": 1,
    "volume": 5,
    "issue_number": 2,
    "title": "Special Issue: Artificial Intelligence",
    "publication_date": "2024-06-01",
    "submission_deadline": "2024-04-15",
    "doi": "10.1234/journal.2024.5.2",
    "status": "published",
    "status_display": "Published",
    "is_special_issue": true,
    "cover_image_url": "http://localhost:8000/media/issues/covers/vol5_iss2.jpg",
    "article_count": 15,
    "created_at": "2024-01-10T09:00:00Z"
  }
]
```

---

### 11. Create Issue

**POST** `/api/publications/journals/{journal_id}/issues/`

Create a new issue for the journal.

**Request Body**:

```json
{
  "volume": 5,
  "issue_number": 3,
  "title": "Summer 2024 Edition",
  "publication_date": "2024-09-01",
  "submission_deadline": "2024-07-15",
  "doi": "10.1234/journal.2024.5.3",
  "editorial_note": "This issue focuses on emerging trends in AI...",
  "guest_editors": "Dr. Alice Wang, Dr. Bob Chen",
  "status": "upcoming",
  "is_special_issue": false
}
```

**Response** (201 Created):

```json
{
  "message": "Issue created successfully",
  "issue": {
    /* full issue details */
  }
}
```

---

### 12. Get Issue Details

**GET** `/api/publications/journals/{journal_id}/issues/{id}/`

Retrieve complete information about a specific issue including all articles.

**Response** (200 OK):

```json
{
  "id": 1,
  "journal_id": 1,
  "journal_title": "International Journal of Advanced Research",
  "volume": 5,
  "issue_number": 2,
  "title": "Special Issue: Artificial Intelligence",
  "publication_date": "2024-06-01",
  "submission_deadline": "2024-04-15",
  "doi": "10.1234/journal.2024.5.2",
  "editorial_note": "This special issue...",
  "guest_editors": "Dr. Alice Wang, Dr. Bob Chen",
  "status": "published",
  "status_display": "Published",
  "is_special_issue": true,
  "cover_image_url": "http://localhost:8000/media/issues/covers/vol5_iss2.jpg",
  "articles": [
    {
      "id": 1,
      "publication_id": 45,
      "article_title": "Deep Learning Applications in Healthcare",
      "article_authors": "Dr. Smith, Dr. Johnson",
      "article_doi": "10.1234/article.2024.001",
      "section": "Research Articles",
      "order": 1
    },
    {
      "id": 2,
      "publication_id": 46,
      "article_title": "Neural Networks for Climate Prediction",
      "article_authors": "Dr. Lee, Dr. Wang",
      "article_doi": "10.1234/article.2024.002",
      "section": "Research Articles",
      "order": 2
    }
  ],
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-06-01T10:00:00Z"
}
```

---

### 13. Update Issue

**PATCH** `/api/publications/journals/{journal_id}/issues/{id}/`

Update issue information.

**Request Body**:

```json
{
  "status": "published",
  "publication_date": "2024-09-15"
}
```

**Response** (200 OK):

```json
{
  "message": "Issue updated successfully",
  "issue": {
    /* updated issue details */
  }
}
```

---

### 14. Delete Issue

**DELETE** `/api/publications/journals/{journal_id}/issues/{id}/`

Permanently delete an issue.

**Response** (200 OK):

```json
{
  "message": "Issue \"Vol. 5, Issue 2\" has been deleted successfully"
}
```

---

### 15. Add Article to Issue

**POST** `/api/publications/journals/{journal_id}/issues/{issue_id}/articles/add/`

Add an existing publication to a journal issue.

**Request Body**:

```json
{
  "publication_id": 45,
  "section": "Research Articles",
  "order": 1
}
```

**Response** (201 Created):

```json
{
  "message": "Article added to issue successfully",
  "article": {
    "id": 1,
    "publication_id": 45,
    "order": 1,
    "section": "Research Articles"
  }
}
```

---

## Models Reference

### Journal Model

| Field                 | Type       | Description                                      |
| --------------------- | ---------- | ------------------------------------------------ |
| id                    | Integer    | Unique identifier                                |
| institution           | ForeignKey | Institution that owns the journal                |
| title                 | String     | Full journal title                               |
| short_title           | String     | Abbreviated title                                |
| issn                  | String     | Print ISSN                                       |
| e_issn                | String     | Electronic ISSN                                  |
| description           | Text       | Brief description                                |
| scope                 | Text       | Academic scope and coverage                      |
| cover_image           | Image      | Journal cover image                              |
| publisher_name        | String     | Publisher name                                   |
| publisher_location    | String     | Publisher location                               |
| frequency             | Choice     | Publication frequency (monthly, quarterly, etc.) |
| established_year      | Integer    | Year established                                 |
| about_journal         | Text       | Comprehensive about section                      |
| ethics_policies       | Text       | Editorial ethics and policies                    |
| writing_formatting    | Text       | Author guidelines for formatting                 |
| submitting_manuscript | Text       | Submission instructions                          |
| help_support          | Text       | Help and support information                     |
| contact_email         | Email      | Editorial contact email                          |
| contact_phone         | String     | Contact phone number                             |
| contact_address       | Text       | Physical address                                 |
| website_url           | URL        | Journal website                                  |
| is_open_access        | Boolean    | Open access status                               |
| peer_reviewed         | Boolean    | Peer review status                               |
| is_active             | Boolean    | Active status                                    |

### Editorial Board Member Model

| Field                  | Type       | Description                                              |
| ---------------------- | ---------- | -------------------------------------------------------- |
| id                     | Integer    | Unique identifier                                        |
| journal                | ForeignKey | Associated journal                                       |
| name                   | String     | Full name                                                |
| role                   | Choice     | Editorial role (editor_in_chief, associate_editor, etc.) |
| title                  | String     | Academic title                                           |
| affiliation            | String     | Institution affiliation                                  |
| email                  | Email      | Contact email                                            |
| bio                    | Text       | Biography                                                |
| expertise              | Text       | Areas of expertise                                       |
| photo                  | Image      | Profile photo                                            |
| orcid                  | String     | ORCID identifier                                         |
| google_scholar_profile | URL        | Google Scholar URL                                       |
| order                  | Integer    | Display order                                            |
| is_active              | Boolean    | Active status                                            |
| joined_date            | Date       | Date joined board                                        |
| left_date              | Date       | Date left board                                          |

### Journal Stats Model

| Field               | Type    | Description                |
| ------------------- | ------- | -------------------------- |
| impact_factor       | Decimal | Impact factor              |
| cite_score          | Decimal | CiteScore metric           |
| h_index             | Integer | h-index                    |
| sjr_score           | Decimal | SCImago Journal Rank       |
| acceptance_rate     | Decimal | Acceptance rate (%)        |
| average_review_time | Integer | Average review time (days) |
| total_articles      | Integer | Total published articles   |
| total_issues        | Integer | Total published issues     |
| total_citations     | Integer | Total citations            |
| total_reads         | Integer | Total article reads        |
| recommendations     | Integer | Recommendations count      |

### Issue Model

| Field               | Type       | Description                                            |
| ------------------- | ---------- | ------------------------------------------------------ |
| id                  | Integer    | Unique identifier                                      |
| journal             | ForeignKey | Associated journal                                     |
| volume              | Integer    | Volume number                                          |
| issue_number        | Integer    | Issue number                                           |
| title               | String     | Issue title                                            |
| cover_image         | Image      | Issue cover image                                      |
| publication_date    | Date       | Publication date                                       |
| submission_deadline | Date       | Manuscript submission deadline                         |
| doi                 | String     | Digital Object Identifier                              |
| editorial_note      | Text       | Editorial note                                         |
| guest_editors       | String     | Guest editors (if applicable)                          |
| status              | Choice     | Status (draft, upcoming, current, published, archived) |
| is_special_issue    | Boolean    | Special issue flag                                     |

---

## Error Responses

### 400 Bad Request

```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "error": "Journal not found"
}
```

---

## Examples

### Complete Journal Creation Example

```bash
curl -X POST http://localhost:8000/api/publications/journals/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Journal of Advanced Computing",
    "short_title": "JAC",
    "issn": "2234-5678",
    "e_issn": "2234-5679",
    "description": "Premier journal in computing research",
    "scope": "Covers AI, ML, Cloud Computing, and more",
    "publisher_name": "Tech Publishing",
    "frequency": "quarterly",
    "established_year": 2022,
    "about_journal": "We publish cutting-edge research...",
    "ethics_policies": "All manuscripts undergo rigorous review...",
    "writing_formatting": "Follow IEEE citation style...",
    "submitting_manuscript": "Submit via our portal...",
    "help_support": "Contact support@journal.com...",
    "contact_email": "editor@journal.com",
    "is_open_access": true,
    "peer_reviewed": true,
    "editorial_board_data": [
      {
        "name": "Dr. Alan Turing",
        "role": "editor_in_chief",
        "affiliation": "Cambridge University",
        "email": "turing@cambridge.edu",
        "expertise": "Computer Science, AI",
        "order": 1
      }
    ]
  }'
```

### Create Issue and Add Articles Example

```bash
# 1. Create Issue
curl -X POST http://localhost:8000/api/publications/journals/1/issues/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "volume": 1,
    "issue_number": 1,
    "title": "Inaugural Issue",
    "publication_date": "2024-03-01",
    "submission_deadline": "2024-01-15",
    "status": "upcoming"
  }'

# 2. Add Article to Issue
curl -X POST http://localhost:8000/api/publications/journals/1/issues/1/articles/add/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publication_id": 10,
    "section": "Research Articles",
    "order": 1
  }'
```

---

## Workflow Example

1. **Institution creates journal** → `POST /journals/`
2. **Add editorial board members** → Included in creation or added later
3. **Update journal statistics** → `PATCH /journals/{id}/stats/`
4. **Create first issue** → `POST /journals/{id}/issues/`
5. **Authors submit articles** → Handled via publications API
6. **Add approved articles to issue** → `POST /journals/{id}/issues/{issue_id}/articles/add/`
7. **Publish issue** → `PATCH /journals/{id}/issues/{issue_id}/` with `status: published`
8. **Track metrics** → Stats automatically updated

---

## Field Constraints

### Journal Constraints

- `title`: Max 500 characters
- `issn`: Unique, max 20 characters
- `frequency`: One of: monthly, bimonthly, quarterly, semiannual, annual, irregular
- `established_year`: Integer
- `contact_email`: Valid email format

### Editorial Board Constraints

- `role`: One of: editor_in_chief, associate_editor, managing_editor, section_editor, editorial_board_member, advisory_board_member, guest_editor, reviewer
- `order`: Positive integer for display ordering
- `orcid`: Format: 0000-0000-0000-0000

### Issue Constraints

- `volume` and `issue_number`: Unique together per journal
- `status`: One of: draft, upcoming, current, published, archived
- `publication_date`: Date format (YYYY-MM-DD)

### Statistics Constraints

- `impact_factor`, `cite_score`, `sjr_score`: Decimal (max 2 places)
- `acceptance_rate`: 0-100 (percentage)
- `average_review_time`: Integer (days)
- All counts: Non-negative integers

---

## Notes

1. **File Uploads**: Use `multipart/form-data` for cover images and editorial photos
2. **Permissions**: Only institution users can manage their own journals
3. **Stats Auto-Creation**: JournalStats are automatically created when a journal is created
4. **Cascading Deletes**: Deleting a journal deletes all associated issues, editorial board members, and stats
5. **Unique Constraints**: ISSN must be unique, Volume+Issue must be unique per journal
6. **Editorial Board**: Can be managed during journal creation or separately
7. **Issue Status Workflow**: draft → upcoming → current → published → archived
8. **Article Linking**: Only published articles can be added to issues

---

For additional support or questions, please refer to the main API documentation or contact the development team.
