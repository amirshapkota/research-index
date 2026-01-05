# Author Statistics and Co-Authors Feature

## Overview

The ResearchIndex platform now includes comprehensive author statistics and co-author tracking, similar to Google Scholar metrics. This feature provides authors with detailed insights into their research impact and collaboration networks.

## Features

### 1. Author Statistics (AuthorStats Model)

Author statistics are automatically calculated based on all published articles by the author.

#### Metrics Included:

**Impact Metrics:**

- **h-index**: Number h where the author has h papers with at least h citations each
- **i10-index**: Number of publications with at least 10 citations
- **Total Citations**: Sum of all citations across all publications

**Engagement Metrics:**

- **Total Reads**: Total number of times publications were read
- **Total Downloads**: Total number of PDF downloads
- **Recommendations Count**: Total recommendations received across all publications

**Additional Metrics:**

- **Total Publications**: Count of all published works
- **Average Citations per Paper**: Mean citation count per publication
- **Last Updated**: Timestamp of last statistics update

### 2. Co-Authors Tracking

The system automatically extracts and displays co-authors from publications.

#### Co-Author Information:

- **Name**: Full name of the co-author
- **Registered Status**: Whether the co-author has an account on the platform
- **Email**: Email address (if registered)
- **Institute**: Affiliated institution (if registered)
- **Collaboration Count**: Number of unique co-authors

## API Endpoints

### 1. Get Author Profile (with stats and co-authors)

**Endpoint:** `GET /api/users/profile/author/`

**Authentication:** Required (JWT Token)

**Response:**

```json
{
  "id": 1,
  "email": "john.doe@university.edu",
  "user_type": "author",
  "title": "Dr.",
  "full_name": "John Doe",
  "institute": "MIT",
  "designation": "Associate Professor",
  "degree": "PhD in Computer Science",
  "bio": "Researcher in AI and Machine Learning...",
  "research_interests": "AI, ML, Deep Learning",
  "stats": {
    "h_index": 15,
    "i10_index": 12,
    "total_citations": 450,
    "total_reads": 12000,
    "total_downloads": 3500,
    "recommendations_count": 85,
    "total_publications": 25,
    "average_citations_per_paper": 18.0,
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

### 2. Refresh Author Statistics

**Endpoint:** `POST /api/users/profile/author/refresh-stats/`

**Authentication:** Required (JWT Token)

**Description:** Manually trigger a recalculation of all statistics

**Response:**

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
    "average_citations_per_paper": 18.0,
    "last_updated": "2024-01-15T11:00:00Z"
  }
}
```

## How It Works

### H-Index Calculation

The h-index is calculated as follows:

1. Get all published articles by the author
2. Extract citation counts for each article
3. Sort citations in descending order
4. Find the largest number h where h articles have ≥h citations

**Example:**

- If an author has 5 papers with citations: [20, 15, 10, 5, 2]
- h-index = 4 (4 papers with at least 4 citations each)

### I10-Index Calculation

The i10-index is simply the count of publications with 10 or more citations.

### Co-Author Extraction

1. System scans all publications by the author
2. Extracts names from the `co_authors` field (comma-separated)
3. Attempts to match with registered Author accounts
4. Returns both registered and non-registered co-authors
5. Provides collaboration metadata for network analysis

## Statistics Auto-Update

Statistics are automatically updated in the following scenarios:

1. **On Profile View**: When an author profile is retrieved via API, stats are refreshed if:

   - Stats record doesn't exist (first-time creation)
   - Stats have never been updated (`last_updated` is None)

2. **Manual Refresh**: Authors can manually trigger updates via the refresh endpoint

3. **Admin Action**: Administrators can bulk recalculate stats from the Django admin panel

## Database Models

### AuthorStats Model

```python
class AuthorStats(models.Model):
    author = models.OneToOneField(Author, related_name='stats')
    h_index = models.IntegerField(default=0)
    i10_index = models.IntegerField(default=0)
    total_citations = models.IntegerField(default=0)
    total_reads = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    recommendations_count = models.IntegerField(default=0)
    total_publications = models.IntegerField(default=0)
    average_citations_per_paper = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Author Model (Updated Methods)

```python
class Author(models.Model):
    # ... existing fields ...

    def get_coauthors(self):
        """Return list of unique co-authors with collaboration details"""
        # Extracts from publications and matches with registered authors

    def get_collaboration_count(self):
        """Return count of unique co-authors"""
