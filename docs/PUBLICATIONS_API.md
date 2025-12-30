# Publications API Documentation

## Overview

Complete publication management system for authors. This system allows authors to add articles with comprehensive metadata, track statistics, manage citations and references, and provide external links.

---

## Authentication

All publication management endpoints require **JWT authentication** (author accounts only). Include the access token:

```
Authorization: Bearer <your_access_token>
```

---

## Available Endpoints

### 1. Create Publication

**Endpoint:** `POST /api/publications/`

**Description:** Create a new publication with PDF upload, MeSH terms, and external links.

**Authentication:** Required (Author only)

**Content-Type:** `multipart/form-data` (for PDF upload) or `application/json`

**Request Body:**

```json
{
  "title": "Deep Learning Applications in Medical Imaging",
  "abstract": "This paper explores the use of deep learning techniques...",
  "publication_type": "journal_article",
  "pdf_file": "<file>",
  "doi": "10.1234/example.2024.001",
  "published_date": "2024-01-15",
  "journal_name": "Journal of Medical AI",
  "volume": "10",
  "issue": "2",
  "pages": "123-145",
  "publisher": "Medical Press",
  "co_authors": "Jane Smith, John Doe, Alice Johnson",
  "pubmed_id": "12345678",
  "arxiv_id": "2401.12345",
  "pubmed_central_id": "PMC9876543",
  "is_published": true,
  "mesh_terms_data": [
    { "term": "Deep Learning", "term_type": "major" },
    { "term": "Medical Imaging", "term_type": "major" },
    { "term": "Artificial Intelligence", "term_type": "minor" }
  ],
  "link_outs_data": [
    {
      "link_type": "pubmed",
      "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    },
    { "link_type": "doi", "url": "https://doi.org/10.1234/example.2024.001" }
  ]
}
```

**Publication Types:**

- `journal_article` - Journal Article
- `conference_paper` - Conference Paper
- `book_chapter` - Book Chapter
- `preprint` - Preprint
- `thesis` - Thesis/Dissertation
- `technical_report` - Technical Report
- `poster` - Poster
- `presentation` - Presentation
- `book` - Book
- `review` - Review Article
- `other` - Other

**MeSH Term Types:**

- `major` - Major Topic
- `minor` - Minor Topic

**Link Out Types:**

- `pubmed`, `pmc`, `google_scholar`, `doi`, `arxiv`, `researchgate`, `academia`, `publisher`, `preprint`, `dataset`, `code`, `other`

**Response (201 Created):**

```json
{
  "message": "Publication created successfully",
  "publication": {
    "id": 1,
    "title": "Deep Learning Applications in Medical Imaging",
    "abstract": "This paper explores...",
    "publication_type": "journal_article",
    "publication_type_display": "Journal Article",
    "pdf_file": "/media/publications/pdfs/article.pdf",
    "pdf_url": "http://localhost:8000/media/publications/pdfs/article.pdf",
    "doi": "10.1234/example.2024.001",
    "published_date": "2024-01-15",
    "journal_name": "Journal of Medical AI",
    "volume": "10",
    "issue": "2",
    "pages": "123-145",
    "publisher": "Medical Press",
    "co_authors": "Jane Smith, John Doe, Alice Johnson",
    "pubmed_id": "12345678",
    "arxiv_id": "2401.12345",
    "pubmed_central_id": "PMC9876543",
    "is_published": true,
    "created_at": "2024-12-30T10:30:00Z",
    "updated_at": "2024-12-30T10:30:00Z",
    "author_id": 1,
    "author_name": "Dr. John Smith",
    "author_email": "john@example.com",
    "author_orcid": "0000-0001-2345-6789",
    "mesh_terms": [
      { "id": 1, "term": "Deep Learning", "term_type": "major" },
      { "id": 2, "term": "Medical Imaging", "term_type": "major" }
    ],
    "citations": [],
    "references": [],
    "link_outs": [
      {
        "id": 1,
        "link_type": "pubmed",
        "link_type_display": "PubMed",
        "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
      }
    ],
    "stats": {
      "citations_count": 0,
      "reads_count": 0,
      "downloads_count": 0,
      "recommendations_count": 0,
      "altmetric_score": "0.00",
      "field_citation_ratio": "0.00"
    }
  }
}
```

---

### 2. List My Publications

**Endpoint:** `GET /api/publications/`

**Description:** Get all publications for the authenticated author.

