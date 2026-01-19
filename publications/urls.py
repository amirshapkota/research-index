from django.urls import path
from .views import (
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
    EditorialBoardListCreateView,
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
    JournalPublicationsListView,
)

urlpatterns = [
    # ==================== PUBLIC ENDPOINTS ====================
    # Public publications list (no auth required)
    path('public/', PublicPublicationsListView.as_view(), name='public-publications-list'),
    
    # Public journal publications (no auth required)
    path('journals/<int:journal_pk>/publications/', JournalPublicationsListView.as_view(), name='journal-publications-list'),
    
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
]
