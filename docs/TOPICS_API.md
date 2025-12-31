# Topics & Topic Branches API Documentation

## Overview

The Topics API provides a hierarchical categorization system for organizing publications. Topics are top-level categories (e.g., "Computer Science"), and Topic Branches are subcategories (e.g., "Machine Learning", "Artificial Intelligence"). Authors can tag their publications with specific topic branches for better discoverability.

**Base URL**: `/api/publications/topics/`

---

## Authentication

- **Public Endpoints**: List topics, list branches, browse publications by topic
- **Authenticated Endpoints**: All endpoints require authentication
- **Admin Endpoints**: Create/Update/Delete topics and branches (requires admin/staff permissions)

---

## Endpoints

### Topics

#### 1. List All Topics

**GET** `/api/publications/topics/`

Get all active topics with branch and publication counts.

**Response** (200 OK):

```json
[
  {
    "id": 1,
    "name": "Computer Science",
    "slug": "computer-science",
    "description": "Research in computing, algorithms, AI, and related fields",
    "icon": "💻",
    "is_active": true,
    "order": 1,
    "branches_count": 12,
    "publications_count": 145,
    "created_at": "2024-01-15T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Biology",
    "slug": "biology",
    "description": "Life sciences and biological research",
    "icon": "🧬",
    "is_active": true,
    "order": 2,
    "branches_count": 8,
    "publications_count": 98,
    "created_at": "2024-01-15T10:05:00Z"
  }
]
```

---

#### 2. Create Topic

**POST** `/api/publications/topics/`

Create a new topic (admin only).

**Request Headers**:

```
Authorization: Bearer <admin_access_token>
```

**Request Body**:

```json
{
  "name": "Physics",
  "slug": "physics",
  "description": "Research in physics and related fields",
  "icon": "⚛️",
  "is_active": true,
  "order": 3
}
```

**Response** (201 Created):

```json
{
  "message": "Topic created successfully",
  "topic": {
    "id": 3,
    "name": "Physics",
    "slug": "physics",
    "description": "Research in physics and related fields",
    "icon": "⚛️",
    "is_active": true,
    "order": 3,
    "branches": [],
    "branches_count": 0,
    "publications_count": 0,
    "created_at": "2024-01-20T14:30:00Z",
    "updated_at": "2024-01-20T14:30:00Z"
  }
}
```

**Error Response** (403 Forbidden):

```json
{
  "error": "Only administrators can create topics"
}
```

---

#### 3. Get Topic Details

**GET** `/api/publications/topics/{id}/`

Retrieve complete topic information including all branches.

**Response** (200 OK):

```json
{
  "id": 1,
  "name": "Computer Science",
  "slug": "computer-science",
  "description": "Research in computing, algorithms, AI, and related fields",
  "icon": "💻",
  "is_active": true,
  "order": 1,
  "branches": [
    {
      "id": 1,
      "name": "Machine Learning",
      "slug": "machine-learning",
      "description": "ML algorithms, neural networks, deep learning",
      "is_active": true,
      "order": 1,
      "publications_count": 45
    },
    {
      "id": 2,
      "name": "Artificial Intelligence",
      "slug": "artificial-intelligence",
      "description": "AI research, expert systems, NLP",
      "is_active": true,
      "order": 2,
      "publications_count": 38
    },
    {
      "id": 3,
      "name": "Computer Vision",
      "slug": "computer-vision",
      "description": "Image processing, object detection, recognition",
      "is_active": true,
      "order": 3,
      "publications_count": 29
    }
  ],
  "branches_count": 12,
  "publications_count": 145,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-18T16:20:00Z"
}
```

---

#### 4. Update Topic

**PATCH** `/api/publications/topics/{id}/`

Update topic information (admin only).

**Request Body** (partial update):

```json
{
  "description": "Updated description for computer science",
  "icon": "🖥️",
  "order": 0
}
```

**Response** (200 OK):

