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
)

urlpatterns = [
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
]
