# Journal Questionnaire - Quick Reference

## API Endpoints Summary

| Method | Endpoint                                                 | Description                      |
| ------ | -------------------------------------------------------- | -------------------------------- |
| POST   | `/api/publications/journals/{journal_id}/questionnaire/` | Create questionnaire for journal |
| GET    | `/api/publications/journals/{journal_id}/questionnaire/` | Get questionnaire for journal    |
| GET    | `/api/publications/questionnaires/`                      | List all questionnaires          |
| GET    | `/api/publications/questionnaires/{id}/`                 | Get specific questionnaire       |
| PATCH  | `/api/publications/questionnaires/{id}/`                 | Partial update                   |
| PUT    | `/api/publications/questionnaires/{id}/`                 | Full update                      |
| DELETE | `/api/publications/questionnaires/{id}/`                 | Delete questionnaire             |

## 12 Questionnaire Sections

### Journal Identity & Formal Data

- Journal title, ISSN/e-ISSN
- Publisher info & country
- Year founded, frequency, format
- Website & contact email

### Scientific Scope & Profile

- Main & secondary disciplines
- Aims and scope
- Article types (research, reviews, case studies, etc.)

### Editorial Board

- Editor-in-Chief details
- Board size & countries
- Foreign member percentage
- Board details published?

### Peer Review Process

- Uses peer review?
- Review type (single/double-blind, open)
- Reviewers per manuscript
- Average review time
- External reviewers?

### Ethics & Publication Standards

- Follows publication ethics?
- Guidelines (COPE, ICMJE)
- Plagiarism detection & software
- Retraction & COI policies

### Publishing Regularity & Stability

- Issues/articles published per year
- On-time publication?
- Rejection count
- Acceptance rate

### Authors & Internationalization

- Total authors per year
- Foreign authors count & percentage
- Countries represented
- Encourages international submissions?

### Open Access & Fees

- Open Access? (Yes/No)
- OA model (Gold, Hybrid, Diamond, etc.)
- APC amount & currency
- License type (CC BY, etc.)

### Digital Publishing Standards

- Assigns DOIs?
- DOI registration agency
- Metadata standards
- Submission system used
- Digital archiving

### Indexing & Visibility

- Indexed databases
- Year first indexed
- Presence in Google Scholar, DOAJ, Scopus, WoS
- Abstracting services

### Website Quality & Transparency

- Author guidelines available?
- Peer review rules available?
- APCs clearly stated?
- Archive accessible?

### Declarations & Verification

- Data is verifiable (required)
- Data matches website (required)
- Consent to evaluation (required)
- Completed by (name & role)
- Submission date (auto)

## Choice Fields Reference

### Publication Frequency

```python
'weekly', 'biweekly', 'monthly', 'bimonthly',
'quarterly', 'biannual', 'annual', 'irregular'
```

### Publication Format

```python
'online', 'print', 'both'
```

### Peer Review Type

```python
'single_blind', 'double_blind', 'open', 'post_publication', 'other'
```

### OA Model

```python
'gold', 'hybrid', 'diamond', 'green', 'bronze', 'not_oa'
```

### License Type

```python
'cc_by', 'cc_by_sa', 'cc_by_nc', 'cc_by_nc_sa',
'cc_by_nd', 'cc_by_nc_nd', 'cc0', 'other'
```

### Digital Archiving

```python
'lockss', 'clockss', 'portico', 'institutional', 'pmc', 'other', 'none'
```

## Minimal Request Example

```json
{
  "journal_title": "Journal Name",
  "issn": "1234-5678",
  "publisher_name": "Publisher",
  "publisher_country": "USA",
  "year_first_publication": 2020,
  "publication_frequency": "quarterly",
  "publication_format": "both",
  "journal_website_url": "https://example.com",
  "contact_email": "editor@example.com",
  "main_discipline": "Computer Science",
  "aims_and_scope": "Journal focuses on...",
  "publishes_original_research": true,
  "editor_in_chief_name": "Dr. Smith",
  "editor_in_chief_affiliation": "MIT",
  "editor_in_chief_country": "USA",
  "editorial_board_members_count": 20,
  "editorial_board_countries": "USA, UK, Germany",
  "foreign_board_members_percentage": 50.0,
  "board_details_published": true,
  "uses_peer_review": true,
  "peer_review_type": "double_blind",
  "reviewers_per_manuscript": 2,
  "average_review_time_weeks": 4,
  "reviewers_external": true,
  "peer_review_procedure_published": true,
  "follows_publication_ethics": true,
  "uses_plagiarism_detection": true,
  "has_retraction_policy": true,
  "has_conflict_of_interest_policy": true,
  "issues_published_in_year": 4,
  "all_issues_published_on_time": true,
  "articles_published_in_year": 100,
  "submissions_rejected": 150,
  "average_acceptance_rate": 40.0,
  "total_authors_in_year": 300,
  "foreign_authors_count": 150,
  "author_countries_count": 30,
  "foreign_authors_percentage": 50.0,
  "encourages_international_submissions": true,
  "is_open_access": true,
  "oa_model": "gold",
  "has_apc": true,
  "apc_amount": 2000.0,
  "apc_currency": "USD",
  "license_type": "cc_by",
  "assigns_dois": true,
  "doi_registration_agency": "Crossref",
  "uses_online_submission_system": true,
  "digital_archiving_system": "lockss",
  "indexed_databases": "Scopus, Google Scholar",
  "indexed_in_google_scholar": true,
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

## Validation Tips

**Do:**

- Ensure percentages are 0-100
- Provide URLs for policies if set to true
- Fill all required declaration fields (Section 12)
- Use correct choice values from lists above

  **Don't:**

- Try to create multiple questionnaires for one journal
- Leave required declaration fields empty
- Use invalid choice values
- Provide negative numbers for counts/amounts

## Completeness Calculation

- Automatically calculated based on required fields
- `is_complete = true` when completeness >= 90%
- Updated on every save
- Can be checked via API response

## Status Codes

- `201`: Questionnaire created successfully
- `200`: Questionnaire retrieved/updated
- `400`: Validation error
- `404`: Journal or questionnaire not found
- `403`: Permission denied (not your institution's journal)

## Python Code Example

```python
import requests

# Create questionnaire
url = "http://localhost:8000/api/publications/journals/5/questionnaire/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
data = {
    # ... questionnaire data ...
}
response = requests.post(url, json=data, headers=headers)
print(response.json())

# Get questionnaire
response = requests.get(url, headers=headers)
print(f"Completeness: {response.json()['completeness_percentage']}%")

# Update questionnaire
update_url = "http://localhost:8000/api/publications/questionnaires/1/"
update_data = {"articles_published_in_year": 120}
response = requests.patch(update_url, json=update_data, headers=headers)
```

## Database Migration

```bash
cd researchindex
python manage.py migrate publications
```

Migration file: `publications/migrations/0005_add_journal_questionnaire.py`

---

**For full documentation, see:** [JOURNAL_QUESTIONNAIRE.md](JOURNAL_QUESTIONNAIRE.md)
