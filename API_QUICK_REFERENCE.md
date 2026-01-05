# API Quick Reference - Author Stats & Co-Writers

## Endpoints

### 1. Get Author Profile (includes stats and co-writers)

**Endpoint**: `GET /api/users/profile/author/`

**Authentication**: Required (Bearer token)

**Headers**:

```
Authorization: Bearer <your_access_token>
```

**Response** (200 OK):

```json
{
  "id": 1,
  "email": "author@university.edu",
  "user_type": "author",
  "title": "Dr.",
  "full_name": "John Doe",
  "institute": "MIT",
  "designation": "Associate Professor",
  "degree": "PhD in Computer Science",
  "gender": "male",
  "profile_picture": "/media/profiles/authors/photo.jpg",
  "profile_picture_url": "http://localhost:8000/media/profiles/authors/photo.jpg",
  "cv": "/media/cvs/cv.pdf",
  "cv_url": "http://localhost:8000/media/cvs/cv.pdf",
  "bio": "Researcher specializing in AI...",
  "research_interests": "Machine Learning, Deep Learning, NLP",
  "orcid": "0000-0001-2345-6789",
  "google_scholar": "https://scholar.google.com/citations?user=ABC123",
  "researchgate": "https://www.researchgate.net/profile/John-Doe",
  "linkedin": "https://linkedin.com/in/johndoe",
  "website": "https://johndoe.com",
  "stats": {
    "h_index": 15,
    "i10_index": 12,
    "total_citations": 450,
    "total_reads": 12000,
    "total_downloads": 3500,
    "recommendations_count": 85,
    "total_publications": 25,
    "average_citations_per_paper": "18.00",
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "coauthors": [
    {
      "id": 45,
      "name": "Jane Smith",
      "email": "jane.smith@university.edu",
      "institute": "Stanford University",
      "is_registered": true
    },
    {
      "id": null,
      "name": "Robert Johnson",
      "email": null,
      "institute": null,
      "is_registered": false
    }
  ],
  "collaboration_count": 2
}
```

---

### 2. Refresh Author Statistics

**Endpoint**: `POST /api/users/profile/author/refresh-stats/`

**Authentication**: Required (Bearer token)

**Headers**:

```
Authorization: Bearer <your_access_token>
```

**Request Body**: None (empty POST)

**Response** (200 OK):

```json
{
  "message": "Statistics updated successfully",
  "stats": {
    "h_index": 15,
    "i10_index": 12,
    "total_citations": 450,
    "total_reads": 12000,
    "total_downloads": 3500,
    "recommendations_count": 85,
    "total_publications": 25,
    "average_citations_per_paper": "18.00",
    "last_updated": "2024-01-15T11:00:00Z"
  }
}
```

**Error Response** (403 Forbidden):

```json
{
  "error": "Only authors can refresh statistics"
}
```

**Error Response** (404 Not Found):

```json
{
  "error": "Author profile not found"
}
```

---

## Usage Examples

### cURL Examples

#### 1. Get Profile with Stats

```bash
curl -X GET http://localhost:8000/api/users/profile/author/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 2. Refresh Statistics

```bash
curl -X POST http://localhost:8000/api/users/profile/author/refresh-stats/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript/Fetch Examples

#### 1. Get Profile

```javascript
fetch("http://localhost:8000/api/users/profile/author/", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((data) => {
    console.log("H-Index:", data.stats.h_index);
    console.log("Total Citations:", data.stats.total_citations);
    console.log("Co-authors:", data.coauthors);
  })
  .catch((error) => console.error("Error:", error));
```

#### 2. Refresh Stats

```javascript
fetch("http://localhost:8000/api/users/profile/author/refresh-stats/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  },
})
  .then((response) => response.json())
  .then((data) => {
    console.log("Updated stats:", data.stats);
  })
  .catch((error) => console.error("Error:", error));
```

### Python/Requests Examples

#### 1. Get Profile

```python
import requests

url = 'http://localhost:8000/api/users/profile/author/'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get(url, headers=headers)
data = response.json()

print(f"H-Index: {data['stats']['h_index']}")
print(f"Total Citations: {data['stats']['total_citations']}")
print(f"Co-authors: {len(data['coauthors'])}")
```

#### 2. Refresh Stats