**Authentication:** Required

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "title": "Deep Learning Applications in Medical Imaging",
    "author_name": "Dr. John Smith",
    "author_orcid": "0000-0001-2345-6789",
    "publication_type": "journal_article",
    "publication_type_display": "Journal Article",
    "doi": "10.1234/example.2024.001",
    "published_date": "2024-01-15",
    "journal_name": "Journal of Medical AI",
    "abstract": "This paper explores...",
    "pdf_url": "http://localhost:8000/media/publications/pdfs/article.pdf",
    "is_published": true,
    "created_at": "2024-12-30T10:30:00Z",
    "updated_at": "2024-12-30T10:30:00Z",
    "stats": {
      "citations_count": 5,
      "reads_count": 120,
      "downloads_count": 45,
      "recommendations_count": 10,
      "altmetric_score": "15.50",
      "field_citation_ratio": "1.25"
    },
    "mesh_terms_count": 3,
    "citations_count": 5,
    "references_count": 25
  }
]
```

---

### 3. Get Publication Details

**Endpoint:** `GET /api/publications/{id}/`

**Description:** Get complete details of a publication including all citations, references, and stats.

**Authentication:** Required

**Response (200 OK):** Same as create response with all nested data.

---

### 4. Update Publication

**Endpoint:** `PUT /api/publications/{id}/` (Full update) or `PATCH /api/publications/{id}/` (Partial)

**Description:** Update publication details, upload new PDF, or modify metadata.

**Authentication:** Required

**Request Body:** Same as create (all fields for PUT, selected fields for PATCH)

---

### 5. Delete Publication

**Endpoint:** `DELETE /api/publications/{id}/`

**Description:** Permanently delete a publication and all associated data.

**Authentication:** Required

**Response (200 OK):**

```json
{
  "message": "Publication \"Deep Learning Applications in Medical Imaging\" has been deleted successfully"
}
```

---

### 6. Get Publication Stats

**Endpoint:** `GET /api/publications/{id}/stats/`

**Description:** Get statistics for a publication.

**Authentication:** Required

**Response (200 OK):**

```json
{
  "citations_count": 15,
  "reads_count": 450,
  "downloads_count": 120,
  "recommendations_count": 25,
  "altmetric_score": "32.50",
  "field_citation_ratio": "1.75",
  "last_updated": "2024-12-30T15:30:00Z"
}
```

---

### 7. Update Publication Stats

**Endpoint:** `PATCH /api/publications/{id}/stats/`

**Description:** Manually update statistics (useful for importing data).

**Authentication:** Required

**Request Body:**

```json
{
  "citations_count": 20,
  "altmetric_score": "45.00",
  "field_citation_ratio": "2.10"
}
```

---

### 8. Add Citation

**Endpoint:** `POST /api/publications/{id}/citations/add/`

**Description:** Add a citation to your publication. Automatically increments citation count.

**Authentication:** Required

**Request Body:**

```json
{
  "citing_title": "Advanced Machine Learning Techniques in Healthcare",
  "citing_authors": "Smith J, Doe J, Johnson A",
  "citing_doi": "10.5678/example.2024.002",
  "citing_year": 2024,
  "citing_journal": "AI Research Journal"
}
```

**Response (201 Created):**

```json
{
  "message": "Citation added successfully",
  "citation": {
    "id": 1,
    "citing_title": "Advanced Machine Learning Techniques in Healthcare",
    "citing_authors": "Smith J, Doe J, Johnson A",
    "citing_doi": "10.5678/example.2024.002",
    "citing_year": 2024,
    "citing_journal": "AI Research Journal",
    "added_at": "2024-12-30T16:00:00Z"
  }
}
```

---

### 9. Add Single Reference

**Endpoint:** `POST /api/publications/{id}/references/add/`

**Description:** Add a reference to your publication.

**Authentication:** Required

**Request Body:**

```json
{
  "reference_text": "Author A, Author B. Title of Referenced Paper. Journal Name. 2023;10(2):123-145. doi:10.1234/ref.2023.001",
  "reference_title": "Title of Referenced Paper",
  "reference_authors": "Author A, Author B",
  "reference_doi": "10.1234/ref.2023.001",
  "reference_year": 2023,
  "reference_journal": "Journal Name",
  "order": 1
}
```

---

### 10. Add Multiple References (Bulk)

**Endpoint:** `POST /api/publications/{id}/references/bulk/`

**Description:** Add multiple references at once.

**Authentication:** Required

**Request Body:**

```json
{
  "references": [
    {
      "reference_text": "Smith J. Paper 1. Journal A. 2023;1:1-10.",
      "reference_title": "Paper 1",
      "reference_authors": "Smith J",
      "reference_year": 2023,
      "order": 1
    },
    {
      "reference_text": "Doe A. Paper 2. Journal B. 2022;2:20-30.",
      "reference_title": "Paper 2",
      "reference_authors": "Doe A",
      "reference_year": 2022,
      "order": 2
    }
  ]
}
```

**Response (201 Created):**

```json
{
  "message": "2 references added successfully",
  "count": 2
}
```

---

### 11. Record Read Event (Public)

**Endpoint:** `POST /api/publications/{id}/read/`

**Description:** Record when someone reads your publication. Increments read count.

**Authentication:** Not required (public)

**Response (200 OK):**

```json
{
  "message": "Read recorded",
  "reads_count": 451
}
```

---

### 12. Download PDF (Public)

**Endpoint:** `GET /api/publications/{id}/download/`

**Description:** Get PDF URL and increment download count.

**Authentication:** Not required (public)

**Response (200 OK):**

```json
{
  "message": "Download initiated",
  "pdf_url": "http://localhost:8000/media/publications/pdfs/article.pdf",
  "downloads_count": 121
}
```

---

## Complete Workflow Example

### Creating a Publication with All Metadata

```javascript
const createPublication = async () => {
  const formData = new FormData();

  // Basic info
  formData.append("title", "Deep Learning in Medical Imaging");
  formData.append("abstract", "This comprehensive study...");
  formData.append("publication_type", "journal_article");

  // PDF file
  const pdfFile = document.getElementById("pdf-input").files[0];
  formData.append("pdf_file", pdfFile);

  // Publication details
  formData.append("doi", "10.1234/example.2024.001");
  formData.append("published_date", "2024-01-15");
  formData.append("journal_name", "Journal of Medical AI");
  formData.append("volume", "10");
  formData.append("issue", "2");
  formData.append("pages", "123-145");
  formData.append("publisher", "Medical Press");
  formData.append("co_authors", "Jane Smith, John Doe");

  // External IDs
  formData.append("pubmed_id", "12345678");
  formData.append("arxiv_id", "2401.12345");

  // MeSH terms (as JSON string)
  formData.append(
    "mesh_terms_data",
    JSON.stringify([
      { term: "Deep Learning", term_type: "major" },
      { term: "Medical Imaging", term_type: "major" },
    ])
  );

  // Link outs (as JSON string)
  formData.append(
    "link_outs_data",
    JSON.stringify([
      { link_type: "pubmed", url: "https://pubmed.ncbi.nlm.nih.gov/12345678/" },
      { link_type: "doi", url: "https://doi.org/10.1234/example.2024.001" },
    ])
  );

  const response = await fetch("http://localhost:8000/api/publications/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  const data = await response.json();
  console.log("Publication created:", data);
};
```

### Adding Citations Programmatically

```javascript
const addCitation = async (publicationId, citationData) => {
  const response = await fetch(
    `http://localhost:8000/api/publications/${publicationId}/citations/add/`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(citationData),
    }
  );

  return await response.json();
};

