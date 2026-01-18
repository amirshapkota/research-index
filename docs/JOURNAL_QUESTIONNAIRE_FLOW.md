# Journal Questionnaire Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Journal    │  │ Questionnaire│  │  Dashboard   │         │
│  │   Creation   │→ │    Wizard    │→ │   Review     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │ API Calls
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO REST API                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  publications/urls.py                                     │  │
│  │  ├─ POST   /journals/{id}/questionnaire/                 │  │
│  │  ├─ GET    /journals/{id}/questionnaire/                 │  │
│  │  ├─ GET    /questionnaires/                              │  │
│  │  ├─ PATCH  /questionnaires/{id}/                         │  │
│  │  ├─ PUT    /questionnaires/{id}/                         │  │
│  │  └─ DELETE /questionnaires/{id}/                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  publications/views.py                                    │  │
│  │  ├─ JournalQuestionnaireCreateView                       │  │
│  │  ├─ JournalQuestionnaireDetailView                       │  │
│  │  └─ JournalQuestionnaireListView                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  publications/serializers.py                              │  │
│  │  ├─ JournalQuestionnaireListSerializer                   │  │
│  │  ├─ JournalQuestionnaireDetailSerializer                 │  │
│  │  └─ JournalQuestionnaireCreateUpdateSerializer           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│                             ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  publications/models.py                                   │  │
│  │  └─ JournalQuestionnaire (80+ fields)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATABASE                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  publications_journalquestionnaire                        │  │
│  │  ├─ id (PK)                                              │  │
│  │  ├─ journal_id (FK → Journal, OneToOne)                 │  │
│  │  ├─ [Section 1] 10 fields                               │  │
│  │  ├─ [Section 2] 6 fields                                │  │
│  │  ├─ [Section 3] 7 fields                                │  │
│  │  ├─ [Section 4] 7 fields                                │  │
│  │  ├─ [Section 5] 9 fields                                │  │
│  │  ├─ [Section 6] 5 fields                                │  │
│  │  ├─ [Section 7] 5 fields                                │  │
│  │  ├─ [Section 8] 6 fields                                │  │
│  │  ├─ [Section 9] 7 fields                                │  │
│  │  ├─ [Section 10] 6 fields                               │  │
│  │  ├─ [Section 11] 4 fields                               │  │
│  │  ├─ [Section 12] 7 fields                               │  │
│  │  ├─ is_complete (Boolean)                               │  │
│  │  ├─ submission_date (DateTime)                          │  │
│  │  └─ last_updated (DateTime)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## User Journey Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                        INSTITUTION USER                            │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
                    ┌──────────────────────────┐
                    │   1. Login to System     │
                    └──────────────────────────┘
                                   │
                                   ↓
                    ┌──────────────────────────┐
                    │  2. Create New Journal   │
                    │  (POST /journals/)       │
                    └──────────────────────────┘
                                   │
                                   ↓
          ┌────────────────────────────────────────────┐
          │  3. Journal Created Successfully!          │
          │  → Prompt: "Complete Questionnaire?"       │
          └────────────────────────────────────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                YES                                 NO
                 │                                   │
                 ↓                                   ↓
    ┌────────────────────────┐         ┌────────────────────────┐
    │ 4. Start Questionnaire │         │ Skip (Complete Later)  │
    │ Wizard (12 Steps)      │         └────────────────────────┘
    └────────────────────────┘
                 │
                 ↓
    ┌────────────────────────┐
    │ Section 1: Identity    │
    │ ┌────────────────────┐ │
    │ │ • Journal Title    │ │
    │ │ • ISSN             │ │
    │ │ • Publisher        │ │
    │ │ • Website          │ │
    │ └────────────────────┘ │
    └────────────────────────┘
                 │ [Next]
                 ↓
    ┌────────────────────────┐
    │ Section 2: Scope       │
    │ ┌────────────────────┐ │
    │ │ • Discipline       │ │
    │ │ • Aims & Scope     │ │
    │ │ • Article Types    │ │
    │ └────────────────────┘ │
    └────────────────────────┘
                 │ [Next]
                 ↓
    ┌────────────────────────┐
    │ Section 3: Editorial   │
    │ ┌────────────────────┐ │
    │ │ • EIC Details      │ │
    │ │ • Board Size       │ │
    │ │ • Countries        │ │
    │ └────────────────────┘ │
    └────────────────────────┘
                 │ [Next]
                 ↓
               [...]
                 │ (Sections 4-11)
                 ↓
    ┌────────────────────────┐
    │ Section 12: Verify     │
    │ ┌────────────────────┐ │
    │ │ ☑ Data Verifiable  │ │
    │ │ ☑ Matches Website  │ │
    │ │ ☑ Consent          │ │
    │ │ • Completed By     │ │
    │ └────────────────────┘ │
    └────────────────────────┘
                 │ [Submit]
                 ↓
    ┌────────────────────────┐
    │ Review & Confirmation  │
    │ ┌────────────────────┐ │
    │ │ Completeness: 95%  │ │
    │ │ Status: Complete ✓ │ │
    │ └────────────────────┘ │
    └────────────────────────┘
                 │
                 ↓
    ┌────────────────────────┐
    │ ✓ Questionnaire Saved  │
    │   Ready for Indexing   │
    └────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CREATE QUESTIONNAIRE                       │