```json
{
  "message": "Topic updated successfully",
  "topic": {
    /* updated topic details */
  }
}
```

---

#### 5. Delete Topic

**DELETE** `/api/publications/topics/{id}/`

Delete a topic (admin only). This will also delete all associated branches.

**Response** (200 OK):

```json
{
  "message": "Topic \"Computer Science\" has been deleted successfully"
}
```

---

### Topic Branches

#### 6. List Topic Branches

**GET** `/api/publications/topics/{topic_id}/branches/`

Get all branches for a specific topic.

**Response** (200 OK):

```json
[
  {
    "id": 1,
    "name": "Machine Learning",
    "slug": "machine-learning",
    "description": "ML algorithms, neural networks, deep learning",
    "is_active": true,
    "order": 1,
    "publications_count": 45
  },
  {
    "id": 2,
    "name": "Artificial Intelligence",
    "slug": "artificial-intelligence",
    "description": "AI research, expert systems, NLP",
    "is_active": true,
    "order": 2,
    "publications_count": 38
  }
]
```

---

#### 7. Create Topic Branch

**POST** `/api/publications/topics/{topic_id}/branches/`

Create a new branch under a topic (admin only).

**Request Body**:

```json
{
  "name": "Quantum Computing",
  "slug": "quantum-computing",
  "description": "Quantum algorithms, quantum cryptography, quantum information",
  "is_active": true,
  "order": 10
}
```

**Response** (201 Created):

```json
{
  "message": "Topic branch created successfully",
  "branch": {
    "id": 13,
    "topic_id": 1,
    "topic_name": "Computer Science",
    "name": "Quantum Computing",
    "slug": "quantum-computing",
    "description": "Quantum algorithms, quantum cryptography, quantum information",
    "is_active": true,
    "order": 10,
    "publications_count": 0,
    "created_at": "2024-01-20T15:00:00Z",
    "updated_at": "2024-01-20T15:00:00Z"
  }
}
```

---

#### 8. Get Branch Details

**GET** `/api/publications/topics/{topic_id}/branches/{id}/`

Retrieve complete information about a topic branch.

**Response** (200 OK):

```json
{
  "id": 1,
  "topic_id": 1,
  "topic_name": "Computer Science",
  "name": "Machine Learning",
  "slug": "machine-learning",
  "description": "ML algorithms, neural networks, deep learning",
  "is_active": true,
  "order": 1,
  "publications_count": 45,
  "created_at": "2024-01-15T10:10:00Z",
  "updated_at": "2024-01-18T11:00:00Z"
}
```

---

#### 9. Update Branch

**PATCH** `/api/publications/topics/{topic_id}/branches/{id}/`

Update topic branch information (admin only).

**Request Body**:

```json
{
  "description": "Updated description with more details",
  "order": 5
}
```

**Response** (200 OK):

```json
{
  "message": "Topic branch updated successfully",
  "branch": {
    /* updated branch details */
  }
}
```

---

#### 10. Delete Branch

**DELETE** `/api/publications/topics/{topic_id}/branches/{id}/`

Delete a topic branch (admin only).

**Response** (200 OK):

```json
{
  "message": "Topic branch \"Machine Learning\" has been deleted successfully"
}
```

---

### Publications by Topic

#### 11. Browse Publications by Topic Branch

**GET** `/api/publications/topics/{topic_id}/branches/{branch_id}/publications/`

List all published publications under a specific topic branch.

**Response** (200 OK):

