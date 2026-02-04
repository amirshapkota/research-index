from django.urls import path, re_path
from .views import (
    ContactCreateView,
    # Crossref API views
    CrossrefWorkByDOIView,
    CrossrefSearchWorksView,
    CrossrefWorkReferencesView,
    CrossrefWorkCitationsView,
    CrossrefJournalByISSNView,
    CrossrefJournalWorksView,
    CrossrefValidateDOIView,
    CrossrefSearchFundersView,
)

urlpatterns = [
    # Contact
    path('contact/', ContactCreateView.as_view(), name='contact-create'),
    
    # Crossref API integration
    # Search and validation (no DOI in path)
    path('crossref/search/works/', CrossrefSearchWorksView.as_view(), name='crossref-search-works'),
    path('crossref/search/funders/', CrossrefSearchFundersView.as_view(), name='crossref-search-funders'),
    path('crossref/validate-doi/', CrossrefValidateDOIView.as_view(), name='crossref-validate-doi'),
    
    # DOI-based endpoints (DOI must be URL-encoded, e.g., 10.1007%2Fs10791-025-09890-x)
    re_path(r'^crossref/works/(?P<doi>.+)/references/$', CrossrefWorkReferencesView.as_view(), name='crossref-work-references'),
    re_path(r'^crossref/works/(?P<doi>.+)/citations/$', CrossrefWorkCitationsView.as_view(), name='crossref-work-citations'),
    re_path(r'^crossref/works/(?P<doi>.+)/$', CrossrefWorkByDOIView.as_view(), name='crossref-work-by-doi'),
    
    # Journal endpoints
    path('crossref/journal/<str:issn>/', CrossrefJournalByISSNView.as_view(), name='crossref-journal-by-issn'),
    path('crossref/journal/<str:issn>/works/', CrossrefJournalWorksView.as_view(), name='crossref-journal-works'),
]