└─────────────────────────────────────────────────────────────────┘

Frontend Form
     │
     │ Submit Data (JSON)
     ↓
POST /api/publications/journals/5/questionnaire/
     │
     │ Request with JWT Token
     ↓
Authentication Middleware
     │
     │ Token Valid ✓
     ↓
JournalQuestionnaireCreateView
     │
     ├─→ Check: User owns journal? → YES ✓
     │
     ├─→ Check: Questionnaire exists? → NO ✓
     │
     ↓
JournalQuestionnaireCreateUpdateSerializer
     │
     ├─→ Validate: All required fields
     ├─→ Validate: Percentages (0-100)
     ├─→ Validate: URLs, Emails
     ├─→ Validate: Conditional logic
     │
     ↓
Create JournalQuestionnaire Object
     │
     ├─→ Set journal FK
     ├─→ Auto-set submission_date
     ├─→ Calculate completeness
     ├─→ Set is_complete if >= 90%
     │
     ↓
Save to Database
     │
     ↓
Return Response (201 Created)
     │
     │ {
     │   "message": "Questionnaire created",
     │   "questionnaire": {...},
     │   "completeness_percentage": 95.5,
     │   "is_complete": true
     │ }
     ↓
Frontend Updates UI
```

## Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      UPDATE QUESTIONNAIRE                       │
└─────────────────────────────────────────────────────────────────┘

User Edits Section 6
     │
     │ Changed Fields Only
     ↓
PATCH /api/publications/questionnaires/1/
     │
     │ {
     │   "articles_published_in_year": 150,
     │   "average_acceptance_rate": 42.0
     │ }
     ↓
JournalQuestionnaireDetailView
     │
     ├─→ Check: User owns this questionnaire? → YES ✓
     │
     ↓
JournalQuestionnaireCreateUpdateSerializer
     │
     ├─→ Validate changed fields
     ├─→ Preserve unchanged fields
     │
     ↓
Update JournalQuestionnaire Object
     │
     ├─→ Update specified fields
     ├─→ Auto-update last_updated
     ├─→ Recalculate completeness
     ├─→ Update is_complete
     │
     ↓
Save to Database
     │
     ↓
Return Response (200 OK)
     │
     │ {
     │   "message": "Updated successfully",
     │   "questionnaire": {...}
     │ }
     ↓
Frontend Reflects Changes
```

## Completeness Calculation

```
┌─────────────────────────────────────────────────────────────────┐
│              AUTOMATIC COMPLETENESS CALCULATION                 │
└─────────────────────────────────────────────────────────────────┘

Trigger: On Create or Update
     │
     ↓
JournalQuestionnaire.calculate_completeness()
     │
     ├─→ Check Required Fields:
     │   ├─ journal_title ✓
     │   ├─ publisher_name ✓
     │   ├─ publisher_country ✓
     │   ├─ year_first_publication ✓
     │   ├─ main_discipline ✓
     │   ├─ aims_and_scope ✓
     │   ├─ editor_in_chief_name ✓
     │   ├─ data_is_verifiable ✓
     │   └─ data_matches_website ✓
     │
     ↓
Calculate: (filled / total) × 100
     │
     │ Example: (9 / 9) × 100 = 100%
     ↓
Compare: completeness >= 90%?
     │
     ├─→ YES → Set is_complete = True
     │
     └─→ NO  → Set is_complete = False
     │
     ↓
Save & Return Percentage
```