```json
[
  {
    "id": 15,
    "title": "Deep Learning for Image Classification",
    "author_name": "Dr. Sarah Johnson",
    "author_orcid": "0000-0001-2345-6789",
    "publication_type": "journal_article",
    "publication_type_display": "Journal Article",
    "doi": "10.1234/example.2024.001",
    "published_date": "2024-03-15",
    "journal_name": "Journal of Machine Learning Research",
    "abstract": "This paper presents a novel approach to image classification using deep neural networks...",
    "pdf_url": "http://localhost:8000/media/publications/pdfs/paper.pdf",
    "is_published": true,
    "topic_branch_id": 1,
    "topic_branch_name": "Machine Learning",
    "topic_id": 1,
    "topic_name": "Computer Science",
    "stats": {
      "citations_count": 23,
      "reads_count": 456,
      "downloads_count": 189,
      "recommendations_count": 12,
      "altmetric_score": 15.5
    },
    "mesh_terms_count": 5,
    "citations_count": 23,
    "references_count": 35,
    "created_at": "2024-03-10T09:00:00Z",
    "updated_at": "2024-03-15T14:30:00Z"
  }
]
```

---

## Using Topics with Publications

### When Creating a Publication

Include the `topic_branch` field when creating a publication:

**POST** `/api/publications/`

```json
{
  "title": "Neural Networks for Climate Prediction",
  "abstract": "This research explores the use of neural networks...",
  "publication_type": "journal_article",
  "topic_branch": 1,
  "doi": "10.1234/climate.2024.005",
  "published_date": "2024-04-01"
}
```

### When Updating a Publication

Update the topic branch assignment:

**PATCH** `/api/publications/{id}/`

```json
{
  "topic_branch": 2
}
```

### When Viewing Publications

The topic information is automatically included in publication responses:

```json
{
  "id": 25,
  "title": "Publication Title",
  "topic_branch_id": 1,
  "topic_branch_name": "Machine Learning",
  "topic_id": 1,
  "topic_name": "Computer Science",
  "topic_branch": {
    "id": 1,
    "topic_id": 1,
    "topic_name": "Computer Science",
    "name": "Machine Learning",
    "slug": "machine-learning",
    "publications_count": 45
  }
}
```

---

## Models Reference

### Topic Model

| Field       | Type           | Description                   |
| ----------- | -------------- | ----------------------------- |
| id          | Integer        | Unique identifier             |
| name        | String(200)    | Topic name (unique)           |
| slug        | SlugField(200) | URL-friendly version (unique) |
| description | Text           | Description of the topic      |
| icon        | String(100)    | Icon class or emoji           |
| is_active   | Boolean        | Whether topic is active       |
| order       | Integer        | Display order (default: 0)    |
| created_at  | DateTime       | Creation timestamp            |
| updated_at  | DateTime       | Last update timestamp         |

### TopicBranch Model

| Field       | Type           | Description                             |
| ----------- | -------------- | --------------------------------------- |
| id          | Integer        | Unique identifier                       |
| topic       | ForeignKey     | Parent topic                            |
| name        | String(200)    | Branch name                             |
| slug        | SlugField(200) | URL-friendly version                    |
| description | Text           | Description of the branch               |
| is_active   | Boolean        | Whether branch is active                |
| order       | Integer        | Display order within topic (default: 0) |
| created_at  | DateTime       | Creation timestamp                      |
| updated_at  | DateTime       | Last update timestamp                   |

**Unique Constraint**: (topic, slug)

---

## Workflow Examples

### 1. Admin Sets Up Topics

```bash
# Create topic
POST /api/publications/topics/
{
  "name": "Computer Science",
  "slug": "computer-science",
  "description": "Computing research",
  "icon": "💻",
  "order": 1
}

# Create branches
POST /api/publications/topics/1/branches/
{
  "name": "Machine Learning",
  "slug": "machine-learning",
  "description": "ML research",
  "order": 1
}

POST /api/publications/topics/1/branches/
{
  "name": "Computer Vision",
  "slug": "computer-vision",
  "description": "Image processing",
  "order": 2
}
```

### 2. Author Publishes Article

```bash
# Author browses topics to find appropriate branch
GET /api/publications/topics/

# Author views branches under Computer Science
GET /api/publications/topics/1/branches/

# Author creates publication with topic branch
POST /api/publications/
{
  "title": "Novel ML Algorithm",
  "topic_branch": 1,
  "publication_type": "journal_article",
  ...
}
```

