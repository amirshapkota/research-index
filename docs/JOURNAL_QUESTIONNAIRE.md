# Journal Questionnaire System

## Overview

After adding a journal to the system, institutions can complete a comprehensive **12-section questionnaire** to provide detailed information for journal evaluation and indexing purposes (e.g., Index Copernicus, DOAJ, Scopus evaluation).

## Table of Contents

1. [How Journals Are Added](#how-journals-are-added)
2. [Questionnaire Sections](#questionnaire-sections)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Data Model](#data-model)
6. [Validation Rules](#validation-rules)

---

## How Journals Are Added

### Current Journal Creation Flow

1. **Institution Login**: User logs in with institution credentials
2. **Create Journal**: POST to `/api/publications/journals/`
3. **Basic Information**: Provides basic journal info (title, ISSN, description, etc.)
4. **Journal Created**: A `Journal` object and associated `JournalStats` object are created

### New Questionnaire Flow

After a journal is created, the system prompts for a comprehensive questionnaire:

```
Journal Created → Questionnaire Prompt → Fill 12 Sections → Submit → Complete
```

---

## Questionnaire Sections

The questionnaire is divided into **12 comprehensive sections**:

### Section 1: Journal Identity & Formal Data

Basic identifying information about the journal.

**Fields:**

- Journal title
- ISSN / e-ISSN
- Publisher name
- Publisher country
- Year of first publication
- Publication frequency (weekly, monthly, quarterly, etc.)
- Publication format (online / print / both)
- Journal website URL
- Contact email

### Section 2: Scientific Scope & Profile

Information about the journal's scientific focus and article types.

**Fields:**

- Main scientific discipline
- Secondary disciplines (if applicable)
- Aims and scope (detailed text)
- Types of published articles:
  - Original research (checkbox)
  - Review articles (checkbox)
  - Case studies (checkbox)
  - Short communications (checkbox)
  - Other (text field for specification)

### Section 3: Editorial Board

Details about the journal's editorial leadership and board.

**Fields:**

- Editor-in-Chief name
- Editor-in-Chief affiliation
- Country of Editor-in-Chief
- Number of editorial board members
- Countries represented on editorial board (comma-separated)
- Percentage of foreign editorial board members
- Are full editorial board details published on the website? (Yes/No)

### Section 4: Peer Review Process

Critical information about the peer review system.

**Fields:**

- Does the journal use peer review? (Yes/No)
- Peer review type:
  - Single-blind
  - Double-blind
  - Open peer review
  - Post-publication review
  - Other
- Number of reviewers per manuscript
- Average review time (in weeks)
- Are reviewers external to the authors' institutions? (Yes/No)
- Is the peer-review procedure described on the website? (Yes/No)
- Peer review procedure URL

### Section 5: Ethics & Publication Standards

Information about publication ethics and standards.

**Fields:**

- Does the journal follow publication ethics? (Yes/No)
- Ethics guidelines based on:
  - COPE (checkbox)
  - ICMJE (checkbox)
  - Other (text field)
- Plagiarism detection used? (Yes/No)
- Name of plagiarism software (e.g., iThenticate)
- Retraction policy available? (Yes/No + URL)
- Conflict of interest policy available? (Yes/No + URL)

### Section 6: Publishing Regularity & Stability

Metrics about publication consistency and volume.

**Fields:**

- Number of issues published in the evaluated year
- Were all declared issues published on time? (Yes/No)
- Number of articles published in the year
- Number of rejected submissions
- Average acceptance rate (%)

### Section 7: Authors & Internationalization

Author diversity and internationalization metrics.

**Fields:**

- Total number of authors published in the year
- Number of foreign authors
- Number of countries represented by authors
- Percentage of foreign authors
- Does the journal encourage international submissions? (Yes/No)

### Section 8: Open Access & Fees

Open access model and pricing information.

**Fields:**

- Is the journal Open Access? (Yes/No)
- OA model:
  - Gold OA
  - Hybrid OA
  - Diamond OA (no fees)
  - Green OA
  - Bronze OA
  - Not Open Access
- Article Processing Charge (APC)? (Yes/No)
- APC amount (if applicable)
- APC currency
- License type:
  - CC BY
  - CC BY-SA
  - CC BY-NC
  - CC BY-NC-SA
  - CC BY-ND
  - CC BY-NC-ND
  - CC0 (Public Domain)
  - Other

### Section 9: Digital Publishing Standards

Technical standards and infrastructure.

**Fields:**

- Does the journal assign DOIs? (Yes/No)
- DOI registration agency (e.g., Crossref)
- Metadata standards used (comma-separated)
- Online submission system used? (Yes/No)
- Submission system name (e.g., Open Journal Systems)
- Digital archiving system:
  - LOCKSS
  - CLOCKSS
  - Portico
  - Institutional repository
  - PubMed Central
  - Other
  - None

### Section 10: Indexing & Visibility

Database indexing and discovery information.

**Fields:**

- Databases where the journal is indexed (comma-separated)
- Year first indexed
- Presence in:
  - Google Scholar (checkbox)
  - DOAJ (checkbox)
  - Scopus (checkbox)
  - Web of Science (checkbox)
- Abstracting services used (comma-separated)

### Section 11: Website Quality & Transparency

Information transparency on the journal website.

**Fields:**

- Are author guidelines publicly available? (Yes/No)
- Are peer review rules publicly available? (Yes/No)
- Are APCs clearly stated? (Yes/No)
- Is the journal archive publicly accessible? (Yes/No)

### Section 12: Declarations & Verification

Verification and accountability.

**Fields:**

- All data provided is true and verifiable (checkbox - required)
- Data corresponds to information on the journal website (checkbox - required)
- Consent to Index Copernicus evaluation (checkbox - required)
- Name of person completing the survey
- Role of person completing the survey
- Submission date (auto-generated)

---

## API Endpoints

### 1. Create Questionnaire for a Journal

**Endpoint:** `POST /api/publications/journals/{journal_id}/questionnaire/`

**Description:** Create a new questionnaire for a specific journal.

**Authentication:** Required (Institution user)

**Request Body:**

```json
{
  "journal_title": "International Journal of Advanced Research",
  "issn": "1234-5678",
  "e_issn": "9876-5432",
  "publisher_name": "Academic Press",
  "publisher_country": "United States",
  "year_first_publication": 2020,
  "publication_frequency": "quarterly",
  "publication_format": "both",
  "journal_website_url": "https://journal.example.com",
  "contact_email": "editor@journal.com",

  "main_discipline": "Computer Science",
  "secondary_disciplines": "Artificial Intelligence, Machine Learning",
  "aims_and_scope": "The journal focuses on...",
  "publishes_original_research": true,
  "publishes_review_articles": true,
  "publishes_case_studies": false,
  "publishes_short_communications": true,
  "publishes_other": "",

  "editor_in_chief_name": "Dr. John Smith",
  "editor_in_chief_affiliation": "MIT",
  "editor_in_chief_country": "United States",
  "editorial_board_members_count": 25,
  "editorial_board_countries": "USA, UK, Germany, France, China",
  "foreign_board_members_percentage": 60.0,
  "board_details_published": true,

  "uses_peer_review": true,
  "peer_review_type": "double_blind",
  "reviewers_per_manuscript": 2,
  "average_review_time_weeks": 4,
  "reviewers_external": true,
  "peer_review_procedure_published": true,
  "peer_review_procedure_url": "https://journal.example.com/peer-review",

  "follows_publication_ethics": true,
  "ethics_based_on_cope": true,
  "ethics_based_on_icmje": true,
  "ethics_other_guidelines": "",
  "uses_plagiarism_detection": true,
  "plagiarism_software_name": "iThenticate",
  "has_retraction_policy": true,
  "retraction_policy_url": "https://journal.example.com/retraction-policy",
  "has_conflict_of_interest_policy": true,
  "conflict_of_interest_policy_url": "https://journal.example.com/coi-policy",

  "issues_published_in_year": 4,
  "all_issues_published_on_time": true,
  "articles_published_in_year": 120,
  "submissions_rejected": 200,
  "average_acceptance_rate": 37.5,

  "total_authors_in_year": 350,
  "foreign_authors_count": 210,
  "author_countries_count": 45,
  "foreign_authors_percentage": 60.0,
  "encourages_international_submissions": true,

  "is_open_access": true,
  "oa_model": "gold",
  "has_apc": true,
  "apc_amount": 2000.0,
  "apc_currency": "USD",
  "license_type": "cc_by",

  "assigns_dois": true,
  "doi_registration_agency": "Crossref",
  "metadata_standards_used": "Dublin Core, JATS",
  "uses_online_submission_system": true,
  "submission_system_name": "Open Journal Systems",
  "digital_archiving_system": "lockss",
  "other_archiving_system": "",

  "indexed_databases": "Scopus, Web of Science, Google Scholar",
  "year_first_indexed": 2021,
  "indexed_in_google_scholar": true,
  "indexed_in_doaj": true,
  "indexed_in_scopus": true,
  "indexed_in_web_of_science": false,
  "abstracting_services": "Chemical Abstracts, INSPEC",

  "author_guidelines_available": true,
  "peer_review_rules_available": true,
  "apcs_clearly_stated": true,
  "journal_archive_accessible": true,

  "data_is_verifiable": true,
  "data_matches_website": true,
  "consent_to_evaluation": true,
  "completed_by_name": "Jane Doe",
  "completed_by_role": "Managing Editor"
}
```

**Response (201 Created):**

```json
{
  "message": "Journal questionnaire created successfully",
  "questionnaire": {
    "id": 1,
    "journal": 1,
    "journal_title": "International Journal of Advanced Research",
    "is_complete": true,
    "completeness_percentage": 95.5,
    "submission_date": "2026-01-14T10:30:00Z",
    "last_updated": "2026-01-14T10:30:00Z"
    // ... all other fields ...
  }
}
```

### 2. Get Questionnaire for a Journal

**Endpoint:** `GET /api/publications/journals/{journal_id}/questionnaire/`

**Description:** Retrieve the existing questionnaire for a journal.

**Authentication:** Required

**Response (200 OK):**

```json
{
  "id": 1,
  "journal": 1,
  "journal_title": "International Journal of Advanced Research",
  // ... all questionnaire fields ...
  "completeness_percentage": 95.5,
  "is_complete": true,
  "submission_date": "2026-01-14T10:30:00Z",
  "last_updated": "2026-01-14T10:30:00Z"
}
```

**Response (404 Not Found):**

```json
{
  "error": "No questionnaire found for this journal",
  "message": "Please create a questionnaire using POST method"
}
```

### 3. Update Questionnaire (Partial)

**Endpoint:** `PATCH /api/publications/questionnaires/{questionnaire_id}/`

**Description:** Partially update a questionnaire (only update provided fields).

**Authentication:** Required

**Request Body:**

```json
{
  "average_acceptance_rate": 42.0,
  "articles_published_in_year": 135,
  "indexed_in_scopus": true
}
```

**Response (200 OK):**

```json
{
  "message": "Questionnaire updated successfully",
  "questionnaire": {
    // ... updated questionnaire data ...
  }
}
```

### 4. Update Questionnaire (Full)

**Endpoint:** `PUT /api/publications/questionnaires/{questionnaire_id}/`

**Description:** Fully update a questionnaire (all fields required).

**Authentication:** Required

### 5. Delete Questionnaire

**Endpoint:** `DELETE /api/publications/questionnaires/{questionnaire_id}/`

**Description:** Delete a questionnaire.

**Authentication:** Required

**Response (200 OK):**

```json
{
  "message": "Questionnaire for \"International Journal of Advanced Research\" has been deleted successfully"
}
```

### 6. List All Questionnaires

**Endpoint:** `GET /api/publications/questionnaires/`

**Description:** List all questionnaires for the authenticated institution's journals.

**Authentication:** Required

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "journal": 1,
    "journal_title": "International Journal of Advanced Research",
    "is_complete": true,
    "completeness_percentage": 95.5,
    "submission_date": "2026-01-14T10:30:00Z",
    "last_updated": "2026-01-14T10:30:00Z"
  },
  {
    "id": 2,
    "journal": 2,
    "journal_title": "Journal of Applied Sciences",
    "is_complete": false,
    "completeness_percentage": 65.0,
    "submission_date": "2026-01-13T14:20:00Z",
    "last_updated": "2026-01-14T09:15:00Z"
  }
]
```

---

## Usage Examples

### Step-by-Step: Adding a Journal with Questionnaire

#### Step 1: Create a Journal

```bash
POST /api/publications/journals/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "International Journal of AI Research",
  "short_title": "IJAIR",
  "issn": "1234-5678",
  "e_issn": "9876-5432",
  "description": "Leading journal in AI research",
  "is_open_access": true,
  "peer_reviewed": true
}
```

**Response:**

```json
{
  "message": "Journal created successfully",
  "journal": {
    "id": 5,
    "title": "International Journal of AI Research"
    // ... other fields ...
  }
}
```

#### Step 2: Fill Out Questionnaire

```bash
POST /api/publications/journals/5/questionnaire/
Authorization: Bearer <token>
Content-Type: application/json