## API Response Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESPONSE SERIALIZATION                      │
└─────────────────────────────────────────────────────────────────┘

JournalQuestionnaire Object
     │
     ↓
JournalQuestionnaireDetailSerializer
     │
     ├─→ Include all 80+ fields
     ├─→ Add display values (e.g., get_..._display())
     ├─→ Add computed fields:
     │   ├─ journal_title (from FK)
     │   ├─ journal_id (from FK)
     │   └─ completeness_percentage (calculated)
     │
     ↓
Convert to JSON
     │
     ↓
HTTP Response
     │
     │ {
     │   "id": 1,
     │   "journal": 5,
     │   "journal_title": "IJAR",
     │   "completeness_percentage": 95.5,
     │   "is_complete": true,
     │   "section_1_fields": {...},
     │   "section_2_fields": {...},
     │   ...
     │   "section_12_fields": {...},
     │   "submission_date": "2026-01-14T10:30:00Z",
     │   "last_updated": "2026-01-14T11:45:00Z"
     │ }
     ↓
Frontend Renders Data
```

## Permissions & Access Control

```
┌─────────────────────────────────────────────────────────────────┐
│                     PERMISSION CHECKS                           │
└─────────────────────────────────────────────────────────────────┘

Incoming Request
     │
     ↓
IsAuthenticated?
     │
     ├─→ NO  → 401 Unauthorized
     │
     └─→ YES → Continue
             │
             ↓
     Get Institution from User
             │
             ├─→ No Institution? → 404 Not Found
             │
             └─→ Has Institution → Continue
                         │
                         ↓
             Check Journal Ownership
                         │
                         ├─→ journal.institution != user.institution
                         │   → 403 Forbidden
                         │
                         └─→ Owns Journal → Allow Access ✓
```

## Database Relations

```
┌────────────────────────────────────────────────────────────────┐
│                    DATABASE RELATIONSHIPS                       │
└────────────────────────────────────────────────────────────────┘

Institution
    │ 1
    │
    │ *
    ↓
Journal ←──────────── JournalStats (1:1)
    │ 1                     ↑
    │                       │
    │ 1                     │
    ↓                       │
JournalQuestionnaire        │
    (80+ fields)            │
    - Sections 1-12         │
    - Completeness calc     │
    - Auto timestamps       │
                            │
                   References for metrics
```

## Validation Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     VALIDATION PIPELINE                         │
└────────────────────────────────────────────────────────────────┘

Incoming Data
     │
     ↓
Field Type Validation (Django)
     │
     ├─→ EmailField → Valid email?
     ├─→ URLField → Valid URL?
     ├─→ IntegerField → Is integer?
     ├─→ DecimalField → Valid decimal?
     │
     ↓
Field Validators (Django)
     │
     ├─→ MinValueValidator(0) → >= 0?
     ├─→ MaxValueValidator(100) → <= 100?
     │
     ↓
Serializer Validation
     │
     ├─→ validate_foreign_board_members_percentage()
     ├─→ validate_average_acceptance_rate()
     ├─→ validate_foreign_authors_percentage()
     ├─→ validate_apc_amount()
     │
     ↓
Cross-field Validation
     │
     ├─→ uses_peer_review = False?
     │   → Clear peer review fields
     │
     ├─→ has_apc = False?
     │   → Clear apc_amount
     │
     ├─→ No indexed_databases?
     │   → Clear year_first_indexed
     │
     ↓
Business Logic Validation
     │
     ├─→ Questionnaire already exists?
     │   → Raise error
     │
     ↓
All Validations Pass ✓
     │
     ↓
Proceed to Save
```

---

## Summary

This comprehensive flow diagram illustrates:

- ✅ Complete system architecture
- ✅ User journey from journal creation to questionnaire submission
- ✅ Data flow through all layers
- ✅ Update and retrieval processes
- ✅ Automatic completeness calculation
- ✅ Permission and access control
- ✅ Database relationships
- ✅ Validation pipeline

Each flow is designed to ensure data integrity, security, and a smooth user experience!
