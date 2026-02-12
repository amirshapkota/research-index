from django.urls import path
from .views.views import (
    PublicationListCreateView,
    PublicationDetailView,
    PublicationStatsView,
    AddCitationView,
    AddReferenceView,
    BulkAddReferencesView,
    RecordPublicationReadView,
    DownloadPublicationView,
    # Journal views
    JournalListCreateView,
    JournalDetailView,
    JournalStatsView,
    RefreshJournalStatsView,
    EditorialBoardListCreateView,
    ExportJournalView,
    ShareJournalView,
    # Issue views
    IssueListCreateView,
    IssueDetailView,
    AddArticleToIssueView,
    # Topic views
    TopicListCreateView,
    TopicDetailView,
    TopicTreeView,
    TopicBranchListCreateView,
    TopicBranchDetailView,
    PublicationsByTopicBranchView,
    # Questionnaire views
    JournalQuestionnaireCreateView,
    JournalQuestionnaireDetailView,
    JournalQuestionnaireListView,
    # Public views
    PublicPublicationsListView,
    PublicPublicationDetailView,
    JournalPublicationsListView,
    PublicJournalsListView,
    PublicJournalDetailView,
    PublicJournalIssuesView,
    PublicJournalIssueDetailView,
    PublicJournalVolumesView,
    PublicInstitutionsListView,
    PublicInstitutionDetailView,
    PublicAuthorsListView,
    PublicAuthorDetailView,
    PublicAuthorPublicationsView,
    PublicInstitutionPublicationsView,
    # DOAJ views
    DOAJSearchView,
    DOAJJournalByISSNView,
    # Admin views
    SyncCitationsAdminView,
    RecalculateStatsAdminView,
)
from .views.sync.views import sync_external_publications