```python
import requests

url = 'http://localhost:8000/api/users/profile/author/refresh-stats/'
headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.post(url, headers=headers)
data = response.json()

print(data['message'])
print(f"New H-Index: {data['stats']['h_index']}")
```

---

## Response Field Descriptions

### Stats Object

| Field                         | Type     | Description                                          |
| ----------------------------- | -------- | ---------------------------------------------------- |
| `h_index`                     | integer  | Number h where author has h papers with ≥h citations |
| `i10_index`                   | integer  | Number of publications with ≥10 citations            |
| `total_citations`             | integer  | Sum of all citations across all publications         |
| `total_reads`                 | integer  | Aggregate read count across all publications         |
| `total_downloads`             | integer  | Total PDF downloads across all publications          |
| `recommendations_count`       | integer  | Total recommendations across all publications        |
| `total_publications`          | integer  | Number of published articles                         |
| `average_citations_per_paper` | decimal  | Mean citations per publication                       |
| `last_updated`                | datetime | ISO 8601 timestamp of last update                    |

### Co-Author Object

| Field           | Type         | Description                               |
| --------------- | ------------ | ----------------------------------------- |
| `id`            | integer/null | Author ID if registered, null otherwise   |
| `name`          | string       | Full name of co-author                    |
| `email`         | string/null  | Email if registered, null otherwise       |
| `institute`     | string/null  | Institution if registered, null otherwise |
| `is_registered` | boolean      | Whether co-author has an account          |

---

## When to Refresh Stats

Stats are automatically created/updated on first profile GET request. Manual refresh is needed when:

1. **After Publishing New Articles**: Update metrics to include new publications
2. **Citation Count Changes**: When publications receive new citations
3. **Engagement Updates**: When reads/downloads/recommendations change
4. **Periodic Updates**: Regular maintenance (daily/weekly)

---

## Admin Panel Access

**URL**: `http://localhost:8000/admin/users/authorstats/`

**Features**:

- View all author statistics
- Search by author name/email
- Filter by last update date
- Bulk recalculate action for multiple authors

---

## Notes

1. **Authentication Required**: Both endpoints require valid JWT access token
2. **Author Only**: Stats are only available for user_type='author'
3. **Published Only**: Calculations use only published articles (`is_published=True`)
4. **Name Matching**: Co-author matching uses case-insensitive name search
5. **Performance**: First-time stats creation may take a few seconds for prolific authors

---

## Error Codes

| Code | Meaning      | Solution                                |
| ---- | ------------ | --------------------------------------- |
| 401  | Unauthorized | Provide valid access token              |
| 403  | Forbidden    | Only authors can access these endpoints |
| 404  | Not Found    | Author profile doesn't exist            |
| 500  | Server Error | Contact administrator                   |

---

## Integration Guide

### Frontend Display Example

```javascript
// Display author stats card
function renderAuthorStats(stats) {
  return `
    <div class="stats-card">
      <h3>Research Metrics</h3>
      <div class="metric">
        <label>h-index:</label>
        <span class="value">${stats.h_index}</span>
      </div>
      <div class="metric">
        <label>i10-index:</label>
        <span class="value">${stats.i10_index}</span>
      </div>
      <div class="metric">
        <label>Total Citations:</label>
        <span class="value">${stats.total_citations}</span>
      </div>
      <div class="metric">
        <label>Publications:</label>
        <span class="value">${stats.total_publications}</span>
      </div>
      <div class="metric">
        <label>Avg Citations/Paper:</label>
        <span class="value">${stats.average_citations_per_paper}</span>
      </div>
      <small>Last updated: ${new Date(
        stats.last_updated
      ).toLocaleDateString()}</small>
    </div>
  `;
}

// Display co-authors list
function renderCoauthors(coauthors) {
  return coauthors
    .map(
      (ca) => `
    <div class="coauthor ${ca.is_registered ? "registered" : "external"}">
      <h4>${ca.name}</h4>
      ${ca.institute ? `<p>${ca.institute}</p>` : ""}
      ${ca.is_registered ? '<span class="badge">Registered</span>' : ""}
    </div>
  `
    )
    .join("");
}
```

---

## Support

For questions or issues:

1. Check the comprehensive documentation: `AUTHOR_STATS_AND_COAUTHORS.md`
2. Review implementation details: `IMPLEMENTATION_SUMMARY.md`
3. Contact the development team
