# Journal API Test Guide

This guide helps you test all the journal endpoints using curl or your API client.

## Prerequisites

1. **Start the server**: `python manage.py runserver`
2. **Get authentication token**: Login as an institution user
3. **Replace** `YOUR_ACCESS_TOKEN` with your actual token in the examples below

## Step-by-Step Testing

### 1. Register/Login as Institution

```bash
# Register Institution
curl -X POST http://127.0.0.1:8000/api/users/register/institution/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "journal@university.edu",
    "password": "SecurePass123!",
    "institution_name": "International University",
    "institution_type": "university",
    "country": "USA"
  }'

# Login
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "journal@university.edu",
    "password": "SecurePass123!"
  }'
```

**Copy the `access` token from the response!**

---

### 2. Create a Journal

```bash
curl -X POST http://127.0.0.1:8000/api/publications/journals/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "International Journal of Advanced Research",
    "short_title": "IJAR",
    "issn": "1234-5678",
    "e_issn": "9876-5432",
    "description": "Leading journal in advanced scientific research",
    "scope": "Covers all aspects of advanced scientific research including AI, ML, and data science",
    "publisher_name": "Academic Publishing House",
    "publisher_location": "New York, USA",
    "frequency": "quarterly",
    "established_year": 2020,
    "about_journal": "The International Journal of Advanced Research publishes cutting-edge research across multiple disciplines. We are committed to advancing scientific knowledge and promoting open access to research.",
    "ethics_policies": "All manuscripts undergo rigorous peer review. We adhere to COPE guidelines and maintain strict ethical standards including plagiarism detection, conflict of interest disclosure, and data integrity verification.",
    "writing_formatting": "Authors should follow APA 7th edition for citations and references. Manuscripts should be double-spaced, 12pt Times New Roman font. Include an abstract of 150-250 words. Maximum manuscript length: 8000 words excluding references.",
    "submitting_manuscript": "Submit manuscripts via our online submission system at https://submit.ijar.com. Include a cover letter stating the manuscripts originality and significance. All authors must approve the final submission.",
    "help_support": "For technical support, contact support@ijar.com. For editorial queries, reach out to editor@ijar.com. Office hours: Monday-Friday, 9 AM - 5 PM EST.",
    "contact_email": "editor@ijar.com",
    "contact_phone": "+1-555-123-4567",
    "contact_address": "123 Research Plaza, Suite 456, New York, NY 10001",
    "website_url": "https://www.ijar.com",
    "is_open_access": true,
    "peer_reviewed": true,
    "editorial_board_data": [
      {
        "name": "Dr. John Smith",
        "role": "editor_in_chief",
        "title": "Professor",
        "affiliation": "Harvard University",
        "email": "john.smith@harvard.edu",
        "bio": "Dr. John Smith is a distinguished professor with over 25 years of experience in advanced research. He has published 150+ papers and received numerous awards for his contributions to science.",
        "expertise": "Artificial Intelligence, Machine Learning, Data Science",
        "orcid": "0000-0001-2345-6789",
        "google_scholar_profile": "https://scholar.google.com/citations?user=abc123",
        "order": 1
      },
      {
        "name": "Dr. Jane Doe",
        "role": "associate_editor",
        "title": "Associate Professor",
        "affiliation": "MIT",
        "email": "jane.doe@mit.edu",
        "bio": "Dr. Jane Doe specializes in computational methods and has been instrumental in advancing research methodologies.",
        "expertise": "Computational Methods, Algorithm Design",
        "orcid": "0000-0002-3456-7890",
        "order": 2
      },
      {
        "name": "Dr. Robert Chen",
        "role": "managing_editor",
        "affiliation": "Stanford University",
        "email": "robert.chen@stanford.edu",
        "expertise": "Research Management, Quality Assurance",
        "order": 3
      }
    ]
  }'
```

**Expected Response**: Journal created with ID, editorial board, and auto-created stats

---

### 3. List Your Journals

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 4. Get Journal Details

```bash
# Replace {journal_id} with the ID from step 2
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 5. Update Journal Statistics

```bash
curl -X PATCH http://127.0.0.1:8000/api/publications/journals/1/stats/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "impact_factor": 3.45,
    "cite_score": 4.2,
    "h_index": 25,
    "sjr_score": 1.8,
    "acceptance_rate": 35.5,
    "average_review_time": 45
  }'
```

---

### 6. Add Editorial Board Member

```bash
curl -X POST http://127.0.0.1:8000/api/publications/journals/1/editorial-board/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Sarah Johnson",
    "role": "section_editor",
    "title": "Assistant Professor",
    "affiliation": "Princeton University",
    "email": "sarah.j@princeton.edu",
    "bio": "Dr. Johnson is an expert in computational biology with a focus on bioinformatics.",
    "expertise": "Computational Biology, Bioinformatics, Genomics",
    "orcid": "0000-0003-4567-8901",
    "order": 4
  }'