urlpatterns = [
    # ==================== PUBLIC ENDPOINTS ====================
    # Public publications (no auth required)
    path('public/', PublicPublicationsListView.as_view(), name='public-publications-list'),
    path('public/<int:pk>/', PublicPublicationDetailView.as_view(), name='public-publication-detail'),
    
    # Public journals (no auth required)
    path('journals/public/', PublicJournalsListView.as_view(), name='public-journals-list'),
    path('journals/public/<int:pk>/', PublicJournalDetailView.as_view(), name='public-journal-detail'),
    path('journals/public/<int:pk>/export/', ExportJournalView.as_view(), name='export-journal'),
    path('journals/public/<int:pk>/share/', ShareJournalView.as_view(), name='share-journal'),
    path('journals/public/<int:journal_pk>/issues/', PublicJournalIssuesView.as_view(), name='public-journal-issues'),
    path('journals/public/<int:journal_pk>/issues/<int:pk>/', PublicJournalIssueDetailView.as_view(), name='public-journal-issue-detail'),
    path('journals/public/<int:journal_pk>/volumes/', PublicJournalVolumesView.as_view(), name='public-journal-volumes'),
    path('journals/<int:journal_pk>/publications/', JournalPublicationsListView.as_view(), name='journal-publications-list'),
    
    # Public institutions (no auth required)
    path('institutions/public/', PublicInstitutionsListView.as_view(), name='public-institutions-list'),
    path('institutions/public/<int:pk>/', PublicInstitutionDetailView.as_view(), name='public-institution-detail'),
    
    # Public authors (no auth required)
    path('authors/public/', PublicAuthorsListView.as_view(), name='public-authors-list'),
    path('authors/public/<int:pk>/', PublicAuthorDetailView.as_view(), name='public-author-detail'),
    path('authors/public/<int:author_pk>/publications/', PublicAuthorPublicationsView.as_view(), name='public-author-publications'),
    
    # Public institutions (no auth required)
    path('institutions/public/', PublicInstitutionsListView.as_view(), name='public-institutions-list'),
    path('institutions/public/<int:pk>/', PublicInstitutionDetailView.as_view(), name='public-institution-detail'),
    path('institutions/public/<int:institution_pk>/publications/', PublicInstitutionPublicationsView.as_view(), name='public-institution-publications'),
    
    # ==================== TOPICS ====================
    # Topic CRUD
    path('topics/', TopicListCreateView.as_view(), name='topic-list-create'),
    path('topics/tree/', TopicTreeView.as_view(), name='topic-tree'),
    path('topics/<int:pk>/', TopicDetailView.as_view(), name='topic-detail'),
    
    # Topic Branches
    path('topics/<int:topic_pk>/branches/', TopicBranchListCreateView.as_view(), name='topic-branch-list-create'),
    path('topics/<int:topic_pk>/branches/<int:pk>/', TopicBranchDetailView.as_view(), name='topic-branch-detail'),
    
    # Publications by Topic Branch
    path('topics/<int:topic_pk>/branches/<int:branch_pk>/publications/', PublicationsByTopicBranchView.as_view(), name='publications-by-topic-branch'),
    
    # ==================== PUBLICATIONS ====================
    # Publication CRUD
    path('', PublicationListCreateView.as_view(), name='publication-list-create'),
    path('<int:pk>/', PublicationDetailView.as_view(), name='publication-detail'),
    
    # Stats
    path('<int:pk>/stats/', PublicationStatsView.as_view(), name='publication-stats'),
    
    # Citations
    path('<int:pk>/citations/add/', AddCitationView.as_view(), name='add-citation'),
    
    # References
    path('<int:pk>/references/add/', AddReferenceView.as_view(), name='add-reference'),
    path('<int:pk>/references/bulk/', BulkAddReferencesView.as_view(), name='bulk-add-references'),
    
    # Public endpoints
    path('<int:pk>/read/', RecordPublicationReadView.as_view(), name='record-read'),
    path('<int:pk>/download/', DownloadPublicationView.as_view(), name='download-pdf'),
    
    # Journal CRUD
    path('journals/', JournalListCreateView.as_view(), name='journal-list-create'),
    path('journals/<int:pk>/', JournalDetailView.as_view(), name='journal-detail'),
    
    # Journal Stats
    path('journals/<int:pk>/stats/', JournalStatsView.as_view(), name='journal-stats'),
    path('journals/<int:pk>/refresh-stats/', RefreshJournalStatsView.as_view(), name='refresh-journal-stats'),
    
    # Editorial Board
    path('journals/<int:journal_pk>/editorial-board/', EditorialBoardListCreateView.as_view(), name='editorial-board-list-create'),
    
    # Issue CRUD
    path('journals/<int:journal_pk>/issues/', IssueListCreateView.as_view(), name='issue-list-create'),
    path('journals/<int:journal_pk>/issues/<int:pk>/', IssueDetailView.as_view(), name='issue-detail'),
    
    # Issue Articles
    path('journals/<int:journal_pk>/issues/<int:issue_pk>/articles/add/', AddArticleToIssueView.as_view(), name='add-article-to-issue'),
    
    # ==================== JOURNAL QUESTIONNAIRE ====================
    # List all questionnaires
    path('questionnaires/', JournalQuestionnaireListView.as_view(), name='questionnaire-list'),
    
    # Create/Get questionnaire for a specific journal
    path('journals/<int:journal_pk>/questionnaire/', JournalQuestionnaireCreateView.as_view(), name='journal-questionnaire-create'),
    
    # Retrieve/Update/Delete a specific questionnaire
    path('questionnaires/<int:pk>/', JournalQuestionnaireDetailView.as_view(), name='questionnaire-detail'),
    
    # ==================== DOAJ API ====================
    # Search DOAJ journals
    path('doaj/search/', DOAJSearchView.as_view(), name='doaj-search'),
    # Get journal by ISSN from DOAJ
    path('doaj/issn/<str:issn>/', DOAJJournalByISSNView.as_view(), name='doaj-journal-by-issn'),
    
    # ==================== ADMIN ENDPOINTS ====================
    # Sync from external journal portal
    path('sync/', sync_external_publications, name='sync-external-publications'),
    
    # Admin: Sync citations from Crossref
    path('admin/sync-citations/', SyncCitationsAdminView.as_view(), name='admin-sync-citations'),
    
    # Admin: Recalculate journal statistics
    path('admin/recalculate-stats/', RecalculateStatsAdminView.as_view(), name='admin-recalculate-stats'),
]
