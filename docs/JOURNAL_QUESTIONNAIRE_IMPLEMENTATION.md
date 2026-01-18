# Journal Questionnaire Implementation Summary

## What Was Implemented

A comprehensive **12-section questionnaire system** for collecting detailed journal information after journal creation. This system is designed for journal evaluation and indexing purposes (Index Copernicus, DOAJ, Scopus, etc.).

## Files Modified/Created

### Models

- **Modified:** [researchindex/publications/models.py](../publications/models.py)
  - Added `JournalQuestionnaire` model with 80+ fields across 12 sections

### Serializers

- **Modified:** [researchindex/publications/serializers.py](../publications/serializers.py)
  - `JournalQuestionnaireListSerializer` - For listing questionnaires
  - `JournalQuestionnaireDetailSerializer` - For viewing complete data
  - `JournalQuestionnaireCreateUpdateSerializer` - For creating/updating

### Views

- **Modified:** [researchindex/publications/views.py](../publications/views.py)
  - `JournalQuestionnaireCreateView` - GET/POST questionnaire for journal
  - `JournalQuestionnaireDetailView` - GET/PATCH/PUT/DELETE questionnaire
  - `JournalQuestionnaireListView` - List all questionnaires

### URLs

- **Modified:** [researchindex/publications/urls.py](../publications/urls.py)
  - Added 3 new URL patterns for questionnaire endpoints

### Admin

- **Modified:** [researchindex/publications/admin.py](../publications/admin.py)
  - Registered `JournalQuestionnaire` with comprehensive admin interface
  - Organized fields into 12 collapsible sections

### Migrations

- **Created:** `publications/migrations/0005_add_journal_questionnaire.py`
  - Database migration for the new model

### Documentation

- **Created:** [JOURNAL_QUESTIONNAIRE.md](JOURNAL_QUESTIONNAIRE.md)

  - Comprehensive documentation (15+ pages)
  - All 12 sections detailed
  - API examples
  - Usage guide

- **Created:** [JOURNAL_QUESTIONNAIRE_QUICK_REF.md](JOURNAL_QUESTIONNAIRE_QUICK_REF.md)
  - Quick reference guide
  - API endpoints summary
  - Field choices reference
  - Code examples

## 🔧 How It Works

### Journal Creation Flow

```
1. Institution creates a journal
   ↓
2. System prompts for questionnaire
   ↓
3. Institution fills 12 sections
   ↓
4. System validates & saves
   ↓
5. Completeness calculated automatically
   ↓
6. Journal ready for indexing evaluation
```

### API Endpoints

| Endpoint                                         | Method               | Description          |
| ------------------------------------------------ | -------------------- | -------------------- |
| `/api/publications/journals/{id}/questionnaire/` | POST                 | Create questionnaire |
| `/api/publications/journals/{id}/questionnaire/` | GET                  | Get questionnaire    |
| `/api/publications/questionnaires/`              | GET                  | List all             |
| `/api/publications/questionnaires/{id}/`         | GET/PATCH/PUT/DELETE | CRUD operations      |

## The 12 Sections

1. **Journal Identity & Formal Data** - Basic journal information
2. **Scientific Scope & Profile** - Discipline, aims, article types
3. **Editorial Board** - Editor-in-Chief, board composition
4. **Peer Review Process** - Review type, timelines, procedures
5. **Ethics & Publication Standards** - COPE, ICMJE, plagiarism policies
6. **Publishing Regularity & Stability** - Issues, articles, acceptance rate
7. **Authors & Internationalization** - Author diversity metrics
8. **Open Access & Fees** - OA model, APCs, licensing
9. **Digital Publishing Standards** - DOIs, metadata, archiving
10. **Indexing & Visibility** - Databases, Scopus, WoS, DOAJ
11. **Website Quality & Transparency** - Guidelines, policies availability
12. **Declarations & Verification** - Accountability statements

## Key Features

### Automatic Completeness Calculation

```python
completeness = (filled_required_fields / total_required_fields) * 100
is_complete = completeness >= 90%
```

### Smart Validation

- Percentage fields: 0-100
- Conditional requirements (e.g., if peer review = False, clear review fields)
- One questionnaire per journal (enforced)
- Required declarations in Section 12

### Admin Interface

- Searchable by journal, publisher, discipline
- Filterable by completion status, OA status, peer review
- Collapsible sections for easy navigation
- Read-only auto-generated fields

### Audit Trail

- `submission_date` - Auto-set on creation
- `last_updated` - Auto-updated on every save
- `completed_by_name` & `completed_by_role` - Accountability

## Example Usage

### Create Questionnaire

