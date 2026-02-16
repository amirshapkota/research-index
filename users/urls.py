from django.urls import path
from .views.views import (
    AuthorRegistrationView,
    InstitutionRegistrationView,
    LoginView,
    LogoutView,
    CookieTokenRefreshView,
    MeView,
    AuthorProfileView,
    InstitutionProfileView,
    ChangePasswordView,
    UpdateEmailView,
    AccountStatusView,
    DeactivateAccountView,
    DeleteAccountView,
    RefreshAuthorStatsView,
    ExportAuthorView,
    ShareAuthorView,
    ExportInstitutionView,
    ShareInstitutionView,
)
from .views.claim.author.views import (
    SearchImportedAuthorsView,
    ClaimAuthorAccountView,
)
from .views.claim.journal.views import (
    SearchClaimableJournalsView,
    ClaimJournalsWithInstitutionView,
    ClaimJournalView,
    ListMyJournalsView,
)
from .views.follow.views import (
    FollowUserView,
    UnfollowUserView,
    MyFollowersView,
    MyFollowingView,
    UserFollowersView,
    UserFollowingView,
    FollowStatsView,
)
from .views.admin.views import (
    AdminUserListView,
    AdminAuthorDetailView,
    AdminInstitutionDetailView,
)

urlpatterns = [
    # Registration endpoints
    path('register/author/', AuthorRegistrationView.as_view(), name='author-register'),
    path('register/institution/', InstitutionRegistrationView.as_view(), name='institution-register'),
    
    # Account Claiming endpoints (for imported authors only)
    # Institutions are created via journal claiming, not account claiming
    path('claim/authors/search/', SearchImportedAuthorsView.as_view(), name='claim-authors-search'),
    path('claim/author/', ClaimAuthorAccountView.as_view(), name='claim-author'),
    
    # Journal Claiming endpoints
    # Primary way to create institution accounts is by claiming journals
    path('journals/claim/search/', SearchClaimableJournalsView.as_view(), name='journal-claim-search'),
    path('journals/claim/create-institution/', ClaimJournalsWithInstitutionView.as_view(), name='claim-journals-create-institution'),
    path('journals/claim/add/', ClaimJournalView.as_view(), name='claim-additional-journal'),  # For existing institutions
    path('journals/my-journals/', ListMyJournalsView.as_view(), name='my-journals'),
    
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    
    # Current user profile (me)
    path('me/', MeView.as_view(), name='me'),
    
    # Profile endpoints
    path('profile/author/', AuthorProfileView.as_view(), name='author-profile'),
    path('profile/institution/', InstitutionProfileView.as_view(), name='institution-profile'),
    path('profile/author/refresh-stats/', RefreshAuthorStatsView.as_view(), name='refresh-author-stats'),
    
    # Account Settings endpoints
    path('settings/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('settings/update-email/', UpdateEmailView.as_view(), name='update-email'),
    path('settings/account-status/', AccountStatusView.as_view(), name='account-status'),
    path('settings/deactivate-account/', DeactivateAccountView.as_view(), name='deactivate-account'),
    path('settings/delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    
    # Follow endpoints
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/<int:user_id>/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', MyFollowersView.as_view(), name='my-followers'),
    path('following/', MyFollowingView.as_view(), name='my-following'),
    path('users/<int:user_id>/followers/', UserFollowersView.as_view(), name='user-followers'),
    path('users/<int:user_id>/following/', UserFollowingView.as_view(), name='user-following'),
    path('follow-stats/', FollowStatsView.as_view(), name='my-follow-stats'),
    path('users/<int:user_id>/follow-stats/', FollowStatsView.as_view(), name='user-follow-stats'),
    
    # Admin User Management endpoints
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/authors/<int:pk>/', AdminAuthorDetailView.as_view(), name='admin-author-detail'),
    path('admin/institutions/<int:pk>/', AdminInstitutionDetailView.as_view(), name='admin-institution-detail'),
]