// Use it
await addCitation(1, {
  citing_title: "Advanced ML in Healthcare",
  citing_authors: "Smith J, Doe A",
  citing_doi: "10.5678/cite.2024.001",
  citing_year: 2024,
  citing_journal: "AI Journal",
});
```

---

## Data Models

### Publication Fields

| Field             | Type    | Description                 | Required |
| ----------------- | ------- | --------------------------- | -------- |
| title             | string  | Publication title           | Yes      |
| abstract          | text    | Abstract/summary            | No       |
| publication_type  | choice  | Type of publication         | Yes      |
| pdf_file          | file    | PDF upload                  | No       |
| doi               | string  | Digital Object Identifier   | No       |
| published_date    | date    | Publication date            | No       |
| journal_name      | string  | Journal/conference name     | No       |
| volume            | string  | Volume number               | No       |
| issue             | string  | Issue number                | No       |
| pages             | string  | Page range                  | No       |
| publisher         | string  | Publisher name              | No       |
| co_authors        | text    | Comma-separated co-authors  | No       |
| erratum_from      | FK      | Original if this is erratum | No       |
| pubmed_id         | string  | PubMed ID                   | No       |
| arxiv_id          | string  | arXiv ID                    | No       |
| pubmed_central_id | string  | PMC ID                      | No       |
| is_published      | boolean | Public visibility           | Yes      |

### Stats Fields

| Field                 | Type    | Description         |
| --------------------- | ------- | ------------------- |
| citations_count       | integer | Number of citations |
| reads_count           | integer | Number of reads     |
| downloads_count       | integer | Number of downloads |
| recommendations_count | integer | Recommendations     |
| altmetric_score       | decimal | Altmetric score     |
| field_citation_ratio  | decimal | Citation ratio      |

---

## Key Features

**Comprehensive Metadata** - All fields needed for academic publications  
 **PDF Upload** - Store and serve publication PDFs  
 **MeSH Terms** - Medical subject headings for categorization  
 **Citation Tracking** - Track who cites your work  
 **Reference Management** - Store all references  
 **External Links** - Link to PubMed, DOI, arXiv, etc.  
 **Statistics** - Citations, reads, downloads, altmetric  
 **Author ORCID** - Automatically includes author's ORCID  
 **DOI Integration** - Store and display DOI  
 **Erratum Support** - Link errata to original publications  
 **Public/Private** - Control publication visibility

All endpoints documented in Swagger UI at: http://localhost:8000/api/docs/