```bash
POST /api/publications/journals/5/questionnaire/
{
  "journal_title": "International Journal of AI",
  "issn": "1234-5678",
  "publisher_name": "Academic Press",
  "publisher_country": "USA",
  # ... 70+ more fields ...
  "data_is_verifiable": true,
  "completed_by_name": "Jane Doe",
  "completed_by_role": "Managing Editor"
}
```

### Check Completeness

```bash
GET /api/publications/journals/5/questionnaire/
Response:
{
  "completeness_percentage": 95.5,
  "is_complete": true,
  # ... all questionnaire data ...
}
```

### Update Partial Data

```bash
PATCH /api/publications/questionnaires/1/
{
  "indexed_in_scopus": true,
  "articles_published_in_year": 150
}
```

## 🔒 Security

- Authentication required for all endpoints
- Users can only access their institution's journals
- Validation on all input fields
- Foreign key constraints ensure data integrity

## 📊 Data Model

```
Journal (1) ←──── (1) JournalQuestionnaire
   ↓
   └─ institution (FK to Institution)

One-to-One relationship ensures:
- One questionnaire per journal
- Questionnaire deleted when journal deleted (CASCADE)
```

## 🚀 Next Steps

### To Use This System:

1. **Run Migration**

   ```bash
   cd researchindex
   python manage.py migrate publications
   ```

2. **Create Journal** (if not already done)

   ```bash
   POST /api/publications/journals/
   ```

3. **Fill Questionnaire**

   ```bash
   POST /api/publications/journals/{id}/questionnaire/
   ```

4. **Monitor Completeness**
   ```bash
   GET /api/publications/questionnaires/
   ```

### Frontend Integration

**Recommended UI:**

- Multi-step wizard (12 steps)
- Progress bar showing completeness
- Auto-save on section completion
- Validation feedback per section
- Final review page before submission

**Form Flow:**

```
Journal Created → Questionnaire Wizard → Section 1 → ... → Section 12 → Review → Submit
```

## 📚 Documentation

- **Full Guide:** [JOURNAL_QUESTIONNAIRE.md](JOURNAL_QUESTIONNAIRE.md)
- **Quick Reference:** [JOURNAL_QUESTIONNAIRE_QUICK_REF.md](JOURNAL_QUESTIONNAIRE_QUICK_REF.md)

## Use Cases

1. **Index Copernicus Evaluation** - Complete profile for IC scoring
2. **DOAJ Application** - All required data for DOAJ submission
3. **Scopus Review** - Comprehensive journal information
4. **Internal Quality Assurance** - Track journal standards
5. **Journal Directory** - Rich metadata for discovery

## ⚙️ Technical Details

- **Database Table:** `publications_journalquestionnaire`
- **Model Fields:** 80+ fields
- **Validation:** Django validators + custom validation
- **Serialization:** DRF serializers with nested data
- **API Style:** RESTful with proper HTTP methods
- **Documentation:** Swagger/OpenAPI via drf-spectacular

## 📈 Metrics Tracked

The questionnaire captures:

- 📊 Acceptance rates
- 🌍 International author percentages
- 👥 Editorial board diversity
- ⏱️ Review timelines
- 💰 APC amounts
- 📚 Indexing databases
- ✅ Ethics compliance
- 🔓 Open access status

## 🎨 Admin Features

- List view with key metrics
- Filters for common criteria
- Search across multiple fields
- Bulk actions support
- Export capabilities (Django default)
- Inline help text

## ✅ Validation Rules

- ✓ Percentages: 0-100 range
- ✓ URLs: Valid format
- ✓ Emails: Valid format
- ✓ Required fields: Cannot be empty
- ✓ Conditional logic: Auto-clear dependent fields
- ✓ Uniqueness: One per journal

## 🔄 Update Workflow

```
Draft → Partial Save → Continue → Complete → Submit → Verified
  ↓         ↓            ↓          ↓         ↓         ↓
 40%       60%          75%        90%      100%    Published
```

## 🛠️ Maintenance

- **Backup:** Regular database backups recommended
- **Updates:** Use PATCH for partial updates to preserve data
- **Versioning:** Consider adding version tracking for future enhancements
- **Monitoring:** Track completion rates via admin dashboard

---

## Summary

A complete, production-ready journal questionnaire system that:

- ✅ Captures 12 sections of detailed journal data
- ✅ Provides RESTful API endpoints
- ✅ Includes comprehensive validation
- ✅ Offers rich admin interface
- ✅ Calculates completeness automatically
- ✅ Supports partial updates and drafts
- ✅ Includes full documentation

Ready for integration with frontend and use in journal evaluation workflows!