```

---

### 7. Create an Issue

```bash
curl -X POST http://127.0.0.1:8000/api/publications/journals/1/issues/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "volume": 1,
    "issue_number": 1,
    "title": "Inaugural Issue - Spring 2024",
    "publication_date": "2024-03-01",
    "submission_deadline": "2024-01-15",
    "doi": "10.1234/ijar.2024.1.1",
    "editorial_note": "Welcome to the inaugural issue of IJAR. This issue showcases groundbreaking research from leading scientists worldwide.",
    "status": "upcoming",
    "is_special_issue": false
  }'
```

---

### 8. List Journal Issues

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/issues/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 9. Get Issue Details

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/issues/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### 10. Create a Publication (as Author)

First, you need to create/login as an author and create a publication:

```bash
# Register Author
curl -X POST http://127.0.0.1:8000/api/users/register/author/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "author@research.com",
    "password": "AuthorPass123!",
    "full_name": "Dr. Alice Researcher",
    "field_of_study": "Computer Science",
    "institution": "Tech University"
  }'

# Login as Author
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "author@research.com",
    "password": "AuthorPass123!"
  }'

# Create Publication (use Author's token)
curl -X POST http://127.0.0.1:8000/api/publications/ \
  -H "Authorization: Bearer AUTHOR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deep Learning Applications in Healthcare: A Comprehensive Review",
    "abstract": "This paper reviews recent advances in deep learning applications for healthcare, including medical imaging, diagnosis, and treatment planning.",
    "publication_type": "journal_article",
    "doi": "10.1234/article.2024.001",
    "published_date": "2024-02-15",
    "journal_name": "International Journal of Advanced Research",
    "volume": "1",
    "issue": "1",
    "pages": "1-15",
    "publisher": "Academic Publishing House",
    "co_authors": "Dr. Bob Smith, Dr. Carol White",
    "is_published": true
  }'
```

---

### 11. Add Publication to Issue

```bash
# Use Institution token and publication ID from step 10
curl -X POST http://127.0.0.1:8000/api/publications/journals/1/issues/1/articles/add/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publication_id": 1,
    "section": "Research Articles",
    "order": 1
  }'
```

---

### 12. Update Issue Status to Published

```bash
curl -X PATCH http://127.0.0.1:8000/api/publications/journals/1/issues/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "published",
    "publication_date": "2024-03-01"
  }'
```

---

### 13. Update Journal Information

```bash
curl -X PATCH http://127.0.0.1:8000/api/publications/journals/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description with more details about our journal",
    "about_journal": "Updated about section with new information"
  }'
```

---

## Testing with File Uploads

### Upload Journal Cover Image

```bash
curl -X PATCH http://127.0.0.1:8000/api/publications/journals/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "cover_image=@/path/to/your/journal_cover.jpg"
```

### Upload Editorial Board Member Photo

```bash
curl -X POST http://127.0.0.1:8000/api/publications/journals/1/editorial-board/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "name=Dr. Michael Brown" \
  -F "role=editorial_board_member" \
  -F "affiliation=Yale University" \
  -F "email=michael.b@yale.edu" \
  -F "photo=@/path/to/photo.jpg" \
  -F "order=5"
```

---

## Accessing API Documentation

Visit these URLs in your browser while the server is running:

1. **Swagger UI**: http://127.0.0.1:8000/api/schema/swagger-ui/
2. **Redoc**: http://127.0.0.1:8000/api/schema/redoc/
3. **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

These interfaces provide interactive testing of all endpoints!

---

## Expected Results

After completing all steps, you should have:

✅ Institution account created  
✅ Journal created with editorial board  
✅ Journal statistics updated  
✅ Additional editorial board member added  
✅ Issue created  
✅ Author account created  
✅ Publication created  
✅ Publication added to issue  
✅ Issue published

---

## Verification Queries

### Check Journal with All Data

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

### Check Issue with Articles

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/issues/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

### Check Journal Statistics

```bash
curl -X GET http://127.0.0.1:8000/api/publications/journals/1/stats/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

---

## Common Issues & Solutions

### Issue: "Authentication credentials were not provided"

**Solution**: Make sure you're including the Authorization header with a valid token

### Issue: "Journal not found"

**Solution**: Verify the journal ID and ensure you're logged in as the institution that owns it

### Issue: "Publication not found" when adding to issue

**Solution**: Make sure the publication exists and is published

### Issue: "Duplicate ISSN"

**Solution**: Use a unique ISSN for each journal

---

## Django Admin Access

You can also manage journals via Django admin:

1. Create superuser: `python manage.py createsuperuser`
2. Visit: http://127.0.0.1:8000/admin/
3. Navigate to Publications → Journals

---

## Next Steps

1. Test all endpoints thoroughly
2. Try edge cases (invalid data, unauthorized access, etc.)
3. Upload images for journals, issues, and editorial board
4. Create multiple issues with different statuses
5. Add multiple articles to issues
6. Test the workflow from draft to published status

---

For complete API documentation, see [JOURNALS_API.md](JOURNALS_API.md)