{
  // ... complete questionnaire data (see full example above) ...
}
```

#### Step 3: Check Completeness

The system automatically calculates completeness percentage based on filled required fields.

```bash
GET /api/publications/journals/5/questionnaire/
```

**Response includes:**

```json
{
  "completeness_percentage": 95.5,
  "is_complete": true // Automatically set to true if >= 90%
}
```

#### Step 4: Update Questionnaire as Needed

```bash
PATCH /api/publications/questionnaires/1/
Authorization: Bearer <token>

{
  "articles_published_in_year": 150,
  "indexed_in_web_of_science": true
}
```

---

## Data Model

### JournalQuestionnaire Model

**Database Table:** `publications_journalquestionnaire`

**Key Relationships:**

- **One-to-One** with `Journal` (each journal has one questionnaire)
- Linked via `journal` foreign key

**Field Types:**

- CharField: Text fields with max length
- TextField: Long text (aims, scope, descriptions)
- BooleanField: Yes/No questions
- PositiveIntegerField: Counts, years
- DecimalField: Percentages, amounts
- URLField: Web links
- EmailField: Email addresses
- DateTimeField: Timestamps (auto-managed)

**Special Fields:**

- `is_complete`: Boolean flag (auto-set when completeness >= 90%)
- `submission_date`: Auto-set on creation
- `last_updated`: Auto-updated on every save

**Methods:**

- `calculate_completeness()`: Returns percentage of required fields filled

---

## Validation Rules

### Field Validations

1. **Percentages** (0-100):

   - `foreign_board_members_percentage`
   - `average_acceptance_rate`
   - `foreign_authors_percentage`

2. **Non-negative values**:

   - `apc_amount`
   - All count fields

3. **Conditional Requirements**:

   - If `uses_peer_review = False`, peer review fields are cleared
   - If `has_apc = False`, `apc_amount` is cleared
   - If no indexed databases, `year_first_indexed` is cleared

4. **Required Declarations** (Section 12):
   - `data_is_verifiable` must be True
   - `data_matches_website` must be True
   - `consent_to_evaluation` must be True
   - `completed_by_name` required
   - `completed_by_role` required

### Uniqueness Constraints

- Only **one questionnaire per journal** (enforced at database level)
- Attempting to create a second questionnaire returns an error

---

## Completeness Calculation

The system calculates completeness based on:

1. **Required core fields** (minimum):

   - journal_title
   - publisher_name
   - publisher_country
   - year_first_publication
   - main_discipline
   - aims_and_scope
   - editor_in_chief_name
   - data_is_verifiable
   - data_matches_website

2. **Formula**:

   ```python
   completeness = (filled_required_fields / total_required_fields) * 100
   ```

3. **Auto-completion**:
   - If completeness >= 90%, `is_complete` is automatically set to `true`
   - If < 90%, `is_complete` remains `false`

---

## Integration with Frontend

### Recommended UI Flow

1. **Journal Created Page**
   → "Your journal has been created! Now complete the questionnaire for indexing."

2. **Multi-step Form** (12 sections)
   → Progress bar showing completion
   → Save draft functionality (PATCH updates)
   → Validation on each section

3. **Review & Submit**
   → Summary of all sections
   → Edit individual sections
   → Final submission

4. **Dashboard**
   → List of journals with questionnaire status
   → Completeness indicators
   → Quick links to edit questionnaires

### Form Considerations

- **Long form**: Consider breaking into wizard/stepper
- **Auto-save**: Use PATCH to save progress
- **Validation feedback**: Clear error messages
- **Help text**: Tooltips for each field
- **Pre-fill**: Use journal data to pre-populate Section 1

---

## Admin Interface

The Django admin provides a comprehensive interface for viewing and managing questionnaires:

- **List view** with filters:

  - Completion status
  - Publication format
  - Peer review usage
  - Open access status
  - Submission date

- **Detail view** with collapsible sections (all 12 sections)

- **Search** by journal title, publisher, discipline, editor name

- **Read-only fields**: submission_date, last_updated, completeness_percentage

---

## Migration

The questionnaire model is added via migration:

```bash
python manage.py migrate publications
```

**Migration file:** `publications/migrations/0005_add_journal_questionnaire.py`

---

## Future Enhancements

1. **PDF Export**: Generate PDF summary of questionnaire
2. **Email Notifications**: Remind institutions to complete questionnaires
3. **Versioning**: Track changes over time
4. **Templates**: Pre-fill common values for similar journals
5. **Validation Reports**: Comprehensive validation checks
6. **Integration**: Direct submission to indexing services (DOAJ, etc.)

---

## Support

For questions or issues with the questionnaire system, contact the development team or refer to the main API documentation.