```

## Admin Interface

### AuthorStats Admin Features:

1. **List View**: Display key metrics for all authors
2. **Search**: Search by author name or email
3. **Filters**: Filter by last update date
4. **Readonly Fields**: All calculated fields are read-only
5. **Bulk Actions**: "Recalculate selected author statistics" action

**Admin URL:** `/admin/users/authorstats/`

## Usage Examples

### Example 1: View Your Stats

```bash
curl -X GET http://localhost:8000/api/users/profile/author/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example 2: Refresh Your Stats

```bash
curl -X POST http://localhost:8000/api/users/profile/author/refresh-stats/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example 3: Find Co-Authors in Response

The co-authors array in the profile response shows all collaborators:

- Registered users include full profile data
- Non-registered users show only the name extracted from publications

## Integration with Publications

The stats system integrates seamlessly with the Publications app:

1. **PublicationStats** provides per-article metrics
2. **AuthorStats** aggregates metrics across all publications
3. Co-authors are extracted from the `co_authors` text field in publications
4. All calculations use only published articles (`is_published=True`)

## Performance Considerations

- Stats are calculated on-demand to ensure accuracy
- First-time profile views trigger automatic stats creation
- Subsequent views use cached stats unless manually refreshed
- Admin bulk actions allow batch updates for multiple authors
- Consider setting up periodic tasks for automatic updates (optional)

## Future Enhancements

Potential features for future releases:

1. **Citation Graph**: Visualize citation trends over time
2. **Collaboration Network**: Interactive network graph of co-authors
3. **Impact Timeline**: Historical h-index and citation tracking
4. **Recommendations**: Suggest potential collaborators
5. **Alerts**: Notify authors of new citations or milestone achievements
6. **Export**: Download stats as PDF report
7. **Public Profiles**: Optional public author profile pages
8. **Comparative Metrics**: Compare stats with field averages

## Best Practices

1. **Refresh Regularly**: Manually refresh stats after publishing new articles
2. **Complete Co-Authors**: Always fill in the co-authors field for accurate collaboration tracking
3. **Name Consistency**: Use consistent author name formatting across publications
4. **Profile Completeness**: Maintain updated profile information for better discoverability
5. **ORCID Integration**: Link your ORCID to improve author disambiguation

## Troubleshooting

### Stats Not Updating?

1. Ensure publications have `is_published=True`
2. Check that PublicationStats exist for your articles
3. Manually trigger refresh via the endpoint
4. Contact admin if issues persist

### Co-Authors Missing?

1. Verify co-authors are listed in publication's `co_authors` field
2. Use comma-separated format: "Jane Doe, John Smith"
3. Ensure exact name match for registered users
4. Check publication is published (`is_published=True`)

### Zero H-Index?

1. Ensure publications have citation data in PublicationStats
2. Check that at least one publication has citations
3. Refresh stats manually to recalculate

## Technical Implementation

### Files Modified:

1. **users/models.py**

   - Added `AuthorStats` model
   - Added `get_coauthors()` method to Author
   - Added `get_collaboration_count()` method to Author

2. **users/serializers.py**

   - Added `AuthorStatsSerializer`
   - Added `CoAuthorSerializer`
   - Updated `AuthorProfileSerializer` with stats and coauthors fields

3. **users/views.py**

   - Added `RefreshAuthorStatsView`
   - Updated imports for new serializers

4. **users/admin.py**

   - Added `AuthorStatsAdmin` with bulk recalculate action

5. **users/urls.py**
   - Added `/profile/author/refresh-stats/` endpoint

### Migration:

```bash
python manage.py makemigrations users
python manage.py migrate users
```

## Conclusion

The Author Statistics and Co-Authors feature provides a comprehensive view of research impact and collaboration networks, empowering authors to track their academic influence and discover collaboration opportunities on the ResearchIndex platform.