### 3. Public Browsing

```bash
# User browses all topics
GET /api/publications/topics/

# User explores Computer Science branches
GET /api/publications/topics/1/

# User views all ML publications
GET /api/publications/topics/1/branches/1/publications/
```

---

## Complete Topic Hierarchy Example

```
📚 Topics
├── 💻 Computer Science (id: 1)
│   ├── Machine Learning (id: 1)
│   ├── Artificial Intelligence (id: 2)
│   ├── Computer Vision (id: 3)
│   ├── Natural Language Processing (id: 4)
│   ├── Databases (id: 5)
│   └── Cybersecurity (id: 6)
│
├── 🧬 Biology (id: 2)
│   ├── Molecular Biology (id: 7)
│   ├── Genetics (id: 8)
│   ├── Bioinformatics (id: 9)
│   └── Ecology (id: 10)
│
├── ⚛️ Physics (id: 3)
│   ├── Quantum Physics (id: 11)
│   ├── Astrophysics (id: 12)
│   └── Particle Physics (id: 13)
│
└── 🧪 Chemistry (id: 4)
    ├── Organic Chemistry (id: 14)
    ├── Inorganic Chemistry (id: 15)
    └── Physical Chemistry (id: 16)
```

---

## Field Constraints

### Topic

- `name`: Max 200 chars, unique
- `slug`: Max 200 chars, unique, lowercase, URL-friendly
- `icon`: Max 100 chars (emoji or icon class)
- `order`: Integer (for sorting)

### TopicBranch

- `name`: Max 200 chars
- `slug`: Max 200 chars, unique per topic
- `topic` + `slug`: Unique together
- `order`: Integer (for sorting within topic)

---

## Permissions

| Action                       | Permission Required |
| ---------------------------- | ------------------- |
| List topics                  | Authenticated       |
| View topic details           | Authenticated       |
| Create topic                 | Admin/Staff         |
| Update topic                 | Admin/Staff         |
| Delete topic                 | Admin/Staff         |
| List branches                | Authenticated       |
| View branch details          | Authenticated       |
| Create branch                | Admin/Staff         |
| Update branch                | Admin/Staff         |
| Delete branch                | Admin/Staff         |
| Browse publications by topic | Public (no auth)    |

---

## Best Practices

1. **Slug Generation**: Always use lowercase, hyphen-separated slugs (e.g., "machine-learning")
2. **Ordering**: Use order field to control display sequence (lower numbers appear first)
3. **Icons**: Use emojis for visual appeal or icon classes (e.g., "fa-computer")
4. **Descriptions**: Provide clear, concise descriptions for better UX
5. **Active Status**: Mark inactive topics/branches as `is_active: false` instead of deleting
6. **Hierarchical Organization**: Keep topic hierarchies shallow (2 levels max)
7. **Consistent Naming**: Use standardized terminology across branches

---

## Error Responses

### 400 Bad Request

```json
{
  "slug": ["Topic with this slug already exists."]
}
```

### 403 Forbidden

```json
{
  "error": "Only administrators can create topics"
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

---

## Integration with Existing Features

The topic system integrates seamlessly with:

- **Publications**: Every publication can be tagged with a topic branch
- **Search**: Filter publications by topic/branch
- **Statistics**: Track publication counts per topic/branch
- **Admin Panel**: Full admin interface for managing topics

---

## Notes

1. **Cascading Deletes**: Deleting a topic deletes all its branches
2. **Publication Links**: When a branch is deleted, publications keep their data but topic_branch is set to NULL
3. **Slug Validation**: Slugs are automatically converted to lowercase
4. **Computed Fields**: `branches_count` and `publications_count` are computed properties
5. **Indexing**: Database indexes on slug and is_active for performance

---

For additional support, refer to the main API documentation at `/api/schema/swagger-ui/`
