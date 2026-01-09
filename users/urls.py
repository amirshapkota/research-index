from django.urls import path
from .views import (
    AuthorRegistrationView,
    InstitutionRegistrationView,
    LoginView,
    LogoutView,
    CookieTokenRefreshView,
    AuthorProfileView,
    InstitutionProfileView,
    ChangePasswordView,
    UpdateEmailView,
    AccountStatusView,
    DeactivateAccountView,
    DeleteAccountView,
    RefreshAuthorStatsView
)

urlpatterns = [
    # Registration endpoints
    path('register/author/', AuthorRegistrationView.as_view(), name='author-register'),
    path('register/institution/', InstitutionRegistrationView.as_view(), name='institution-register'),
    
    # Authentication endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    
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
]